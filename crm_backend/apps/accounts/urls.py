"""Accounts app URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LogoutView, UserMeView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
]
