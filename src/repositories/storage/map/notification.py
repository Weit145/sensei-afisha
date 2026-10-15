from src.repositories.storage.models import ConnectionInfo, NotificationType


def model_to_map(info: ConnectionInfo) -> dict[str, str]:
    return {
        "user_ip": info.user_ip,
        "server_id": str(info.server_id),
        "n_type": str(info.n_type.value),
        "afisha_id": str(info.afisha_id),
    }


def dict_to_model(user_ip: str, raw: dict[str, str]) -> ConnectionInfo:
    return ConnectionInfo(
        user_ip=user_ip,
        server_id=int(raw["server_id"]),
        n_type=NotificationType(int(raw["n_type"])),
        afisha_id=int(raw["afisha_id"]),
    )
