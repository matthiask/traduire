from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from projects import models


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    filter_horizontal = ["users"]
    list_display = [
        "name",
        "explicit_users",
        "email_domains",
        "created_at",
        "updated_at",
    ]
    list_filter = ["users"]
    prepopulated_fields = {"slug": ["name"]}

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("users")

    @admin.display(description=_("explicit users"))
    def explicit_users(self, obj):
        return ", ".join(str(user) for user in obj.users.all())


@admin.register(models.Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["project", "language_code", "domain", "created_at", "updated_at"]
    list_filter = ["project"]
    readonly_fields = ["pofile"]
    ordering = ["project", *models.Catalog._meta.ordering]
