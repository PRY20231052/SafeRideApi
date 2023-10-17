from rest_framework import routers
from django.urls import path, include
from api.views import route_views, user_views

router = routers.DefaultRouter()
router.register(r'routes', route_views.RouteViewSet, basename='routes')
router.register(r'users', user_views.UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
