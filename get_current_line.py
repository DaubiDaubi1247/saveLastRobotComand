#!/usr/bin/env python3
"""Основной модуль: REST API сервер + фоновый опрос роботов"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from robot_poller import poll_robots
from robot_state_service import RobotStateService
from robot_state_repository import RobotStateRepository

# Server configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan контекст для запуска фоновых задач"""
    task = asyncio.create_task(poll_robots())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# FastAPI приложение
app = FastAPI(title="Robot Server")


class RequestData(BaseModel):
    data: Optional[Dict[str, Any]] = None


class RobotStateResponse(BaseModel):
    workshop: str
    robot: str


@app.get("/health")
async def health() -> Dict[str, str]:
    """Проверка доступности сервера"""
    return {"status": "ok"}


@app.get("/robots", response_model=List[RobotStateResponse])
async def get_robots() -> List[RobotStateResponse]:
    """Получить состояние всех роботов"""
    repository = RobotStateRepository()
    service = RobotStateService(repository)
    states = service.get_all_robots_state()
    return [RobotStateResponse(workshop=s.workshop, robot=s.robot) for s in states]


def main() -> None:
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")


if __name__ == "__main__":
    main()
