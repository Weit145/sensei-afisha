from src.domain.user import User, UserRole
from src.repositories.storage.models.user import UserModel


def map_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        username=user.username,
        role=user.role.value,
        hashed_password=user.hashed_password,
        tg_url=user.tg_url,
        vk_url=user.vk_url,
        created_at=user.created_at,
    )


def map_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        username=model.username,
        role=UserRole(model.role),
        hashed_password=model.hashed_password,
        tg_url=model.tg_url,
        vk_url=model.vk_url,
        created_at=model.created_at,
    )
