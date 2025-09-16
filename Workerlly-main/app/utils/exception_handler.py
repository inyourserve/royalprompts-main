"""
Custom exception handling utilities for API error responses.
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def create_validation_exception_handler():
    """
    Create and return a validation exception handler that converts Pydantic
    validation errors to user-friendly error messages.

    Returns:
        function: Exception handler function for RequestValidationError
    """

    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Convert Pydantic validation errors to user-friendly error messages.

        Args:
            request: The FastAPI request object
            exc: The RequestValidationError exception

        Returns:
            JSONResponse: A user-friendly error response
        """
        errors = exc.errors()
        error_detail = errors[0] if errors else {"type": "unknown"}

        error_type = error_detail.get("type", "")
        error_loc = error_detail.get("loc", [])

        # Field-specific custom error messages
        if "review" in str(error_loc):
            if error_type == "string_too_short":
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": "Review message can't be empty"}
                )

        if "rating" in str(error_loc):
            if error_type in ["greater_than_equal", "less_than_equal"]:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": "Rating must be between 1 and 5"}
                )

        # Default error message
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Please check your input and try again"}
        )

    return validation_exception_handler
