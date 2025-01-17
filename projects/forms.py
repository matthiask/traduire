import copy

from django import forms
from django.conf import settings
from django.contrib import messages
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _, ngettext

from projects import translators


ENTRIES_PER_PAGE = 20


class FilterForm(forms.Form):
    pending = forms.BooleanField(label=_("Pending"), required=False)
    query = forms.CharField(
        label="",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Query")}),
    )
    start = forms.IntegerField(widget=forms.HiddenInput, required=False)


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
                required=False,
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

    def update(self, catalog, *, request):
        updates = 0

        for index in range(ENTRIES_PER_PAGE):
            msgid_with_context = self.cleaned_data.get(f"msgid_{index}")
            msgstr = self.cleaned_data.get(f"msgstr_{index}", "")
            fuzzy = self.cleaned_data.get(f"fuzzy_{index}")

            if not msgid_with_context:
                continue

            # Better be safe than sorry -- do not modify the entries in
            # self.entries, find the entry in the current version of the pofile
            # instead.
            for entry in catalog.po:
                if entry.msgid_with_context == msgid_with_context:
                    old = copy.deepcopy(entry)
                    entry.msgstr = translators.fix_nls(entry.msgid, msgstr)
                    if entry.msgid_plural:
                        for count in entry.msgstr_plural:
                            entry.msgstr_plural[count] = translators.fix_nls(
                                entry.msgid_plural,
                                self.cleaned_data.get(f"msgstr_{index}:{count}", ""),
                            )
                    if fuzzy and not entry.fuzzy:
                        entry.fuzzy = True
                        updates += 1
                    elif not fuzzy and entry.fuzzy:
                        entry.fuzzy = False
                        updates += 1
                    elif old != entry:
                        entry.fuzzy = fuzzy
                        updates += 1
                    break

        if updates:
            catalog.po.metadata["Last-Translator"] = "{} {} <{}>".format(
                getattr(request.user, "first_name", "Anonymous"),
                getattr(request.user, "last_name", "User"),
                getattr(request.user, "email", "anonymous@user.tld"),
            )
            catalog.po.metadata["X-Translated-Using"] = "traduire 0.0.1"
            catalog.po.metadata["PO-Revision-Date"] = localtime().strftime(
                "%Y-%m-%d %H:%M%z"
            )

            messages.success(
                request,
                ngettext(
                    "Successfully updated {count} message.",
                    "Successfully updated {count} messages.",
                    updates,
                ).format(count=updates),
            )

            catalog.pofile = str(catalog.po)
            catalog.save()

        else:
            messages.info(request, _("No changes detected."))


class SuggestForm(forms.Form):
    language_code = forms.CharField()
    msgid = forms.CharField()
