import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status

from .core.logging import setup_logging
from .repositories.storage.postgres.db_helper import db_helper
from .transport.api.v1.handler.user import router as users

logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Запуск приложения")
    yield
    await db_helper.engine.dispose()
    logger.info("Остановка приложения")


app = FastAPI(
    lifespan=lifespan,
    title="Template Monolit",
)

app.include_router(users, prefix="/api")


@app.get("/_info", status_code=status.HTTP_200_OK)
async def info():
    return status.HTTP_200_OK


if __name__ == "__main__":
    uvicorn.run("src.main:app", reload=True)
