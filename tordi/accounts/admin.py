from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import TordiUser


@admin.register(TordiUser)
class TordiUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Tordi preferences", {"fields": ("avatar", "theme_preference")}),
    )
    list_display = ("username", "email", "is_staff", "theme_preference")
