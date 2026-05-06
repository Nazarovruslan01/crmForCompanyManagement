"""Accounts app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth_views import (
    CookieTokenRefreshView,
    LoginView,
    LogoutView,
    MFADisableView,
    MFASetupView,
    MFAStatusView,
    MFAVerifyView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)
from .views import UserMeView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("me/", UserMeView.as_view(), name="user-me"),
    # Auth endpoints
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token-refresh"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/reset/<str:token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    # MFA endpoints
    path("mfa/setup/", MFASetupView.as_view(), name="mfa-setup"),
    path("mfa/verify/", MFAVerifyView.as_view(), name="mfa-verify"),
    path("mfa/disable/", MFADisableView.as_view(), name="mfa-disable"),
    path("mfa/status/", MFAStatusView.as_view(), name="mfa-status"),
]
