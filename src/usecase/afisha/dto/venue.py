from dataclasses import dataclass

from src.domain.afisha import Venue


@dataclass
class VenueListResult:
    items: list[Venue]
    total: int
    page: int
    page_size: int
