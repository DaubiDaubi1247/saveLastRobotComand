from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class RequestData(BaseModel):
    data: Optional[Dict[str, Any]] = None


class RobotStateResponse(BaseModel):
    workshop: str
    robot: str


class RobotProgramResponse(BaseModel):
    robot: str
    program_name: Optional[str] = None
    snr_c: Optional[int] = None
    program_line: Optional[str] = None
    point_name: Optional[str] = None


class RobotPointsResponse(BaseModel):
    s: List[List[float]]
    w: List[List[float]]
    source: Optional[str] = None


class GeneratedPointsFile(BaseModel):
    file_name: str
    points: Dict[str, List[List[float]]]


class GeneratedPointsResponse(BaseModel):
    files: List[GeneratedPointsFile]
