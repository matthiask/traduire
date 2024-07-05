from django.apps import AppConfig
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    name = "accounts"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = capfirst(_("Authentication"))
