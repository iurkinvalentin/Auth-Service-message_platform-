from django.contrib import admin

from .models import Group, GroupInvitation, GroupMembership


class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "updated_at")
    search_fields = ("name", "owner__username")
    list_filter = ("created_at",)
    ordering = ("name",)

    def get_members_count(self, obj):
        return obj.groupmembership_set.count()

    get_members_count.short_description = "Members Count"


class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "profile", "role", "date_joined")
    search_fields = ("group__name", "profile__user__username")
    list_filter = ("role", "date_joined")
    ordering = ("group", "profile")


class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "invited_by",
        "invited_to",
        "created_at",
        "is_accepted",
    )
    search_fields = (
        "group__name",
        "invited_by__user__username",
        "invited_to__user__username",
    )
    list_filter = ("is_accepted", "created_at")
    ordering = ("group", "created_at")


admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(GroupInvitation, GroupInvitationAdmin)
