from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UsersRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthUseCase:
    def __init__(self, users_repo: UsersRepository) -> None:
        self.users_repo = users_repo

    async def register(self, payload: RegisterRequest) -> User:
        existing_user = await self.users_repo.get_by_email(payload.email)
        if existing_user is not None:
            raise UserAlreadyExistsError()

        return await self.users_repo.create(
            email=payload.email,
            password_hash=hash_password(payload.password),
        )

    async def login(self, *, email: str, password: str) -> TokenResponse:
        user = await self.users_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        access_token = create_access_token(subject=str(user.id), role=user.role)
        return TokenResponse(access_token=access_token)

    async def me(self, *, user_id: str | None) -> User:
        if user_id is None:
            raise InvalidTokenError()

        try:
            parsed_user_id = int(user_id)
        except ValueError as exc:
            raise InvalidTokenError() from exc

        user = await self.users_repo.get_by_id(parsed_user_id)
        if user is None:
            raise UserNotFoundError()
        return user
