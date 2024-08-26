from django.urls import path

from projects import views


app_name = "projects"
urlpatterns = [
    path("", views.projects, name="projects"),
    path("<slug:slug>/", views.project, name="project"),
    path(
        "<slug:project>/<str:language_code>/<str:domain>/",
        views.catalog,
        name="catalog",
    ),
    path("api/suggest/", views.suggest),
    path(
        "api/pofile/<str:project>/<str:language_code>/<str:domain>/",
        views.pofile,
        name="pofile",
    ),
    path(
        "traduire.toml",
        views.traduire_toml,
        name="traduire_toml",
    ),
    path("<slug:slug>/messages.csv", views.messages_csv, name="messages_csv"),
]
