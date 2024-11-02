from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import (ConfirmEmailView, ContactManagementView, DeleteView,
                    LoginView, LogoutView, ProfileDetailView,
                    ProfileUpdateView, RegisterView, VerifyTokenView)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify-token/", VerifyTokenView.as_view(), name="verify_token"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "confirm-email/<uidb64>/<token>/",
        ConfirmEmailView.as_view(),
        name="confirm-email",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("delete-user/", DeleteView.as_view(), name="delete-user"),
    path("update-user/", ProfileUpdateView.as_view(), name="update-user"),
    path(
        "contacts/", ContactManagementView.as_view(), name="contact_management"
    ),
    path(
        "contacts/<int:pk>/",
        ContactManagementView.as_view(),
        name="contact_management_detail",
    ),
    path("profile/", ProfileDetailView.as_view(), name="profile-detail"),
    path(
        "profile/<int:pk>/",
        ProfileDetailView.as_view(),
        name="profile-detail-id",
    ),
]
