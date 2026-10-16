from dataclasses import dataclass, field, asdict
from enum import Enum
import json

# нужно для задания типа сообщения
class NotificationType(Enum):
    MAIN_MENU = 1
    DISCUSSION = 2
    FEEDBACK = 3

# содержит в себе тип сообщения и его текст
# текст, айди юзера
@dataclass(slots=True)
class Notification:
    n_type: NotificationType = field(default=NotificationType.MAIN_MENU)
    text: str = field(default="")
    user_id: str = field(default="")

    def dump_to_json(self) -> str:
        """Сериализует уведомление в JSON-строку."""
        data = asdict(self)
        data["n_type"] = self.n_type.value  # Enum → int
        return json.dumps(data, ensure_ascii=False)