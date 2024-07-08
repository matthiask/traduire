from functools import cached_property

import polib
from django.conf import global_settings, settings
from django.db import models
from django.urls import reverse
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


class ProjectQuerySet(models.QuerySet):
    def for_user(self, user):
        return self if user.is_staff else self.filter(users=user)


class Project(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(_("slug"), unique=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="projects",
        verbose_name=_("users"),
        blank=True,  # Only internal is fine.
        limit_choices_to={"is_staff": False},
    )

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("projects:project", kwargs={"slug": self.slug})

    def get_api_url(self):
        return f"/api/pofile/{self.slug}/"


class CatalogQuerySet(models.QuerySet):
    def for_user(self, user):
        return self if user.is_staff else self.filter(project__users=user)


class Catalog(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="catalogs",
        verbose_name=_("project"),
    )
    language_code = ChoicesCharField(
        _("language"), max_length=10, choices=global_settings.LANGUAGES
    )
    domain = models.CharField(_("domain"), max_length=20, default="django")
    pofile = models.TextField("pofile")

    objects = CatalogQuerySet.as_manager()

    class Meta:
        ordering = ["language_code", "domain"]
        unique_together = [("project", "language_code", "domain")]
        verbose_name = _("catalog")
        verbose_name_plural = _("catalogs")

    def __str__(self):
        try:
            percent_translated = f"{self.po.percent_translated()}%"
        except Exception:
            percent_translated = "Invalid"
        return (
            f"{self.get_language_code_display()}, {self.domain} ({percent_translated})"
        )

    def get_absolute_url(self):
        return reverse(
            "projects:catalog",
            kwargs={
                "project": self.project.slug,
                "language_code": self.language_code,
                "domain": self.domain,
            },
        )

    @cached_property
    def po(self):
        return polib.pofile(self.pofile, wrapwidth=0)
