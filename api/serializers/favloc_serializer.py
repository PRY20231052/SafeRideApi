from rest_framework import serializers
from api.models.favorite_location import FavoriteLocation

class FavoriteLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteLocation
        fields = '__all__'
