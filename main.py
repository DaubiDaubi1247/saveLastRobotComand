#!/usr/bin/env python3
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Callable, Awaitable
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from RobotHelper.robot_poller import poll_robots
from service.robot_state_service import RobotStateService
from repository.robot_state_repository import RobotStateRepository
from repository.program_file_repository import ProgramFileRepository, ProgramSource
from service.robot_points_service import RobotPointsService
from repository.robot_points_repository import RobotPointsRepository
from repository.generated_points_repository import GeneratedPointsRepository
from Api.models.models import RobotStateResponse, RobotProgramResponse
from fastapi.middleware.cors import CORSMiddleware
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

origins = [
    "http://192.168.22.129:8080",  # Адрес, с которого идут запросы
]

# 2. Добавьте CORSMiddleware в приложение
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Разрешаем запросы с этого источника
    allow_credentials=True,         # Разрешаем передавать куки и заголовки авторизации
    allow_methods=["*"],            # Разрешаем все HTTP методы (GET, POST и т.д.)
    allow_headers=["*"],            # Разрешаем все заголовки
)

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

    if 400 <= response.status_code < 500:
        body_content = b"".join([chunk async for chunk in response.body_iterator])  # type: ignore[misc]
        error_detail = body_content.decode("utf-8", errors="replace")
        logger.warning(f"Ошибка клиента ({response.status_code}): {request.method} {request.url.path} - {error_detail}")
        return StreamingResponse(
            status_code=response.status_code,
            content=iter([body_content]),
            headers=response.headers,
            media_type=response.media_type
        )
    elif 500 <= response.status_code < 600:
        body_content = b"".join([chunk async for chunk in response.body_iterator])  # type: ignore[misc]
        error_detail = body_content.decode("utf-8", errors="replace")
        logger.error(f"Ошибка сервера ({response.status_code}): {request.method} {request.url.path} - {error_detail}")
        return StreamingResponse(
            status_code=response.status_code,
            content=iter([body_content]),
            headers=response.headers,
            media_type=response.media_type
        )

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


@app.get("/api/robots/{robot_name}/points", response_model=Dict[str, Dict[str, List[List[float]]]])
async def get_robot_points(robot_name: str, service: RobotPointsService = Depends(get_robot_points_service)) -> Dict[str, Dict[str, List[List[float]]]]:
    try:
        return service.get_robot_points(robot_name)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/robots/{robot_name}/points/generated", response_model=List[Dict[str, Any]])
async def get_robot_points_generated(robot_name: str, service: RobotPointsService = Depends(get_robot_points_service)) -> List[Dict[str, Any]]:
    try:
        return service.get_robot_points_generated(robot_name)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

