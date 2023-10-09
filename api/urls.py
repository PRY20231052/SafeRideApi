from rest_framework import routers
from django.urls import path, include
from api.views import route_views, register_views, favloc_views, trip_views
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()
router.register(r'routes', route_views.RouteViewSet, basename='routes')
router.register(r'trips', trip_views.TripViewSet, basename='trips')
router.register(r'favorite_locations', favloc_views.FavoriteLocationViewSet, basename='favorite_locations')
router.register(r'register', register_views.CustomUserCreateView, basename='register')
router.register(r'api-token-auth', obtain_auth_token, basename='api_token_auth')

urlpatterns = [
    path('', include(router.urls)),
]
