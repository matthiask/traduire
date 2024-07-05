from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as StockUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(StockUserAdmin):
    fieldsets = None
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "email",
        "full_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "role",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "role", "groups")
    ordering = User._meta.ordering
    search_fields = ("full_name", "email")
    filter_horizontal = ("groups", "user_permissions")
    radio_fields = {"role": admin.VERTICAL}
