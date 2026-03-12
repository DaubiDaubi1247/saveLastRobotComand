from pydantic import BaseModel
from typing import Optional, List


class RobotStateResponse(BaseModel):
    workshop: str
    robot: str


class RobotProgramResponse(BaseModel):
    robot: str
    program_name: Optional[str] = None
    snr_c: Optional[int] = None
    program_line: Optional[str] = None
    point_name: Optional[str] = None
