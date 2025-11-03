from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import (
    LoginSerializer, 
    TokenResponseSerializer, 
    LogoutSerializer
)
from .services import AuthenticationService


class LoginView(APIView):
    """
    API endpoint for admin authentication.
    
    Handles admin login and returns JWT tokens for authenticated sessions.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Admin Login",
        description="Authenticate admin user and receive JWT tokens",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful"
            ),
            400: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Access denied"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        """
        Authenticate admin and return tokens.
        
        Args:
            request: HTTP request with username and password
            
        Returns:
            Response with tokens and user info
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        auth_data = AuthenticationService.authenticate_admin(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        return Response(auth_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    API endpoint for user logout.
    
    Note: With JWT, actual logout happens client-side by removing tokens.
    This endpoint serves as a confirmation point.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Logout",
        description="Logout user session",
        responses={
            200: OpenApiResponse(
                response=LogoutSerializer,
                description="Logout successful"
            )
        },
        tags=["Authentication"],
    )
    def post(self, request):
        """
        Logout current user.
        
        Returns:
            Response confirming logout
        """
        serializer = LogoutSerializer({"message": "Successfully logged out"})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReadinessProbeView(APIView):
    """
    Readiness probe endpoint for monitoring, requires authentication.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Readiness Probe",
        description="Check API readiness including auth status",
        responses={
            200: OpenApiResponse(description="API is ready")
        },
        tags=["System"],
    )
    def get(self, request):
        """Return readiness status and current user."""
        return Response({
            "status": "ready",
            "user": request.user.username if request.user.is_authenticated else None,
            "is_admin": request.user.is_admin if request.user.is_authenticated else False,
        })


class LivenessProbeView(APIView):
    """
    Simple liveness probe endpoint for monitoring.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Liveness Probe",
        description="Simple liveness check for monitoring",
        responses={
            200: OpenApiResponse(description="API is live")
        },
        tags=["System"],
    )
    def get(self, request):
        """Return liveness status."""
        return Response({"status": "live"})

@extend_schema(tags=["Authentication"])
class CustomTokenRefreshView(TokenRefreshView):
    """Token refresh endpoint for JWT authentication."""

    authentication_classes = ()