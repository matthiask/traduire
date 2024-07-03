from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import FileResponse
from django.shortcuts import render
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from app.ratelimiting import username_ratelimit


admin.site.enable_nav_sidebar = False
admin.site.site_header = admin.site.site_title = settings.META_TAGS["site_name"]
admin.site.login = username_ratelimit(rate="3/m")(admin.site.login)


def file_response(path):
    return lambda request: FileResponse(path.open("rb"))


urlpatterns = [
    path("", include("authlib.admin_oauth.urls")),
    path("admin/", admin.site.urls),
    path("404/", render, {"template_name": "404.html"}),
    path("favicon.ico", file_response(settings.BASE_DIR / "htdocs" / "favicon.ico")),
    path("favicon.png", file_response(settings.BASE_DIR / "htdocs" / "favicon.png")),
    *i18n_patterns(
        path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    ),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
