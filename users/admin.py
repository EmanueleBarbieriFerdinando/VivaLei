from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "telefono", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    list_filter = ["is_active", "is_staff", "is_superuser"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informazioni personali", {"fields": ("first_name", "last_name", "telefono")}),
        ("Permessi", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Date importanti", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "telefono", "password1", "password2", "is_active", "is_staff"),
            },
        ),
    )