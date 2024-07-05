import polib
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.template.defaulttags import query_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import User
from form_rendering import adapt_rendering
from projects import translators
from projects.forms import EntriesForm, FilterForm, SuggestForm
from projects.models import Catalog, Project


ENTRIES_PER_PAGE = 20


@login_required
def projects(request):
    return render(
        request,
        "projects/projects.html",
        {"projects": Project.objects.for_user(request.user)},
    )


@login_required
def project(request, slug):
    project = get_object_or_404(Project.objects.for_user(request.user), slug=slug)
    return render(
        request,
        "projects/project.html",
        {
            "project": project,
            "api_url": request.build_absolute_uri(project.get_api_url()),
        },
    )


@login_required
def catalog(request, project, language_code, domain):
    catalog = get_object_or_404(
        Catalog.objects.for_user(request.user),
        project__slug=project,
        language_code=language_code,
        domain=domain,
    )

    entries = [entry for entry in catalog.po if not entry.obsolete]
    total = len(entries)

    filter_form = FilterForm(request.GET)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get("pending"):
            entries = [entry for entry in entries if not entry.translated()]
            total = len(entries)
        if query := data.get("query", "").casefold():
            entries = [entry for entry in entries if query in str(entry).casefold()]
            total = len(entries)
        if start := data.get("start") or 0:
            if len(entries) > start:
                entries = entries[start:]
            else:
                start = 0
    else:
        start = 0
        return http.HttpResponseRedirect(".")

    data = [request.POST] if request.method == "POST" else []
    entries = entries[:ENTRIES_PER_PAGE]
    form = EntriesForm(*data, entries=entries, language_code=language_code)

    if form.is_valid():
        form.update(catalog.po, request=request)
        catalog.pofile = str(catalog.po)
        catalog.save()

        return http.HttpResponseRedirect(
            query_string(
                None,
                request.GET,
                start=start,
            )
        )

    return render(
        request,
        "projects/catalog.html",
        {
            "catalog": catalog,
            "project": catalog.project,
            "po": catalog.po,
            "filter_form": adapt_rendering(filter_form),
            "form": adapt_rendering(form),
            "entries": entries,
            "previous_url": query_string(
                None, request.GET, start=start - ENTRIES_PER_PAGE
            )
            if start - ENTRIES_PER_PAGE >= 0
            else None,
            "next_url": query_string(None, request.GET, start=start + ENTRIES_PER_PAGE)
            if start + ENTRIES_PER_PAGE < total
            else None,
            "start": start + 1,
            "end": min(total, start + ENTRIES_PER_PAGE),
            "total": total,
        },
    )


@require_POST
def suggest(request):
    if not request.user.is_authenticated:
        return http.HttpResponseForbidden()

    form = SuggestForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            translation = translators.translate_by_deepl(
                data["msgid"], data["language_code"], settings.DEEPL_AUTH_KEY
            )
        except translators.TranslationError as exc:
            return http.JsonResponse({"error": str(exc)})
        return http.JsonResponse({"msgstr": translation})

    return http.HttpResponseBadRequest()


@csrf_exempt
def pofile(request, project, language_code, domain):
    user = User.objects.filter(token=request.headers.get("x-token")).first()
    if not user:
        return http.HttpResponseForbidden()

    project = Project.objects.for_user(user).filter(slug=project).first()
    if not project:
        return http.HttpResponseNotFound()

    if request.method == "GET":
        if catalog := project.catalogs.filter(
            language_code=language_code, domain=domain
        ).first():
            return http.HttpResponse(catalog.pofile, content_type="text/plain")
        return http.HttpResponseNotFound()

    if request.method == "PUT":
        new = polib.pofile(request.body.decode("utf-8"))
        old, created = project.catalogs.get_or_create(
            language_code=language_code,
            domain=domain,
            defaults={"pofile": ""},
        )
        if created:
            old.pofile = str(new)
        else:
            old.po.merge(new)
            old.pofile = str(old.po)
        old.save()
        return http.HttpResponse(status=202)  # Accepted

    return http.HttpResponse(status=405)  # Method Not Allowed
