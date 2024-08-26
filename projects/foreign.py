from collections import defaultdict
from itertools import chain


def msg_key(entry):
    return (entry.msgid, entry.msgid_plural, entry.msgctxt)


def merge_catalogs(project):
    """
    Return a nested dictionary of the form:

    ``messages[msg_key][language, domain] = entry``
    """

    messages = defaultdict(dict)

    for catalog in project.catalogs.all():
        for entry in catalog.po:
            messages[msg_key(entry)][catalog.language_code, catalog.domain] = entry

    return messages


def messages_as_table(project):
    merged = merge_catalogs(project)
    language_domain_combinations = sorted(
        set(chain.from_iterable(thing.keys() for thing in merged.values()))
    )

    header = [
        "msgctxt",
        "msgid",
        "msgid_plural",
        "comment",
        "tcomment",
        "flags",
        *(
            f"{language_code}:{domain}"
            for language_code, domain in language_domain_combinations
        ),
    ]
    data = []

    for entries in merged.values():
        any_entry = next(iter(entries.values()))

        row = [
            any_entry.msgctxt,
            any_entry.msgid,
            any_entry.msgid_plural,
            any_entry.comment,
            any_entry.tcomment,
            ", ".join(any_entry.flags),
        ]

        for language_code_domain in language_domain_combinations:
            if entry := entries.get(language_code_domain):
                row.append(entry.msgstr)
            else:
                row.append("")

        data.append(row)

    return [header, *data]
