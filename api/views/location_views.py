from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.serializers.location_serializer import LocationSerializer

class LocationViewSet(viewsets.ViewSet):

    serializer_class = LocationSerializer
    permission_classes = ()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            location = serializer.save()  # Save the Location instance (non-persistent)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)