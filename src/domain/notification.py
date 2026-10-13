from dataclasses import dataclass, field

from enum import Enum


# нужно для задания типа сообщения
class NotificationType(Enum):
    MAIN_MENU = 1
    DISCUSSION = 2
    FEEDBACK = 3

# содержит в себе тип сообзения и его текст
@dataclass(slot=True)
class Notification(Protocol):
    n_type: NotificationType = field(default=Notification.MAIN_MENU)
    content: str = field(default="") 

