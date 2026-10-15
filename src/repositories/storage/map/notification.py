from src.repositories.storage.models import ConnectionInfo, NotificationType

def model_to_map(info: ConnectionInfo)->map:
    print("dd")

def dict_to_model( user_ip:str, info)->ConnectionInfo:
    return ConnectionInfo(
        user_ip=user_ip,
        server_id=int(raw["server_id"]),
        n_type=NotificationType(int(raw["n_type"])),
        afisha_id=raw["afisha_id"],
    )
