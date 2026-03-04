#!/usr/bin/env python3
"""Основной модуль: REST API сервер + фоновый опрос роботов"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
from robot_poller import poll_robots

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
app = FastAPI(title="Robot Server", lifespan=lifespan)


class RequestData(BaseModel):
    data: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health() -> Dict[str, str]:
    """Проверка доступности сервера"""
    return {"status": "ok"}


@app.api_route("/api/{endpoint:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_endpoint(endpoint: str, request: Request) -> Dict[str, Any]:
    """Обработчик REST API запросов"""
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
