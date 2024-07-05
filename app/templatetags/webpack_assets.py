from functools import cache
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import mark_safe


register = template.Library()


def webpack_assets(entry):  # pragma: no cover
    base = Path.cwd()
    if settings.DEBUG:
        base = base / "tmp" / "dev"
    assets = (base / "static" / f"{entry}.html").read_text()
    for part in ("<head>", "</head>", "<title></title>"):
        assets = assets.replace(part, "")
    return mark_safe(assets)


if not settings.DEBUG:  # pragma: no branch
    webpack_assets = cache(webpack_assets)
register.simple_tag(webpack_assets)
