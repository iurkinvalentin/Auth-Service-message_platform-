from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Profile, Connections


class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'birthday', 'status_message', 'is_online', 'last_seen')
    search_fields = ('user__username', 'user__email', 'status_message')
    list_filter = ('is_online',)


class ConnectionsAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'is_confirmed', 'created')
    search_fields = ('from_user__username', 'to_user__username')
    list_filter = ('is_confirmed', 'created')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Connections, ConnectionsAdmin)