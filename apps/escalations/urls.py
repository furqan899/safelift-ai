from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EscalationViewSet

router = DefaultRouter()
router.register(r"escalations", EscalationViewSet, basename="escalation")

urlpatterns = [
    path("", include(router.urls)),
]


