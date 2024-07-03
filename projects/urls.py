import polib
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import path

from projects.models import Catalog


@login_required
def projects(request):
    return render(
        request, "projects/projects.html", {"projects": request.user.projects.all()}
    )


@login_required
def project(request, pk):
    project = get_object_or_404(request.user.projects.all(), pk=pk)
    return render(request, "projects/project.html", {"project": project})


@login_required
def catalog(request, project, pk):
    catalog = get_object_or_404(
        Catalog.objects.filter(project__in=request.user.projects.all()),
        project=project,
        pk=pk,
    )

    po = polib.pofile(catalog.pofile, wrapwidth=0)

    return render(
        request,
        "projects/catalog.html",
        {"catalog": catalog, "project": catalog.project, "po": po},
    )


app_name = "projects"
urlpatterns = [
    path("", projects, name="projects"),
    path("project/<int:pk>/", project, name="project"),
    path("project/<int:project>/catalog/<int:pk>/", catalog, name="catalog"),
]
