from django.db import models

from accounts.models import CustomUser, Profile


class Group(models.Model):
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("member", "Member"),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default="member"
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "profile")

    def is_owner(self):
        return self.role == "owner"


class GroupInvitation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="invitations_sent"
    )
    invited_to = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="invitations_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"Invitation to {self.group.name} by "
            f"{self.invited_by.user.username} to "
            f"{self.invited_to.user.username}"
        )
