from django.urls import path

from projects import views


app_name = "projects"
urlpatterns = [
    path("", views.projects, name="projects"),
    path("project/<slug:slug>/", views.project, name="project"),
    path(
        "project/<slug:project>/catalog/<str:language_code>/<str:domain>/",
        views.catalog,
        name="catalog",
    ),
    path("suggest/", views.suggest),
    path("api/pofile/<str:language_code>/<str:domain>/", views.pofile, name="pofile"),
]
