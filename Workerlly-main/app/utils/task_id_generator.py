import datetime


class TaskIDGenerator:
    """
    Utility class for generating readable task IDs for jobs.

    Format: YMD-NNNN
    - Y: Year as single character (base36)
    - M: Month as single character (base36)
    - D: Day as single character (base36)
    - NNNN: 4-digit sequential number that resets each day

    Examples:
    - PC1-0001: First job on March 1, 2025
    - PAF-0042: 42nd job on October 15, 2025

    This format supports up to 9,999 jobs per day.
    """

    # Map for converting numbers to base36 (1-9, A-Z)
    CHAR_MAP = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @classmethod
    def _encode_year(cls, year: int) -> str:
        """Encode year as single base36 character (good for 36 years from 2020-2055)"""
        year_offset = year - 2020
        if year_offset < 0 or year_offset >= 36:
            # Fallback for years outside our range
            return "0"
        return cls.CHAR_MAP[year_offset % 36]

    @classmethod
    def _encode_month(cls, month: int) -> str:
        """Encode month as single character (1-9, A-C for 10-12)"""
        if month < 1 or month > 12:
            return "1"  # Default to January
        return cls.CHAR_MAP[month - 1]

    @classmethod
    def _encode_day(cls, day: int) -> str:
        """Encode day as single base36 character (1-9, A-V for 10-31)"""
        if day < 1 or day > 31:
            return "1"  # Default to 1st
        return cls.CHAR_MAP[day - 1]

    @classmethod
    async def generate_task_id(cls, motor_db=None, sequence_digits: int = 4) -> str:
        """
        Generate a task ID based on current date and sequential counter.

        Args:
            motor_db: Optional MongoDB database connection for finding the latest sequence
            sequence_digits: Number of digits to use for sequence (default: 4)

        Returns:
            A task ID string in format YMD-NNNN
        """
        # Get current date
        # Get current date in IST (GMT+5:30)
        utc_now = datetime.datetime.utcnow()
        ist_offset = datetime.timedelta(hours=5, minutes=30)
        ist_now = utc_now + ist_offset

        # Encode date components
        year_char = cls._encode_year(ist_now.year)
        month_char = cls._encode_month(ist_now.month)
        day_char = cls._encode_day(ist_now.day)

        # Format date prefix
        date_prefix = f"{year_char}{month_char}{day_char}"

        # Start with sequence 1 by default
        sequence = 1

        # If database is provided, find highest sequence for current date
        if motor_db is not None:  # Find highest existing task_id for this date
            highest_job = await motor_db.jobs.find_one(
                {"task_id": {"$regex": f"^{date_prefix}-"}},
                sort=[("task_id", -1)]
            )

            if highest_job and "task_id" in highest_job:
                try:
                    # Extract sequence part (after the hyphen)
                    current_max = int(highest_job["task_id"].split('-')[1])
                    # Increment for new sequence
                    sequence = current_max + 1
                except (ValueError, IndexError):
                    # If parsing fails, start with 1
                    sequence = 1

        # Create task ID in format YMD-NNNN
        return f"{date_prefix}-{sequence:0{sequence_digits}d}"

    @classmethod
    def decode_task_id(cls, task_id: str) -> dict:
        """
        Decode a task ID to extract its date components.

        Args:
            task_id: A task ID string in format YMD-NNNN

        Returns:
            Dict containing date information (year, month, day, sequence)
        """
        if not task_id or len(task_id) < 5 or '-' not in task_id:
            return {"error": "Invalid task ID format"}

        try:
            # Split into date part and sequence
            date_part, sequence_part = task_id.split('-', 1)

            if len(date_part) != 3:
                return {"error": "Invalid date format in task ID"}

            # Extract date components
            year_char, month_char, day_char = date_part[0], date_part[1], date_part[2]

            # Decode year
            year_offset = cls.CHAR_MAP.find(year_char)
            if year_offset == -1:
                year = None
            else:
                year = 2020 + year_offset

            # Decode month
            month_index = cls.CHAR_MAP.find(month_char)
            if month_index == -1:
                month = None
            else:
                month = month_index + 1

            # Decode day
            day_index = cls.CHAR_MAP.find(day_char)
            if day_index == -1:
                day = None
            else:
                day = day_index + 1

            # Decode sequence
            sequence = int(sequence_part)

            return {
                "year": year,
                "month": month,
                "day": day,
                "sequence": sequence,
                "date": datetime.date(year, month, day) if all([year, month, day]) else None
            }

        except Exception as e:
            return {"error": f"Failed to decode task ID: {str(e)}"}
