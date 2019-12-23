from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'is_staff', 'is_active', 'external_id']


admin.site.register(User, UserAdmin)
