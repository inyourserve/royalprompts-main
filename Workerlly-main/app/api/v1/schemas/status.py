from pydantic import BaseModel


class StatusUpdateRequest(BaseModel):
    status: bool
