from dataclasses import dataclass

# это лежит в редис . server_id - id сервера на будущее, если их несколько будет
# user_id - id юзера
# chat_id - id обсуждения/отзывов . если нет , то главное меню
class NotificationType(Enum):
    MAIN_MENU = 1
    DISCUSSION = 2
    FEEDBACK = 3

@dataclass
class ConnectionInfo():
    user_ip : str
    chat_id : int | None
    server_id : int 
    n_type: NotificationType 
