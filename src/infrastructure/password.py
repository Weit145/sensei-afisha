from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash("invalid-login-placeholder")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    try:
        valid = password_hash.verify(password, hashed_password or dummy_password_hash)
    except UnknownHashError:
        return False
    return bool(hashed_password) and valid
