from django.urls import path
from .views import UserListCreateView, UserDetailView

app_name = 'users'

urlpatterns = [
    # User management endpoints
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
