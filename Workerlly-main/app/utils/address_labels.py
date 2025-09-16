from enum import Enum
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException

from app.db.models.database import motor_db


class AddressLabel(str, Enum):
    """Enum for valid address labels"""

    HOME = "home"
    OFFICE = "office"
    OTHER = "other"

    @classmethod
    def list(cls) -> list:
        """Returns list of all valid label values"""
        return [label.value for label in cls]

    @classmethod
    def is_unique_required(cls, label: str) -> bool:
        """Check if the given label requires uniqueness"""
        return label.lower() in [cls.HOME.value, cls.OFFICE.value]

    @classmethod
    def normalize_label(cls, label: str) -> str:
        """Normalize label to lowercase for consistent comparison"""
        return label.lower()


class LabelValidator:
    """Utility class for address label validation and checking"""

    @staticmethod
    async def check_existing_label(
        user_id: str, label: str, address_id: Optional[str] = None
    ) -> bool:
        """
        Check if user already has an address with the given label.

        Args:
            user_id: The ID of the user
            label: The address label to check
            address_id: Optional - The current address ID (for updates)

        Returns:
            bool: True if label exists, False otherwise
        """
        query = {
            "user_id": ObjectId(user_id),
            "label": {
                "$regex": f"^{label}$",
                "$options": "i",
            },  # Case-insensitive match
            "deleted_at": None,
        }

        # For updates, exclude the current address
        if address_id:
            query["_id"] = {"$ne": ObjectId(address_id)}

        existing_address = await motor_db.addresses.find_one(query)
        return existing_address is not None

    @classmethod
    async def validate_label_for_create(cls, user_id: str, label: str) -> None:
        """
        Validate label for new address creation.

        Args:
            user_id: The ID of the user
            label: The proposed label

        Raises:
            HTTPException: If validation fails
            ValueError: If label is invalid
        """
        normalized_label = AddressLabel.normalize_label(label)
        if normalized_label not in AddressLabel.list():
            raise ValueError(
                f"Invalid label. Must be one of: {', '.join(AddressLabel.list())}"
            )

        if AddressLabel.is_unique_required(normalized_label):
            if await cls.check_existing_label(user_id, normalized_label):
                raise HTTPException(
                    status_code=400,
                    detail=f"You already have an address labeled as {label}.",
                )

    @classmethod
    async def validate_label_for_update(
        cls, user_id: str, new_label: str, address_id: str, current_label: str
    ) -> None:
        """
        Validate label for address update.

        Args:
            user_id: The ID of the user
            new_label: The proposed new label
            address_id: The current address ID
            current_label: The current label of the address

        Raises:
            HTTPException: If validation fails
            ValueError: If label is invalid
        """
        normalized_new_label = AddressLabel.normalize_label(new_label)
        normalized_current_label = AddressLabel.normalize_label(current_label)

        if normalized_new_label not in AddressLabel.list():
            raise ValueError(
                f"Invalid label. Must be one of: {', '.join(AddressLabel.list())}"
            )

        # Only check for duplicates if label is being changed and requires uniqueness
        if (
            normalized_new_label != normalized_current_label
            and AddressLabel.is_unique_required(normalized_new_label)
        ):
            if await cls.check_existing_label(
                user_id, normalized_new_label, address_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"You already have an address labeled as {new_label}.",
                )
