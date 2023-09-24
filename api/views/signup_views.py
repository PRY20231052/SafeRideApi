from django.db import models
from rest_framework import viewsets, serializers
from django.contrib.auth.models import User

# Constante que define el tamaño mínimo de la contraseña
MIN_LENGTH = 8

# Extensión del modelo User para añadir el campo favorite_locations
class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='extended')
    favorite_locations = models.JSONField(default=list)

# Serializador para el registro de usuarios
class UserSignUpSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=MIN_LENGTH,
        error_messages={
            "min_length": f"La contraseña debe contener un mínimo de {MIN_LENGTH} caracteres"
        }
    )

    password2 = serializers.CharField(
        write_only=True,
        min_length=MIN_LENGTH,
        error_messages={
            "min_length": f"La contraseña debe contener un mínimo de {MIN_LENGTH} caracteres."
        }
    )

    favorite_locations = serializers.ListField(
        child=serializers.JSONField(),
        required=False
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password", "password2", "favorite_locations"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("La contraseña no coincide")
        return data
    
    def create(self, validated_data):
        # Se extrae 'favorite_locations' y se almacena en una variable
        favorite_locations = validated_data.pop('favorite_locations', [])

        # Creación del usuario
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()

        # Creación del perfil extendido del usuario con las ubicaciones favoritas
        ExtendedUser.objects.create(user=user, favorite_locations=favorite_locations)
        
        return user

class UserSignUpViewSet(viewsets.ModelViewSet):
    permission_classes = ()
    queryset = User.objects.all()
    serializer_class = UserSignUpSerializer