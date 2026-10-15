from src.domain.afisha import Venue
from src.repositories.storage.models.afisha import VenueModel


def map_to_model(venue: Venue) -> VenueModel:
    return VenueModel(
        id=venue.id,
        name=venue.name,
        city=venue.city,
        address=venue.address,
        latitude=venue.latitude,
        longitude=venue.longitude,
        created_at=venue.created_at,
    )


def map_to_domain(model: VenueModel) -> Venue:
    return Venue(
        id=model.id,
        name=model.name,
        city=model.city,
        address=model.address,
        latitude=model.latitude,
        longitude=model.longitude,
        created_at=model.created_at,
    )
