import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from src.core.config import settings

MAX_IMAGE_SIZE = 10 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
IMAGE_TYPES = {
    "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (".webp", lambda data: data.startswith(b"RIFF") and data[8:12] == b"WEBP"),
}


def save_image(image: UploadFile) -> tuple[uuid.UUID, str]:
    image_type = IMAGE_TYPES.get(image.content_type or "")
    header = image.file.read(12)
    if image_type is None or not image_type[1](header):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Поддерживаются только JPEG, PNG и WebP",
        )

    image_id = uuid.uuid4()
    filename = f"{image_id}{image_type[0]}"
    destination = Path(settings.upload_dir) / filename
    size = len(header)
    created = False

    try:
        with destination.open("xb") as output:
            created = True
            output.write(header)
            while chunk := image.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_IMAGE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Изображение не должно превышать 10 МБ",
                    )
                output.write(chunk)
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise

    return image_id, filename
