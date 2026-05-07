import hashlib

# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportPossiblyUnboundVariable=false, reportIncompatibleMethodOverride=false
import logging
import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, cast

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.throttles import LoginRateThrottle, MFAVerifyThrottle, PasswordResetRateThrottle
from common.validators import validate_password_strength
from core.tasks import send_email_async

from .serializers import UserSerializer

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apps.accounts.models import User as UserType

User = get_user_model()


class LoginView(APIView):
    """JWT login endpoint with MFA support for admin/manager accounts."""

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
            200: OpenApiResponse(
                description="Login successful — JWT tokens and user data returned",
                examples=[
                    OpenApiExample(
                        "Successful login",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "user": {
                                "id": 1,
                                "username": "admin",
                                "email": "admin@example.com",
                                "role": "admin",
                            },
                        },
                    ),
                ],
            ),
            202: OpenApiResponse(
                description="MFA required — temporary token returned for TOTP verification",
                examples=[
                    OpenApiExample(
                        "MFA required",
                        value={"mfa_required": True, "temp_token": "eyJ...mfa..."},
                    ),
                ],
            ),
            400: OpenApiResponse(description="Username and password are required"),
            401: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            # Always return the same error regardless of whether the username
            # exists or the account is disabled — prevents account enumeration.
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if MFA is required for admin/manager accounts
        try:
            mfa_required = (
                user.totp_device.is_active  # type: ignore[attr-defined]
                and user.role in (User.Role.ADMIN, User.Role.MANAGER)  # type: ignore[attr-defined]
            )
        except User.totp_device.RelatedObjectDoesNotExist:  # type: ignore[attr-defined]
            mfa_required = False

        if mfa_required:
            # Issue a short-lived temporary token for MFA verification
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            access.payload["type"] = "mfa"
            access.set_exp(lifetime=timedelta(minutes=5))

            return Response(
                {
                    "mfa_required": True,
                    "temp_token": str(access),
                },
                status=status.HTTP_202_ACCEPTED,
            )

        refresh = RefreshToken.for_user(user)

        response = Response(
            {
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(timedelta(days=7).total_seconds()),
        )
        return response


class LogoutView(APIView):
    """Logout endpoint — blacklist refresh token and clear httpOnly cookie."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: {"description": "Successfully logged out"},
            400: {"description": "Invalid token"},
        },
    )
    def post(self, request: Request) -> Response:
        # Blacklist refresh token from httpOnly cookie.
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)  # type: ignore[arg-type]
                token.blacklist()
            except Exception:
                logger.warning("Failed to blacklist refresh token during logout", exc_info=True)

        response = Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response


class PasswordResetRequestView(APIView):
    """Request password reset email.

    Generates a single-purpose cryptographically random token, stores its
    SHA256 hash in the database, and emails the raw token to the user.
    Old unused tokens for the user are cleaned up to prevent accumulation.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    # Token lifetime in minutes
    TOKEN_LIFETIME_MINUTES = 60

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
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist (security)
            return Response({"detail": "If the email exists, a reset link has been sent"}, status=status.HTTP_200_OK)

        from apps.accounts.models import PasswordResetToken

        # Clean up old unused tokens for this user before creating a new one
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).delete()

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        PasswordResetToken.objects.create(user=user, token_hash=token_hash)

        frontend_url = getattr(settings, "FRONTEND_URL", "")
        if frontend_url:
            reset_link = f"{frontend_url.rstrip('/')}/reset-password?token={raw_token}"
        else:
            reset_link = request.build_absolute_uri(f"/reset-password?token={raw_token}")

        send_email_async.delay(
            subject="Şifre Sıfırlama - CRM",
            message=(
                f"Merhaba {user.get_full_name() or user.username},\n\n"
                f"Şifre sıfırlama talebinde bulundunuz. "
                f"Aşağıdaki bağlantıyı kullanarak şifrenizi sıfırlayabilirsiniz:\n\n"
                f"{reset_link}\n\n"
                f"Bu bağlantı {self.TOKEN_LIFETIME_MINUTES} dakika geçerlidir. "
                f"Eğer bu talebi siz yapmadıysanız, bu e-postayı dikkate almayın."
            ),
            recipient_list=[email],
        )

        return Response({"detail": "If the email exists, a reset link has been sent"}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Confirm password reset with single-purpose token.

    Expects the raw token in the URL path. The token is hashed and looked up
    in the PasswordResetToken table. After a successful reset the token is
    marked as used so it cannot be reused.
    """

    permission_classes = [permissions.AllowAny]

    # Same lifetime as the request view
    TOKEN_LIFETIME_MINUTES = 60

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
            400: {"description": "Invalid, expired, or already used token"},
        },
    )
    def post(self, request: Request, token: str) -> Response:
        new_password = request.data.get("new_password")

        if not new_password:
            return Response({"detail": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.accounts.models import PasswordResetToken

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        try:
            reset_token = PasswordResetToken.objects.get(token_hash=token_hash, used_at__isnull=True)
        except PasswordResetToken.DoesNotExist:
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        # Check expiry
        expiry = reset_token.created_at + timedelta(minutes=self.TOKEN_LIFETIME_MINUTES)
        if timezone.now() > expiry:
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        user = reset_token.user
        validate_password_strength(new_password)
        user.set_password(new_password)
        user.save()

        # Mark token as used immediately to prevent replay attacks
        reset_token.used_at = timezone.now()
        reset_token.save(update_fields=["used_at"])

        return Response({"detail": "Password has been reset successfully"}, status=status.HTTP_200_OK)


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
            return Response({"detail": "Old and new password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"detail": "Invalid old password"}, status=status.HTTP_400_BAD_REQUEST)

        validate_password_strength(new_password)
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password has been changed successfully"}, status=status.HTTP_200_OK)


class MFASetupView(APIView):
    """Setup TOTP MFA for admin/manager accounts."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "secret": {"type": "string"},
                    "qr_uri": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            403: {"description": "MFA is only available for admin and manager accounts"},
        },
    )
    def post(self, request: Request) -> Response:
        user = cast("UserType", request.user)
        if user.role not in (User.Role.ADMIN, User.Role.MANAGER):  # type: ignore[attr-defined]
            return Response(
                {"detail": "MFA is only available for admin and manager accounts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        import pyotp

        from apps.accounts.models import TOTPDevice

        device, _ = TOTPDevice.objects.get_or_create(
            user=user,
            defaults={"secret_key": pyotp.random_base32(), "confirmed": False},
        )
        if not device.confirmed:
            device.secret_key = pyotp.random_base32()
            device.confirmed = False
            device.save()

        totp = pyotp.TOTP(device.secret_key)
        qr_uri = totp.provisioning_uri(
            name=user.email or user.username,  # type: ignore[attr-defined]
            issuer_name="CRM",
        )

        return Response(
            {
                "secret": device.secret_key,
                "qr_uri": qr_uri,
                "message": "Scan the QR code with your authenticator app and verify with a code.",
            }
        )


class MFAVerifyView(APIView):
    """Verify TOTP code and issue full JWT tokens."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [MFAVerifyThrottle]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "temp_token": {"type": "string"},
                "totp_code": {"type": "string"},
            },
            "required": ["temp_token", "totp_code"],
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
            400: {"description": "temp_token and totp_code are required"},
            401: {"description": "Invalid or expired token"},
            403: {"description": "Invalid TOTP code"},
        },
    )
    def post(self, request: Request) -> Response:
        temp_token = request.data.get("temp_token")
        totp_code = request.data.get("totp_code")

        if not temp_token or not totp_code:
            return Response(
                {"detail": "temp_token and totp_code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = AccessToken(temp_token)
            if token.payload.get("type") != "mfa":
                return Response({"detail": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED)
            user_id = token.payload.get("user_id")
            if not user_id:
                return Response({"detail": "Invalid token: missing user_id"}, status=status.HTTP_401_UNAUTHORIZED)
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning("MFA verify: user_id %s not found", token.payload.get("user_id"))
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as exc:
            # TokenError, InvalidToken, expired tokens — all get 401
            logger.info("MFA verify token validation failed: %s", type(exc).__name__)
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

        import pyotp

        try:
            device = user.totp_device  # type: ignore[attr-defined]
        except User.totp_device.RelatedObjectDoesNotExist:  # type: ignore[attr-defined]
            return Response({"detail": "MFA not configured"}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(device.secret_key)
        if not totp.verify(totp_code, valid_window=1):
            return Response({"detail": "Invalid TOTP code"}, status=status.HTTP_403_FORBIDDEN)

        # Mark device as confirmed on first successful verification
        if not device.confirmed:
            device.confirmed = True
            device.save()

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=int(timedelta(days=7).total_seconds()),
        )
        return response


class CookieTokenRefreshView(APIView):
    """Refresh access token using the httpOnly refresh_token cookie."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                },
            },
            401: {"description": "Refresh token cookie missing or invalid"},
        },
    )
    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token cookie missing"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        response = Response({"access": data["access"]})

        # If rotation is enabled, update the cookie with the new refresh token.
        if "refresh" in data:
            response.set_cookie(
                "refresh_token",
                data["refresh"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=int(timedelta(days=7).total_seconds()),
            )

        return response


class MFADisableView(APIView):
    """Disable MFA for the current user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "password": {"type": "string"},
            },
            "required": ["password"],
        },
        responses={
            200: {"description": "MFA disabled successfully"},
            400: {"description": "Password is required"},
            403: {"description": "Invalid password or MFA not enabled"},
        },
    )
    def post(self, request: Request) -> Response:
        user = cast("UserType", request.user)
        password = request.data.get("password")

        if not password:
            return Response({"detail": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"detail": "Invalid password"}, status=status.HTTP_403_FORBIDDEN)

        try:
            user.totp_device.delete()  # type: ignore[attr-defined]
        except User.totp_device.RelatedObjectDoesNotExist:  # type: ignore[attr-defined]
            return Response({"detail": "MFA is not enabled"}, status=status.HTTP_403_FORBIDDEN)

        return Response({"detail": "MFA disabled successfully"}, status=status.HTTP_200_OK)


class MFAStatusView(APIView):
    """Check MFA status for the current user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "mfa_enabled": {"type": "boolean"},
                    "mfa_required": {"type": "boolean"},
                },
            },
        },
    )
    def get(self, request: Request) -> Response:
        user = cast("UserType", request.user)
        mfa_enabled = hasattr(user, "totp_device") and user.totp_device.is_active  # type: ignore[attr-defined]
        mfa_required = user.role in (User.Role.ADMIN, User.Role.MANAGER)  # type: ignore[attr-defined]

        return Response(
            {
                "mfa_enabled": mfa_enabled,
                "mfa_required": mfa_required,
            }
        )
