from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _


def _on_project_post_save(sender, instance, created, **kwargs):
    if created:
        event_model = instance.events.model
        event_model.objects.create(
            project=instance,
            action=event_model.Action.PROJECT_CREATED,
        )


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "projects"
    verbose_name = capfirst(_("projects"))

    def ready(self):
        post_save.connect(_on_project_post_save, sender=self.get_model("project"))
