from argon2 import PasswordHasher
from asyncio import to_thread
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError, HashingError


def get_password_hasher():
    if not hasattr(get_password_hasher, 'ph'):
        get_password_hasher.ph = PasswordHasher()
    return get_password_hasher.ph


class AuthPasswordService:
    def __init__(self):
        self.ph = get_password_hasher()

    def _hash_password(self, password):
        return self.ph.hash(password)

    def _verify_password(self, hash_password, password):
        return self.ph.verify(hash_password, password)

    async def make_hash_password(self, password: str):
        try:
            return await to_thread(self._hash_password, password)
        except HashingError:
            return None

    async def verify_hash_password(self, hash_password: str, password: str):
        try:
            return await to_thread(
                self._verify_password,
                hash_password, password
            )
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return None


