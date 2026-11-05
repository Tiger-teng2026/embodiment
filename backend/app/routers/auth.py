from fastapi import APIRouter, Depends

from app.auth import create_token, credentials_match, get_current_user
from app.errors import api_error
from app.schemas import LoginIn, TokenOut, UserOut

router = APIRouter()


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn) -> TokenOut:
    if not credentials_match(body.username, body.password):
        raise api_error(401, "INVALID_CREDENTIALS")
    return TokenOut(access_token=create_token(body.username))


@router.get("/me", response_model=UserOut)
def me(username: str = Depends(get_current_user)) -> UserOut:
    return UserOut(username=username)
