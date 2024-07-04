from django.conf import settings


def site_context(request):
    return {"TESTING": settings.TESTING}
