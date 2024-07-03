import os

from django.db import models
from django.utils.translation import gettext_lazy as _
from feincms3 import plugins
from feincms3.utils import upload_to


class Image(plugins.image.Image):
    copyright = models.CharField(_("copyright"), max_length=1000)

    class Meta(plugins.image.Image.Meta):
        abstract = True


class Download(models.Model):
    download = models.FileField(_("download"), upload_to=upload_to)
    caption = models.CharField(_("caption"), blank=True, max_length=1000)

    class Meta:
        abstract = True
        verbose_name = _("download")
        verbose_name_plural = _("downloads")

    def __str__(self):
        return self.caption or os.path.basename(self.download.name)
