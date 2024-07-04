from django.contrib import admin

from projects import models


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    filter_horizontal = ["users"]
    list_display = ["name"]
    list_filter = ["users"]
    prepopulated_fields = {"slug": ["name"]}
    ordering = ["name"]


@admin.register(models.Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["project", "language_code", "domain"]
    list_filter = ["project"]
