#!/usr/bin/env python3
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional
import uvicorn
from fastapi import FastAPI, Depends
from RobotHelper.robot_poller import poll_robots
from RobotStateService.robot_state_service import RobotStateService
from RobotStateRepository.robot_state_repository import RobotStateRepository
from RobotStateService.robot_points_service import RobotPointsService
from RobotStateRepository.robot_points_repository import RobotPointsRepository
from Api.models.models import RobotStateResponse, RobotProgramResponse
from RobotStateRepository.program_file_repository import ProgramFileRepository

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

_repository: Optional[RobotStateRepository] = None
_service: Optional[RobotStateService] = None
_points_repository: Optional[RobotPointsRepository] = None
_points_service: Optional[RobotPointsService] = None
_file_repository: Optional[ProgramFileRepository] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _repository, _service, _points_repository, _points_service, _file_repository
    _file_repository = ProgramFileRepository()
    _repository = RobotStateRepository()
    _service = RobotStateService(_repository, _file_repository)
    _points_repository = RobotPointsRepository()
    _points_service = RobotPointsService(_points_repository)
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


def get_robot_points_service() -> RobotPointsService:
    if _points_service is None:
        raise RuntimeError("Points service not initialized")
    return _points_service


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/robots", response_model=List[RobotStateResponse])
async def get_robots(service: RobotStateService = Depends(get_robot_state_service)) -> List[RobotStateResponse]:
    states = service.get_all_robots_state()
    return [RobotStateResponse(workshop=s.workshop, robot=s.robot) for s in states]


@app.get("/api/robots/programs", response_model=List[RobotProgramResponse])
async def get_robots_programs(service: RobotStateService = Depends(get_robot_state_service)) -> List[RobotProgramResponse]:
    programs = service.get_all_robots_programs()
    return [RobotProgramResponse(
        robot=p.robot,
        program_name=p.program_name,
        snr_c=p.snr_c,
        program_line=p.program_line
    ) for p in programs]


@app.get("/api/robots/{robot_name}/program", response_model=RobotProgramResponse)
async def get_robot_program(robot_name: str, service: RobotStateService = Depends(get_robot_state_service)) -> RobotProgramResponse:
    program = service.get_robot_program(robot_name)
    return RobotProgramResponse(
        robot=program.robot,
        program_name=program.program_name,
        snr_c=program.snr_c,
        program_line=program.program_line
    )


@app.get("/api/robots/{robot_name}/points", response_model=Dict[str, Any])
async def get_robot_points(robot_name: str, service: RobotPointsService = Depends(get_robot_points_service)) -> Dict[str, Any]:
    return service.get_robot_points(robot_name)


def main() -> None:
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")


if __name__ == "__main__":
    main()
