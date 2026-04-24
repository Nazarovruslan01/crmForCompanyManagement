"""Tickets app URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PresignedUploadView,
    TicketAttachmentViewSet,
    TicketCommentViewSet,
    TicketViewSet,
)

router = DefaultRouter()
router.register(r"tickets", TicketViewSet)
router.register(r"comments", TicketCommentViewSet)
router.register(r"attachments", TicketAttachmentViewSet)

urlpatterns = [
    path("upload/presigned/", PresignedUploadView.as_view(), name="presigned-upload"),
    path("", include(router.urls)),
]
