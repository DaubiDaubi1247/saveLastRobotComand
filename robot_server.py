#!/usr/bin/env python3
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional
import uvicorn
from fastapi import FastAPI, Request, Depends
from robot_poller import poll_robots
from RobotStateService.robot_state_service import RobotStateService
from RobotStateRepository.robot_state_repository import RobotStateRepository
from Api.models.models import RobotStateResponse

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

_repository: Optional[RobotStateRepository] = None
_service: Optional[RobotStateService] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _repository, _service
    _repository = RobotStateRepository()
    _service = RobotStateService(_repository)
    task = asyncio.create_task(poll_robots())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Robot Server", lifespan=lifespan)


def get_robot_state_service() -> RobotStateService:
    if _service is None:
        raise RuntimeError("Service not initialized")
    return _service


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/robots", response_model=List[RobotStateResponse])
async def get_robots(service: RobotStateService = Depends(get_robot_state_service)) -> List[RobotStateResponse]:
    states = service.get_all_robots_state()
    return [RobotStateResponse(workshop=s.workshop, robot=s.robot) for s in states]


@app.api_route("/api/{endpoint:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_endpoint(endpoint: str, request: Request) -> Dict[str, Any]:
    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        body = {}

    return {
        "status": "ok",
        "endpoint": endpoint,
        "method": request.method,
        "data": body
    }


def main() -> None:
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")


if __name__ == "__main__":
    main()
