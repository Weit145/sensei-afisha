import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.logging import setup_logging
from .repositories.storage.postgres.db_helper import db_helper
from .transport.api.v1.handler.afisha.afisha import router as afisha
from .transport.api.v1.handler.afisha.img import router as img
from .transport.api.v1.handler.afisha.venue import router as venue
from .transport.api.v1.handler.discussion.message import router as discussion

logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Запуск приложения")
    yield
    await db_helper.engine.dispose()
    logger.info("Остановка приложения")


app = FastAPI(
    lifespan=lifespan,
    title="Template Monolit",
)

app.include_router(afisha, prefix="/api")
app.include_router(venue, prefix="/api")
app.include_router(img, prefix="/api")
app.include_router(discussion, prefix="/api")

@app.get("/_info", status_code=status.HTTP_200_OK)
async def info():
    return status.HTTP_200_OK

app.mount(
    "/uploads",
    StaticFiles(directory=settings.upload_dir, check_dir=False),
    name="uploads"
)


if __name__ == "__main__":
    uvicorn.run("src.main:app", reload=True)
