class ApiError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class AuthenticationError(ApiError):
    pass


class AuthorizationError(ApiError):
    pass


class ConflictError(ApiError):
    pass


class ValidationError(ApiError):
    def __init__(self, message: str, *, status_code: int | None = None, payload=None, errors=None):
        super().__init__(message, status_code=status_code, payload=payload)
        self.errors = errors or {}
