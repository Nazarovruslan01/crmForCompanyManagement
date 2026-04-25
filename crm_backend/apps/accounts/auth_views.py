from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.throttles import LoginRateThrottle, PasswordResetRateThrottle
from core.tasks import send_email_async

from .serializers import UserSerializer

User = get_user_model()


class LoginView(APIView):
    """JWT login endpoint."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                    "user": {"$ref": "#/components/schemas/User"},
                },
            },
            400: {"description": "Username and password are required"},
            401: {"description": "Invalid credentials"},
            403: {"description": "Account is disabled"},
        },
    )
    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            # authenticate() returns None for inactive users; check explicitly
            try:
                potential = User.objects.get(username=username)
                if not potential.is_active and potential.check_password(password):
                    return Response({"error": "Account is disabled"}, status=status.HTTP_403_FORBIDDEN)
            except User.DoesNotExist:
                pass
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class LogoutView(APIView):
    """Logout endpoint - blacklist refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string"},
            },
        },
        responses={
            200: {"description": "Successfully logged out"},
            400: {"description": "Invalid token"},
        },
    )
    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Request password reset email."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
            },
            "required": ["email"],
        },
        responses={
            200: {"description": "If the email exists, a reset link has been sent"},
            400: {"description": "Email is required"},
        },
    )
    def post(self, request: Request) -> Response:
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist (security)
            return Response({"detail": "If the email exists, a reset link has been sent"}, status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        reset_token = str(refresh.access_token)

        frontend_url = getattr(settings, "FRONTEND_URL", "")
        if frontend_url:
            reset_link = f"{frontend_url.rstrip('/')}/reset-password?token={reset_token}"
        else:
            reset_link = request.build_absolute_uri(f"/reset-password?token={reset_token}")

        send_email_async.delay(
            subject="Şifre Sıfırlama - CRM",
            message=(
                f"Merhaba {user.get_full_name() or user.username},\n\n"
                f"Şifre sıfırlama talebinde bulundunuz. "
                f"Aşağıdaki bağlantıyı kullanarak şifrenizi sıfırlayabilirsiniz:\n\n"
                f"{reset_link}\n\n"
                f"Bu bağlantı 60 dakika geçerlidir. "
                f"Eğer bu talebi siz yapmadıysanız, bu e-postayı dikkate almayın."
            ),
            recipient_list=[email],
        )

        return Response({"detail": "If the email exists, a reset link has been sent"}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "new_password": {"type": "string"},
            },
            "required": ["new_password"],
        },
        responses={
            200: {"description": "Password has been reset successfully"},
            400: {"description": "Invalid or expired token"},
        },
    )
    def post(self, request: Request, token: str) -> Response:
        new_password = request.data.get("new_password")

        if not new_password:
            return Response({"error": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = AccessToken(token)  # type: ignore[arg-type]
            user_id = access_token.payload.get("user_id")
            if not user_id:
                raise ValueError("No user_id in token")

            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            return Response({"detail": "Password has been reset successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """Change password for authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "old_password": {"type": "string"},
                "new_password": {"type": "string"},
            },
            "required": ["old_password", "new_password"],
        },
        responses={
            200: {"description": "Password has been changed successfully"},
            400: {"description": "Old and new password are required or invalid old password"},
        },
    )
    def post(self, request: Request) -> Response:
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"error": "Old and new password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"error": "Invalid old password"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password has been changed successfully"}, status=status.HTTP_200_OK)
