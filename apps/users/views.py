from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from apps.authentication.permissions import IsAdminUser, IsOwnerOrAdmin
from .models import User
from .serializers import UserSerializer


@extend_schema(tags=["Users"])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["list", "create", "destroy"]:
            return [IsAdminUser()]
        # retrieve/update/partial_update enforce owner-or-admin
        return [IsOwnerOrAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs
