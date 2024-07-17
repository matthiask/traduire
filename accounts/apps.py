from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import signals
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _


def add_user_to_projects(sender, user, **kwargs):
    project_model = user.projects.model
    domain = user.email.rsplit("@")[-1]
    if domain in settings.STAFF_EMAIL_DOMAINS:
        user.is_staff = True
        user.role = "manager"
        user.save()
    else:
        for project in project_model.objects.filter(
            _email_domains__icontains=domain
        ).exclude(users=user):
            if domain in project.email_domains:
                project.users.add(user)


class AccountsConfig(AppConfig):
    name = "accounts"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = capfirst(_("Authentication"))

    def ready(self):
        signals.user_logged_in.connect(add_user_to_projects)
