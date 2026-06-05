from .services import get_branding_snapshot


def app_branding(request):
    return {"app_branding": get_branding_snapshot()}
