from rest_framework import viewsets
from django.contrib.auth import get_user_model

from api.serializers.user_serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated

class UserListViewSet(viewsets.ModelViewSet) : 

    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()