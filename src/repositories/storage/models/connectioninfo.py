from dataclasses import dataclass

from enum import Enum

# это лежит в редис . server_id - id сервера на будущее, если их несколько будет
# user_id - id юзера
class NotificationType(Enum):
    MAIN_MENU = 1
    DISCUSSION = 2
    FEEDBACK = 3

MAIN_MENU_ID = -1
@dataclass
class ConnectionInfo():
    user_ip : str
    server_id : int 
    n_type: NotificationType 
    afisha_id: int = MAIN_MENU_ID
