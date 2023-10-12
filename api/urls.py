from rest_framework import routers
from django.urls import path, include
from api.views import favorite_locations_views, route_views, sign_up_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'routes', route_views.RouteViewSet, basename='routes')
router.register(r'trips', route_views.RouteViewSet, basename='trips')
router.register(r'favorite_locations', favorite_locations_views.FavoriteLocationViewSet, basename='favloc')

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', sign_up_views.RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]
