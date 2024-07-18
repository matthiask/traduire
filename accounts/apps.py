from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import signals
from django.db.models.signals import post_save
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _


def _on_user_logged_in(sender, user, **kwargs):
    event_model = user.events.model
    event_model.objects.create(
        user=user,
        action=event_model.Action.USER_LOGGED_IN,
    )

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
                event_model.objects.create(
                    user=user,
                    action=event_model.Action.PROJECT_ACCESS_GRANTED,
                    project=project,
                )


def _on_user_post_save(sender, instance, created, **kwargs):
    if created:
        event_model = instance.events.model
        event_model.objects.create(
            user=instance,
            action=event_model.Action.USER_CREATED,
        )


class AccountsConfig(AppConfig):
    name = "accounts"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = capfirst(_("Authentication"))

    def ready(self):
        signals.user_logged_in.connect(_on_user_logged_in)
        post_save.connect(_on_user_post_save, sender=self.get_model("user"))
