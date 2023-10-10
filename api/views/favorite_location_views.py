from rest_framework import viewsets
from api.models.favorite_location import FavoriteLocation
from api.serializers.favorite_location_serializer import FavoriteLocationSerializer

class FavoriteLocationViewSet(viewsets.ModelViewSet):
    queryset = FavoriteLocation.objects.all()
    serializer_class = FavoriteLocationSerializer
