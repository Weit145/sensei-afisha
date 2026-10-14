from src.domain.afisha import Afisha
from src.repositories.storage.models.afisha import AfishaModel
from src.usecase.afisha.dto import AfishaListItem


def map_to_model(afisha: Afisha) -> AfishaModel:
    return AfishaModel(
        id=afisha.id,
        title=afisha.title,
        description=afisha.description,
        short_description=afisha.short_description,
        starts_at=afisha.starts_at,
        ends_at=afisha.ends_at,
        age_limit=afisha.age_limit,
        status=afisha.status,
        created_at=afisha.created_at,
        updated_at=afisha.updated_at,
    )


def map_to_domain(model: AfishaModel) -> Afisha:
    return Afisha(
        id=model.id,
        title=model.title,
        description=model.description,
        short_description=model.short_description,
        starts_at=model.starts_at,
        ends_at=model.ends_at,
        venue_ids=[venue.id for venue in model.venues],
        age_limit=model.age_limit,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def map_to_list_item(model: AfishaModel) -> AfishaListItem:
    return AfishaListItem(
        afisha=map_to_domain(model),
        venue_names=[venue.name for venue in model.venues],
        cover_file_name=next(
            (image.file_name for image in model.images if image.is_cover),
            None,
        ),
    )
