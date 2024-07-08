from authlib.base_user import BaseUser
from authlib.roles import RoleField
from django.contrib.auth import signals
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from projects.models import Project


class User(BaseUser):
    full_name = models.CharField(_("full name"), max_length=200)
    role = RoleField()
    token = models.CharField(_("token"), max_length=100, editable=False, unique=True)

    class Meta(BaseUser.Meta):
        ordering = ["full_name", "email"]

    def __str__(self):
        return self.full_name or self.email

    get_full_name = __str__
    get_short_name = __str__

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.token:
            self.cycle_token()

    save.alters_data = True

    def cycle_token(self):
        self.token = f"{get_random_string(60)}-{self.pk}"
        self.save()

    cycle_token.alters_data = True


def add_user_to_projects(sender, user, **kwargs):
    domain = user.email.rsplit("@")[-1]
    for project in Project.objects.filter(_email_domains__icontains=domain):
        if domain in project.email_domains:
            project.users.add(user)


signals.user_logged_in.connect(add_user_to_projects)
