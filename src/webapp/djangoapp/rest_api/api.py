from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from ninja.security import HttpBasicAuth


class DjangoBasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            return user
        return None


class AuthenticatedUserSchema(Schema):
    username: str
    is_staff: bool
    is_superuser: bool


api = NinjaAPI(
    title="IT Operation Ticketing Demo Service API",
    version="1.0.0",
    auth=DjangoBasicAuth(),
)


@api.get("/health")
def health(request):
    return {"status": "ok"}


@api.get("/auth/me", response=AuthenticatedUserSchema)
def current_user(request):
    return {
        "username": request.auth.get_username(),
        "is_staff": request.auth.is_staff,
        "is_superuser": request.auth.is_superuser,
    }
