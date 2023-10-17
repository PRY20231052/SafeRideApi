from rest_framework import viewsets
from django.contrib.auth.models import User

from api.serializers.user_serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class UserViewSet(viewsets.ModelViewSet) : 

    permission_classes = (AllowAny, )

    queryset = User.objects.all()
    serializer_class = UserSerializer