from dataclasses import dataclass, field

from enum import Enum

class NotificationType(Enum):
    MAIN_MENU = 1
    DISCUSSION = 2
    FEEDBACK = 3

class Notification(Protocol):
    n_type: NotificationType = field(default=Notification.MAIN_MENU)
    content: str = field(default="") 

