from rest_framework import viewsets, serializers

from django.contrib.auth.models import User

MIN_LENGTH = 8

class UserSignUpSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(
        write_only = True,
        min_length = MIN_LENGTH,
        error_messages = {
            "min_length": "La contraseña debe contener un mínimo de {MIN_LENGTH} caracteres"
        }
    )

    password2 = serializers.CharField(
        write_only = True,
        min_length = MIN_LENGTH,
        error_messages = {
            "min_length": "La contraseña debe contener un mínimo de {MIN_LENGTH} caracteres."
        }
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password", "password2"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("La contraseña no coincide")
        return data
    
    def create(self, validated_data):
        user = User.objects.create(
            username = validated_data["username"],
            email = validated_data["email"],
            first_name = validated_data["first_name"],
            last_name = validated_data["last_name"],
        )

        user.set_password(validated_data["password"])
        user.save()
        return user
    

class UserSignUpViewSet(viewsets.ModelViewSet):

    permission_classes = ()
    queryset = User.objects.all()
    serializer_class = UserSignUpSerializer