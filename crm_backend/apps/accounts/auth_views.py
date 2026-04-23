"""Auth views for login, logout, password reset."""
from django.contrib.auth import authenticate, get_user_model
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.throttles import LoginRateThrottle, PasswordResetRateThrottle

from .serializers import UserSerializer

User = get_user_model()


class LoginView(APIView):
    """JWT login endpoint."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request: Request) -> Response:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class LogoutView(APIView):
    """Logout endpoint - blacklist refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {'detail': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'detail': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(APIView):
    """Request password reset email."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: Request) -> Response:
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist (security)
            return Response(
                {'detail': 'If the email exists, a reset link has been sent'},
                status=status.HTTP_200_OK
            )

        refresh = RefreshToken.for_user(user)
        reset_token = str(refresh.access_token)

        # In production, send this via email service (Resend)
        # reset_link = f"{request.build_absolute_uri('/api/v1/auth/password-reset/')}{reset_token}/"
        # send_mail(
        #     subject='Password Reset - CRM',
        #     message=f'Click to reset: {reset_link}',
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[email],
        # )
        _ = reset_token  # Used when email integration is enabled

        return Response(
            {'detail': 'If the email exists, a reset link has been sent'},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token."""
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, token: str) -> Response:
        new_password = request.data.get('new_password')

        if not new_password:
            return Response(
                {'error': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            access_token = AccessToken(token)  # type: ignore[arg-type]
            user_id = access_token.payload.get('user_id')
            if not user_id:
                raise ValueError("No user_id in token")

            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            return Response(
                {'detail': 'Password has been reset successfully'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordChangeView(APIView):
    """Change password for authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': 'Old and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(old_password):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {'detail': 'Password has been changed successfully'},
            status=status.HTTP_200_OK
        )
