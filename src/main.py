import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.logging import setup_logging
from .repositories.storage.postgres.db_helper import db_helper
from .transport.api.v1.handler.afisha.afisha import router as afisha
from .transport.api.v1.handler.afisha.img import router as img
from .transport.api.v1.handler.afisha.venue import router as venue
from .transport.api.v1.handler.auth.auth import router as auth
from .transport.api.v1.handler.auth.user import router as users
from .transport.api.v1.handler.discussion.message import router as discussion
from .transport.api.v1.handler.notification.notification import router as notification
from .transport.api.v1.handler.reviews.reviews import router as reviews

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
    title="Sensei Afisha",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

app.include_router(afisha, prefix="/api")
app.include_router(venue, prefix="/api")
app.include_router(img, prefix="/api")
app.include_router(discussion, prefix="/api")
app.include_router(auth, prefix="/api")
app.include_router(users, prefix="/api")
app.include_router(notification, prefix="/api")
app.include_router(reviews, prefix="/api")

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
