from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
):

    payload = decode_token(token)

    if payload is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return payload


def require_role(
    allowed_roles: list[str],
):

    def role_checker(
        current_user=Depends(get_current_user),
    ):

        if current_user["role"] not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return role_checker