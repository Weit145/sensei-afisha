
from typing import Protocol

from fastapi import UploadFile


class ImgInfastructure(Protocol):
    async def save_image(self, image: UploadFile) -> str:
        ...

    async def save_images(self, images: list[UploadFile]) -> list[str]:
        ...

    async def delete_image(self, file_name: str) -> None:
        ...
