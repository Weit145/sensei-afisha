import uuid

from src.repositories.storage.models.afisha import AfishaImageModel
from src.usecase.afisha.dto import AfishaImageItem


def map_file_names_to_models(
    afisha_id: uuid.UUID,
    file_names: list[str],
) -> list[AfishaImageModel]:
    return [
        map_to_image_model(afisha_id, file_name, position, position == 0)
        for position, file_name in enumerate(file_names)
    ]


def map_to_image_model(
    afisha_id: uuid.UUID,
    file_name: str,
    position: int,
    is_cover: bool,
) -> AfishaImageModel:
    return AfishaImageModel(
        id=uuid.uuid4(),
        afisha_id=afisha_id,
        file_name=file_name,
        is_cover=is_cover,
        position=position,
    )


def map_to_image_item(model: AfishaImageModel) -> AfishaImageItem:
    return AfishaImageItem(
        id=model.id,
        file_name=model.file_name,
        is_cover=model.is_cover,
        position=model.position,
    )
