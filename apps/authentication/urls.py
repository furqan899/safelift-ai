from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, ReadinessProbeView, LivenessProbeView

app_name = 'authentication'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('readyz/', ReadinessProbeView.as_view(), name='readiness'),
    path('livez/', LivenessProbeView.as_view(), name='liveness'),
]