from rest_framework import generics
from rest_framework.permissions import AllowAny
from api.models.custom_user import CustomUser
from api.serializers.user_serializer import CustomUserSerializer

class CustomUserCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)
