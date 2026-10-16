import uuid
from dataclasses import dataclass


@dataclass
class AfishaStatsResult:
    afisha_id: uuid.UUID
    followers_count: int
