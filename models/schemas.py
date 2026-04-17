from pydantic import BaseModel, Field
from typing import Literal


class PhaseUpdateRequest(BaseModel):
    phase: Literal["PRE_MATCH", "ONGOING", "HALFTIME", "POST_MATCH"] = Field(
        ..., description="The event phase to transition the simulation to."
    )
