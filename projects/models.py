from django.conf import global_settings, settings
from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _


class ChoicesCharField(models.CharField):
    """
    ``models.CharField`` with choices, which makes the migration framework
    always ignore changes to ``choices``, ever.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", [("", "")])  # Non-empty choices for get_*_display
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, _path, args, kwargs = super().deconstruct()
        kwargs["choices"] = [("", "")]
        return name, "django.db.models.CharField", args, kwargs


class Project(models.Model):
    name = models.CharField(_("name"), max_length=100)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="projects",
        verbose_name=_("users"),
    )
    token = models.CharField(_("token"), max_length=100, editable=False)

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.token:
            self.cycle_token(save=False)
        super().save(*args, **kwargs)

    save.alters_data = True

    def get_absolute_url(self):
        return reverse("projects:project", kwargs={"pk": self.pk})

    def cycle_token(self, *, save=True):
        self.token = f"{get_random_string(60)}-{self.pk}"
        if save:
            self.save()


class Catalog(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="catalogs",
        verbose_name=_("project"),
    )
    language_code = ChoicesCharField(_("language"), choices=global_settings.LANGUAGES)
    domain = models.CharField(_("domain"), max_length=20, default="django")
    pofile = models.TextField("pofile")

    class Meta:
        verbose_name = _("catalog")
        verbose_name_plural = _("catalogs")

    def __str__(self):
        return self.language_code

    def get_absolute_url(self):
        return reverse(
            "projects:catalog", kwargs={"project": self.project_id, "pk": self.pk}
        )
