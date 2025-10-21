from rest_framework_simplejwt.views import TokenRefreshView
from django.urls import path
from .views import AdminLoginView, LogoutView, UserListCreateView, UserDetailView, HealthCheckView

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', AdminLoginView.as_view(), name='admin-login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # User management
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
