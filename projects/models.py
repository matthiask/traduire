from functools import cached_property

import polib
from django.conf import global_settings, settings
from django.core import validators
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

from accounts.models import User


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


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True

    @property
    def pretty_timesince(self):
        return timesince(self.updated_at, depth=1)


class ProjectQuerySet(models.QuerySet):
    def for_user(self, user):
        return self if user.is_staff else self.filter(users=user)


class Project(TimestampedModel):
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
    _email_domains = models.TextField(
        _("email domains"),
        blank=True,
        help_text=_(
            "User accounts on these domains will automatically get access to this project. One domain per line."
        ),
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

    @property
    def email_domains(self):
        return [v.strip() for v in self._email_domains.strip().splitlines()]

    def clean(self):
        validator = validators.DomainNameValidator(
            message=_("Some of the lines are not valid domain names.")
        )
        for domain in self.email_domains:
            validator(domain)

    def get_api_url(self):
        return f"/api/pofile/{self.slug}/"

    @cached_property
    def all_users(self):
        return User.objects.filter(
            Q(is_active=True) & (Q(is_staff=True) | Q(projects=self))
        )

    def toml(self, *, request):
        return f"""\
[[project]]
name = "{self.name}"
token = "{request.user.token}"
url = "{request.build_absolute_uri(self.get_api_url())}"
path = "" # Add the absolute path of your local project!
"""


class CatalogQuerySet(models.QuerySet):
    def for_user(self, user):
        return self if user.is_staff else self.filter(project__users=user)


class Catalog(TimestampedModel):
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
