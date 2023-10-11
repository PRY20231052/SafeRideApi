from rest_framework import routers
from django.urls import path, include
from api.views import favorite_location_views, route_views, register_views, trip_views
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()
router.register(r'routes', route_views.RouteViewSet, basename='routes')
router.register(r'trips', trip_views.TripViewSet, basename='trips')
router.register(r'favorite_locations', favorite_location_views.FavoriteLocationViewSet, basename='favorite_locations')


urlpatterns = [
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('register/', register_views.UserList.as_view(), name='register'),
    path('', include(router.urls)),
]
