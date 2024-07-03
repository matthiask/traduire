import polib
from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.defaulttags import query_string
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from projects.models import Catalog


ENTRIES_PER_PAGE = 20


@login_required
def projects(request):
    return render(
        request, "projects/projects.html", {"projects": request.user.projects.all()}
    )


@login_required
def project(request, pk):
    project = get_object_or_404(request.user.projects.all(), pk=pk)
    return render(request, "projects/project.html", {"project": project})


class FilterForm(forms.Form):
    flags = forms.ChoiceField(
        label=_("flags"),
        choices=[
            ("", _("All")),
            ("fuzzy", _("Fuzzy")),
            ("untranslated", _("Untranslated")),
        ],
        required=False,
    )
    start = forms.IntegerField(
        label=_("start"), widget=forms.HiddenInput, required=False
    )


class EntriesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.entries = kwargs.pop("entries")
        super().__init__(*args, **kwargs)

        for index, entry in enumerate(self.entries):
            self.fields[f"msgid_{index}"] = forms.CharField(
                widget=forms.HiddenInput,
                initial=entry.msgid_with_context,
            )
            self.fields[f"msgstr_{index}"] = forms.CharField(
                # label=format_html(
                #     "<small>{msgctxt}</small><br>{msgid}",
                #     msgctxt=entry.msgctxt or "",
                #     msgid=entry.msgid,
                # ),
                label=format_html("<pre>{}</pre>", entry.__unicode__(wrapwidth=0)),
                widget=forms.Textarea(attrs={"rows": 2}),
                initial=entry.msgstr,
                required=False,
            )
            self.fields[f"fuzzy_{index}"] = forms.BooleanField(
                label="Fuzzy",
                initial=entry.fuzzy,
                required=False,
            )

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
            msgstr = self.cleaned_data.get(f"msgstr_{index}")
            fuzzy = self.cleaned_data.get(f"fuzzy_{index}")

            if not msgid_with_context:
                continue

            for entry in po:
                if entry.msgid_with_context == msgid_with_context:
                    entry.msgstr = self.fix_nls(entry.msgid, msgstr)
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
def catalog(request, project, pk):
    catalog = get_object_or_404(
        Catalog.objects.filter(project__users=request.user),
        project=project,
        pk=pk,
    )

    po = polib.pofile(catalog.pofile, wrapwidth=0)
    entries = list(po)

    filter_form = FilterForm(request.GET)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if data.get("flags") == "fuzzy":
            entries = [entry for entry in entries if entry.fuzzy]
        elif data.get("flags") == "untranslated":
            entries = [
                entry
                for entry in entries
                if not entry.translated() and not entry.fuzzy and not entry.obsolete
            ]
        if start := data.get("start"):
            entries = entries[start:]
    else:
        return HttpResponseRedirect(".")

    data = [request.POST] if request.method == "POST" else []
    form = EntriesForm(*data, entries=entries[:ENTRIES_PER_PAGE])

    if form.is_valid():
        form.update(po, user=request.user)
        catalog.pofile = str(po)
        catalog.save()

        return HttpResponseRedirect(
            query_string(
                None,
                request.GET,
                start=ENTRIES_PER_PAGE + (filter_form.cleaned_data.get("start") or 0),
            )
        )

    return render(
        request,
        "projects/catalog.html",
        {
            "catalog": catalog,
            "project": catalog.project,
            "po": po,
            "form": form,
            "entries": entries,
        },
    )
