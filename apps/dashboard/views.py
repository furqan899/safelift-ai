"""
Dashboard Views

API views for dashboard functionality.
Following Clean Code principles: Single Responsibility, clear documentation.
"""

import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .services import DashboardMetricsService
from .serializers import (
    DashboardOverviewSerializer,
    LanguageDistributionSerializer,
    QuickActionSerializer
)

logger = logging.getLogger(__name__)


class DashboardOverviewView(APIView):
    """
    API endpoint for retrieving complete dashboard overview.
    
    Returns all dashboard metrics including:
    - Active conversations with trends
    - Total users with trends
    - Resolution rate with comparison
    - Escalated cases with trends
    - Response time metrics
    - Language distribution
    - Quick actions
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Dashboard Overview",
        description="Retrieve complete dashboard overview with all metrics and trends",
        responses={
            200: OpenApiResponse(
                response=DashboardOverviewSerializer,
                description="Dashboard data retrieved successfully"
            ),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Admin access required")
        },
        tags=['Dashboard']
    )
    def get(self, request):
        """
        Retrieve dashboard overview with comprehensive error handling.
        
        Returns:
            Response: Dashboard metrics and analytics data
        
        Raises:
            HTTP 403: If user is not an administrator
            HTTP 500: If dashboard data retrieval fails
        """
        # Ensure only admins can access dashboard
        if not self._is_admin_user(request.user):
            logger.warning(
                f"Unauthorized dashboard access attempt by user: {request.user.username}"
            )
            return Response(
                {'error': 'Only administrators can access the dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            logger.info(f"Fetching dashboard data for admin: {request.user.username}")
            dashboard_data = self._build_dashboard_data()
            
            serializer = DashboardOverviewSerializer(data=dashboard_data)
            serializer.is_valid(raise_exception=True)
            
            logger.info("Dashboard data retrieved successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve dashboard data: {str(e)}",
                exc_info=True
            )
            return Response(
                {
                    'error': 'Failed to retrieve dashboard data',
                    'detail': str(e) if request.user.is_superuser else 'Internal server error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _build_dashboard_data(self) -> dict:
        """
        Build complete dashboard data from various sources.
        
        Returns:
            Dictionary containing all dashboard metrics
        """
        metrics = DashboardMetricsService.get_today_metrics()
        
        return {
            'active_conversations': metrics['active_conversations'],
            'total_users': metrics['total_users'],
            'resolution_rate': metrics['resolution_rate'],
            'escalated_cases': metrics['escalated_cases'],
            'response_time': metrics['response_time'],
            'language_distribution': DashboardMetricsService.get_language_distribution(),
            'quick_actions': DashboardMetricsService.get_quick_actions()
        }
    
    @staticmethod
    def _is_admin_user(user) -> bool:
        """
        Check if user has admin privileges.
        
        Args:
            user: User instance
            
        Returns:
            Boolean indicating admin status
        """
        return user.is_authenticated and user.is_admin


class LanguageDistributionView(APIView):
    """
    API endpoint for language distribution analytics.
    
    Provides detailed language usage statistics over a specified period.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Language Distribution",
        description="Retrieve language distribution for conversations over past 30 days",
        responses={
            200: OpenApiResponse(
                response=LanguageDistributionSerializer(many=True),
                description="Language distribution retrieved successfully"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden")
        },
        tags=['Dashboard']
    )
    def get(self, request):
        """
        Retrieve language distribution data with error handling.
        
        Query Parameters:
            days (int, optional): Number of days to analyze (default: 30)
        
        Returns:
            Response: Language distribution data
        """
        if not request.user.is_admin:
            logger.warning(
                f"Non-admin access attempt to language distribution by: {request.user.username}"
            )
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            days = int(request.query_params.get('days', 30))
            
            # Validate days parameter
            if days < 1 or days > 365:
                return Response(
                    {'error': 'Days parameter must be between 1 and 365'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Fetching language distribution for {days} days")
            distribution_data = DashboardMetricsService.get_language_distribution(days)
            
            serializer = LanguageDistributionSerializer(distribution_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Invalid days parameter: {str(e)}")
            return Response(
                {'error': 'Invalid days parameter. Must be a number.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to retrieve language distribution: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to retrieve language distribution'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuickActionsView(APIView):
    """
    API endpoint for dashboard quick actions.
    
    Returns available quick actions for the dashboard.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Quick Actions",
        description="Retrieve available quick actions for dashboard",
        responses={
            200: OpenApiResponse(
                response=QuickActionSerializer(many=True),
                description="Quick actions retrieved successfully"
            ),
            401: OpenApiResponse(description="Unauthorized")
        },
        tags=['Dashboard']
    )
    def get(self, request):
        """
        Retrieve quick actions.
        
        Returns:
            Response: List of quick action items
        """
        quick_actions = DashboardMetricsService.get_quick_actions()
        serializer = QuickActionSerializer(quick_actions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HealthStatusView(APIView):
    """
    API endpoint for system health status.
    
    Provides system health information and status indicators.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get System Health Status",
        description="Check system health and operational status",
        responses={
            200: OpenApiResponse(description="System is healthy")
        },
        tags=['Dashboard']
    )
    def get(self, request):
        """
        Get system health status.
        
        Returns:
            Response: System health indicators
        """
        return Response({
            'status': 'healthy',
            'message': 'System is operational',
            'timestamp': request.META.get('HTTP_DATE'),
        }, status=status.HTTP_200_OK)

