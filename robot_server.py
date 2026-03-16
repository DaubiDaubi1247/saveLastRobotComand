#!/usr/bin/env python3
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Callable, Awaitable
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response
from RobotHelper.robot_poller import poll_robots
from service.robot_state_service import RobotStateService
from repository.robot_state_repository import RobotStateRepository
from repository.program_file_repository import ProgramFileRepository, ProgramSource
from service.robot_points_service import RobotPointsService
from repository.robot_points_repository import RobotPointsRepository
from repository.generated_points_repository import GeneratedPointsRepository
from Api.models.models import RobotStateResponse, RobotProgramResponse
from config import SERVER_HOST, SERVER_PORT
from utils.logger import logger
import time
import traceback


async def _get_robot_program_with_source(
    robot_name: str,
    service: RobotStateService,
    source: ProgramSource
) -> RobotProgramResponse:
    """Helper-функция для получения программы робота из указанной папки."""
    try:
        service.download_robot_files(
            robot_name,
            download_work=(source == ProgramSource.WORK),
            download_generated=(source == ProgramSource.GENERATED)
        )
    except Exception as e:
        folder_name = "work" if source == ProgramSource.WORK else "generated"
        raise HTTPException(status_code=500, detail=f"Ошибка при скачивании файлов {folder_name}: {str(e)}")

    try:
        program = service.get_robot_program(robot_name, source=source)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RobotProgramResponse(
        robot=program.robot,
        program_name=program.program_name,
        snr_c=program.snr_c,
        program_line=program.program_line,
        point_name=program.point_name
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Запуск приложения")
    file_repository = ProgramFileRepository()
    repository = RobotStateRepository()
    service = RobotStateService(repository, file_repository)
    points_repository = RobotPointsRepository()
    generated_points_repository = GeneratedPointsRepository()
    points_service = RobotPointsService(points_repository, generated_points_repository)

    app.state.robot_state_service = service
    app.state.robot_points_service = points_service

    task = asyncio.create_task(poll_robots())
    logger.info("Запущен фоновый опрос роботов")
    yield
    task.cancel()
    logger.info("Остановка приложения")
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Robot Server", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start_time = time.time()
    logger.info(f"Запрос: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Ошибка: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise

    process_time = time.time() - start_time
    logger.info(f"Ответ: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")

    return response


def get_robot_state_service(request: Request) -> RobotStateService:
    return request.app.state.robot_state_service


def get_robot_points_service(request: Request) -> RobotPointsService:
    return request.app.state.robot_points_service


@app.get("/health")
async def health() -> Dict[str, str]:
    logger.debug("Health check запрос")
    return {"status": "ok"}


@app.get("/api/robots", response_model=List[RobotStateResponse])
async def get_robots(service: RobotStateService = Depends(get_robot_state_service)) -> List[RobotStateResponse]:
    states = service.get_all_robots_state()
    return [RobotStateResponse(workshop=s.workshop, robot=s.robot) for s in states]


@app.get("/api/robots/{robot_name}/program", response_model=RobotProgramResponse)
async def get_robot_program(robot_name: str, service: RobotStateService = Depends(get_robot_state_service)) -> RobotProgramResponse:
    return await _get_robot_program_with_source(robot_name, service, source=ProgramSource.WORK)


@app.get("/api/robots/{robot_name}/program/generated", response_model=RobotProgramResponse)
async def get_robot_program_generated(robot_name: str, service: RobotStateService = Depends(get_robot_state_service)) -> RobotProgramResponse:
    return await _get_robot_program_with_source(robot_name, service, source=ProgramSource.GENERATED)


@app.get("/api/robots/{robot_name}/points", response_model=Dict[str, Any])
async def get_robot_points(robot_name: str, service: RobotPointsService = Depends(get_robot_points_service)) -> Dict[str, Any]:
    try:
        return service.get_robot_points(robot_name)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/robots/{robot_name}/points/generated", response_model=List[Dict[str, Any]])
async def get_robot_points_generated(robot_name: str, service: RobotPointsService = Depends(get_robot_points_service)) -> List[Dict[str, Any]]:
    try:
        return service.get_robot_points_generated(robot_name)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


def main() -> None:
    logger.info(f"Запуск сервера на {SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")


if __name__ == "__main__":
    main()
