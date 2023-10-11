from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.models.favorite_location import FavoriteLocation
from api.serializers.favorite_location_serializer import FavoriteLocationSerializer

class FavoriteLocationViewSet(viewsets.GenericViewSet):
    serializer_class = FavoriteLocationSerializer
    permission_classes = ()

    def list(self, request):
        queryset = FavoriteLocation.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        favorite_location = FavoriteLocation.objects.get(pk=pk)
        serializer = self.serializer_class(favorite_location, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        favorite_location = FavoriteLocation.objects.get(pk=pk)
        favorite_location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
