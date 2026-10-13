from src.domain.user import User
from src.repositories.storage.models.user import UserModel


def map_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        name=user.name,
        ip=user.ip,
        created_at=user.created_at,
    )


def map_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        name=model.name,
        ip=model.ip,
        created_at=model.created_at,
    )
