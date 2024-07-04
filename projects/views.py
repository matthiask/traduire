import polib
import requests
from django import forms, http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.template.defaulttags import query_string
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from form_rendering import adapt_rendering
from projects.models import Catalog, Project


ENTRIES_PER_PAGE = 20


@login_required
def projects(request):
    return render(
        request, "projects/projects.html", {"projects": request.user.projects.all()}
    )


@login_required
def project(request, slug):
    project = get_object_or_404(Project.objects.for_user(request.user), slug=slug)
    return render(request, "projects/project.html", {"project": project})


class FilterForm(forms.Form):
    pending = forms.BooleanField(label=_("Pending"), required=False)
    query = forms.CharField(
        label="",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Query")}),
    )
    start = forms.IntegerField(
        label=_("Start"), widget=forms.HiddenInput, required=False
    )


def _help_text(msgid, language_code):
    if settings.DEEPL_AUTH_KEY:
        return format_html(
            '<a href="#" data-suggest="{}" data-language-code="{}"><small>{}</small></a>',
            msgid,
            language_code,
            _("Suggest"),
        )
    return ""


class EntriesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.entries = kwargs.pop("entries")
        self.language_code = kwargs.pop("language_code")
        super().__init__(*args, **kwargs)

        self.entry_rows = []

        for index, entry in enumerate(self.entries):
            self.fields[f"msgid_{index}"] = forms.CharField(
                widget=forms.HiddenInput,
                initial=entry.msgid_with_context,
            )
            self.fields[f"fuzzy_{index}"] = forms.BooleanField(
                label="Fuzzy",
                initial=entry.fuzzy,
                required=False,
            )

            self.entry_rows.append({
                "entry": entry,
                "msgid": self[f"msgid_{index}"],
                "msgstr": [],
                "fuzzy": self[f"fuzzy_{index}"],
            })

            if entry.msgid_plural:
                for count, msgstr in sorted(entry.msgstr_plural.items()):
                    name = f"msgstr_{index}:{count}"
                    self.fields[name] = forms.CharField(
                        label=_("With {count} items").format(count=count),
                        widget=forms.Textarea(attrs={"rows": 3}),
                        initial=msgstr,
                        required=False,
                        help_text=_help_text(entry.msgid_plural, self.language_code),
                    )
                    self.entry_rows[-1]["msgstr"].append(self[name])
            else:
                name = f"msgstr_{index}"
                self.fields[f"msgstr_{index}"] = forms.CharField(
                    label="",
                    widget=forms.Textarea(attrs={"rows": 3}),
                    initial=entry.msgstr,
                    required=False,
                    help_text=_help_text(entry.msgid, self.language_code),
                )
                self.entry_rows[-1]["msgstr"].append(self[name])

    def fix_nls(self, in_, out_):
        # Thanks, django-rosetta!
        """Fixes submitted translations by filtering carriage returns and pairing
        newlines at the begging and end of the translated string with the original
        """
        if len(in_) == 0 or len(out_) == 0:
            return out_

        if "\r" in out_ and "\r" not in in_:
            out_ = out_.replace("\r", "")

        if in_[0] == "\n" and out_[0] != "\n":
            out_ = "\n" + out_
        elif in_[0] != "\n" and out_[0] == "\n":
            out_ = out_.lstrip()
        if len(out_) == 0:
            pass
        elif in_[-1] == "\n" and out_[-1] != "\n":
            out_ = out_ + "\n"
        elif in_[-1] != "\n" and out_[-1] == "\n":
            out_ = out_.rstrip()
        return out_

    def update(self, po, *, user):
        for index in range(ENTRIES_PER_PAGE):
            msgid_with_context = self.cleaned_data.get(f"msgid_{index}")
            msgstr = self.cleaned_data.get(f"msgstr_{index}", "")
            fuzzy = self.cleaned_data.get(f"fuzzy_{index}")

            if not msgid_with_context:
                continue

            for entry in po:
                if entry.msgid_with_context == msgid_with_context:
                    entry.msgstr = self.fix_nls(entry.msgid, msgstr)
                    if entry.msgid_plural:
                        for count in entry.msgstr_plural:
                            entry.msgstr_plural[count] = self.fix_nls(
                                entry.msgid_plural,
                                self.cleaned_data.get(f"msgstr_{index}:{count}", ""),
                            )
                    if fuzzy and not entry.fuzzy:
                        entry.flags.append("fuzzy")
                    if not fuzzy and entry.fuzzy:
                        entry.flags.remove("fuzzy")
                    break

        po.metadata["Last-Translator"] = "{} {} <{}>".format(
            getattr(user, "first_name", "Anonymous"),
            getattr(user, "last_name", "User"),
            getattr(user, "email", "anonymous@user.tld"),
        )
        po.metadata["X-Translated-Using"] = "traduire 0.0.1"
        po.metadata["PO-Revision-Date"] = localtime().strftime("%Y-%m-%d %H:%M%z")


@login_required
def catalog(request, project, language_code, domain):
    catalog = get_object_or_404(
        Catalog.objects.for_user(request.user),
        project__slug=project,
        language_code=language_code,
        domain=domain,
    )

    entries = list(catalog.po)
    total = len(entries)

    filter_form = FilterForm(request.GET)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get("pending"):
            entries = [
                entry
                for entry in entries
                if not entry.translated() and not entry.obsolete
            ]
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
        form.update(catalog.po, user=request.user)
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


class TranslationError(Exception):
    pass


def translate_by_deepl(text, to_language, auth_key):
    if auth_key.lower().endswith(":fx"):
        endpoint = "https://api-free.deepl.com"
    else:
        endpoint = "https://api.deepl.com"

    r = requests.post(
        f"{endpoint}/v2/translate",
        headers={"Authorization": f"DeepL-Auth-Key {auth_key}"},
        data={
            "target_lang": to_language.upper(),
            "text": text,
        },
        timeout=5,
    )
    if r.status_code != 200:
        raise TranslationError(
            f"Deepl response is {r.status_code}. Please check your API key or try again later."
        )
    try:
        return r.json().get("translations")[0].get("text")
    except Exception as exc:
        raise TranslationError(
            "Deepl returned a non-JSON or unexpected response."
        ) from exc


class SuggestForm(forms.Form):
    language_code = forms.CharField()
    msgid = forms.CharField()


def suggest(request):
    if not request.user.is_authenticated:
        return http.HttpResponseForbidden()

    form = SuggestForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            translation = translate_by_deepl(
                data["msgid"], data["language_code"], settings.DEEPL_AUTH_KEY
            )
        except TranslationError as exc:
            return http.JsonResponse({"error": str(exc)})
        return http.JsonResponse({"msgstr": translation})

    return http.HttpResponseBadRequest()


@csrf_exempt
def pofile(request, language_code, domain):
    project = Project.objects.filter(
        token=request.headers.get("x-project-token")
    ).first()
    if not project:
        return http.HttpResponseForbidden()

    if request.method == "GET":
        if catalog := project.catalogs.filter(
            language_code=language_code, domain=domain
        ).first():
            return http.HttpResponse(catalog.pofile, content_type="text/plain")
        return http.HttpResponseNotFound()

    if request.method == "PUT":
        po = polib.pofile(request.body.decode("utf-8"))
        project.catalogs.update_or_create(
            language_code=language_code,
            domain=domain,
            defaults={"pofile": str(po)},
        )
        return http.HttpResponse(status=202)  # Accepted

    return http.HttpResponse(status=405)  # Method Not Allowed
