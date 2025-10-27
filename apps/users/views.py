from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdminUser, CanAccessUser


@extend_schema(tags=["Users"])
class UserListCreateView(APIView):
    """
    API view for listing and creating users (admin only).
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="List Users",
        description="Get a list of all users (admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        """List all users (admin only)."""
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create User",
        description="Create a new user (admin only)",
        request=UserSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request):
        """Create a new user (admin only)."""
        serializer = UserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Users"])
class UserDetailView(APIView):
    """
    API view for retrieving, updating, and deleting individual users.
    Users can access their own data; admins can access any user data.
    """

    def get_permissions(self):
        """Return permissions based on the action."""
        if self.request.method == 'DELETE':
            # Only admins can delete users
            return [IsAdminUser()]
        # GET, PUT, PATCH use CanAccessUser permission
        return [CanAccessUser()]

    @extend_schema(
        summary="Get User",
        description="Get details of a specific user (own data or admin access)",
        responses={200: UserSerializer}
    )
    def get(self, request, pk):
        """Get user details."""
        user = get_object_or_404(User, pk=pk)
        self.check_object_permissions(request, user)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @extend_schema(
        summary="Update User",
        description="Update a user completely (own data or admin access)",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request, pk):
        """Update user completely."""
        user = get_object_or_404(User, pk=pk)
        self.check_object_permissions(request, user)
        serializer = UserSerializer(user, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partial Update User",
        description="Partially update a user (own data or admin access)",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request, pk):
        """Partially update user."""
        user = get_object_or_404(User, pk=pk)
        self.check_object_permissions(request, user)
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete User",
        description="Delete a user (admin only)",
        responses={204: None}
    )
    def delete(self, request, pk):
        """Delete user (admin only)."""
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
