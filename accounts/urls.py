from django.urls import include, path

from accounts import views


urlpatterns = [
    path("logout/", views.logout, name="logout"),
    path("google-sso/", views.google_sso, name="google-sso"),
    path("", include("django.contrib.auth.urls")),
]
