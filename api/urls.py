from rest_framework import routers
from django.urls import path, include
from api.views import route_views

router = routers.DefaultRouter()
router.register(r'routes', route_views.RouteViewSet, basename='routes')
router.register(r'trips', route_views.RouteViewSet, basename='trips')

urlpatterns = [
    path('', include(router.urls)),
]
