from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from .models import User
from .serializers import UserSerializer

User = get_user_model()


class UserListCreateView(APIView):
    """
    API view for listing and creating users (admin only).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Users",
        description="Get a list of all users (admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        """List all users (admin only)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can list users'},
                status=status.HTTP_403_FORBIDDEN
            )

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
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can create users'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """
    API view for retrieving, updating, and deleting individual users (admin only).
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Get user object by primary key."""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    @extend_schema(
        summary="Get User",
        description="Get details of a specific user",
        responses={200: UserSerializer}
    )
    def get(self, request, pk):
        """Get user details."""
        if not request.user.is_admin and request.user.id != int(pk):
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object(pk)
        if user is None:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSerializer(user)
        return Response(serializer.data)

    # @extend_schema(
    #     summary="Update User",
    #     description="Update a user (admin only)",
    #     request=UserSerializer,
    #     responses={200: UserSerializer}
    # )
    # def put(self, request, pk):
    #     """Update user (admin only)."""
    #     if not request.user.is_admin:
    #         return Response(
    #             {'error': 'Only admins can update users'},
    #             status=status.HTTP_403_FORBIDDEN
    #         )

    #     user = self.get_object(pk)
    #     if user is None:
    #         return Response(
    #             {'error': 'User not found'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )

    #     serializer = UserSerializer(user, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @extend_schema(
    #     summary="Partial Update User",
    #     description="Partially update a user (admin only)",
    #     request=UserSerializer,
    #     responses={200: UserSerializer}
    # )
    # def patch(self, request, pk):
    #     """Partially update user (admin only)."""
    #     if not request.user.is_admin:
    #         return Response(
    #             {'error': 'Only admins can update users'},
    #             status=status.HTTP_403_FORBIDDEN
    #         )

    #     user = self.get_object(pk)
    #     if user is None:
    #         return Response(
    #             {'error': 'User not found'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )

    #     serializer = UserSerializer(user, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete User",
        description="Delete a user (admin only)",
        responses={204: None}
    )
    def delete(self, request, pk):
        """Delete user (admin only)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can delete users'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object(pk)
        if user is None:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
