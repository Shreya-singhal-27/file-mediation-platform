from fastapi import HTTPException, status


class AuthenticationException(HTTPException):

    def __init__(self):

        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


class AuthorizationException(HTTPException):

    def __init__(self):

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )


class ResourceNotFoundException(HTTPException):

    def __init__(self, resource: str):

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
        )


class BadRequestException(HTTPException):

    def __init__(self, message: str):

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )