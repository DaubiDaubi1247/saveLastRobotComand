from pydantic import BaseModel
from typing import Optional, Dict, Any


class RequestData(BaseModel):
    data: Optional[Dict[str, Any]] = None


class RobotStateResponse(BaseModel):
    workshop: str
    robot: str
