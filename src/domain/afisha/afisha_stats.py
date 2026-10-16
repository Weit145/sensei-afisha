import uuid
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class AfishaStats:
    afisha_id: uuid.UUID
    followers_count: int

    def __post_init__(self):
        if self.followers_count < 0:
            raise ValueError(
                "Число подписчиков не может быть меньше нуля"
            )
