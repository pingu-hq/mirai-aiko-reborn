from asyncio import to_thread

from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)


class PasswordHasherService:
    _password_hasher = PasswordHasher()

    async def hash_password(self, password: str) -> str | None:
        try:
            return await to_thread(self._password_hasher.hash, password)
        except HashingError:
            return None


    async def verify_hash_password(self, hash_password: str | None, password: str | None) -> bool:
        if password is None or hash_password is None:
            return False
        try:
            return await to_thread(
                self._password_hasher.verify,
                hash_password, password
            )
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False



