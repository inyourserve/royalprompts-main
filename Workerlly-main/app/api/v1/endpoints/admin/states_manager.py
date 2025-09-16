from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.models.database import db
from app.utils.admin_roles import admin_permission_required

router = APIRouter()

# Constants for module and actions
MODULE = "states"
ACTIONS = {"VIEW": "read"}


class StateBase(BaseModel):
    id: str
    name: str


class StatesResponse(BaseModel):
    states: List[StateBase]


@router.get("/states", response_model=StatesResponse)
async def get_states(
    current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"])),
):
    """Get all states for the dropdown selection"""
    states = list(db.states.find({}))
    return {
        "states": [{"id": str(state["_id"]), "name": state["name"]} for state in states]
    }
