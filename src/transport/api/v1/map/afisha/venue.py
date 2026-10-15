from src.domain.afisha import Venue, VenueUpdate
from src.transport.api.v1.schemas.afisha import (
    CreateVenue,
    ResponseVenue,
    UpdateVenue,
    VenueListResponse,
)
from src.usecase.afisha.dto import VenueListResult


def map_to_domain(venue: CreateVenue) -> Venue:
    return Venue(
        name=venue.name,
        city=venue.city,
        address=venue.address,
        latitude=venue.latitude,
        longitude=venue.longitude,
    )


def map_to_response(venue: Venue) -> ResponseVenue:
    return ResponseVenue(
        id=venue.id,
        name=venue.name,
        city=venue.city,
        address=venue.address,
        latitude=venue.latitude,
        longitude=venue.longitude,
    )


def map_to_update_domain(venue: UpdateVenue) -> VenueUpdate:
    return VenueUpdate(
        name=venue.name,
        city=venue.city,
        address=venue.address,
        latitude=venue.latitude,
        longitude=venue.longitude,
    )


def map_to_list_response(result: VenueListResult) -> VenueListResponse:
    return VenueListResponse(
        items=[map_to_response(venue) for venue in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )
