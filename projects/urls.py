from django.urls import path

from projects import views


app_name = "projects"
urlpatterns = [
    path("", views.projects, name="projects"),
    path("project/<int:pk>/", views.project, name="project"),
    path("project/<int:project>/catalog/<int:pk>/", views.catalog, name="catalog"),
]
