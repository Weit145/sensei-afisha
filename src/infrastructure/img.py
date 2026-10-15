import logging
import re
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from src.core.config import settings

logger = logging.getLogger(__name__)


class ImgInfastructure:
    def __init__(self, upload_dir: str | Path = settings.upload_dir) -> None:
        self.upload_dir = Path(upload_dir)

    @staticmethod
    async def parse_image(image: UploadFile) -> str:
        header = await image.read(16)
        await image.seek(0)

        if header.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return ".png"
        if header.startswith((b"GIF87a", b"GIF89a")):
            return ".gif"
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            return ".webp"

        raise ValueError("Поддерживаются только JPEG, PNG, GIF и WebP")

    @staticmethod
    def _write_image(source: BinaryIO, path: Path) -> None:
        try:
            with path.open("xb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
        except Exception:
            path.unlink(missing_ok=True)
            raise

    async def save_image(self, image: UploadFile) -> str:
        extension = await self.parse_image(image)
        file_name = f"{uuid.uuid4().hex}{extension}"
        await run_in_threadpool(self.upload_dir.mkdir, parents=True, exist_ok=True)
        await run_in_threadpool(self._write_image, image.file, self.upload_dir / file_name)
        return file_name

    async def save_images(self, images: list[UploadFile]) -> list[str]:
        file_names: list[str] = []
        try:
            for image in images:
                file_names.append(await self.save_image(image))
        except Exception:
            for file_name in file_names:
                try:
                    await self.delete_image(file_name)
                except OSError:
                    logger.exception("Не удалось удалить изображение %s", file_name)
            raise
        return file_names

    async def delete_image(self, file_name: str) -> None:
        if re.fullmatch(r"[0-9a-f]{32}\.(?:jpg|png|gif|webp)", file_name) is None:
            raise ValueError("Некорректное имя файла")
        path = self.upload_dir / file_name
        await run_in_threadpool(path.unlink, missing_ok=True)
