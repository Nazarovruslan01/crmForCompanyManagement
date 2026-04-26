"""Accounts app views for REST API."""

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.audit import AuditLogMixin
from common.permissions import IsAdminOrManager
from common.throttles import UserReadThrottle, UserWriteThrottle

from .serializers import UserCreateSerializer, UserMeSerializer, UserSerializer

User = get_user_model()


class UserViewSet(AuditLogMixin, viewsets.ModelViewSet[User]):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    filterset_fields = ["role", "is_active", "is_staff"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "date_joined"]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminOrManager()]

    def get_serializer_class(self) -> type[UserSerializer | UserCreateSerializer]:
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserWriteThrottle]

    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class UserMeView(generics.RetrieveUpdateAPIView[User]):
    """Get or update current user profile."""

    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserReadThrottle, UserWriteThrottle]

    def get_object(self) -> User:
        return self.request.user
