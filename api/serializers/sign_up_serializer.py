from rest_framework import serializers
from rest_framework.validators import ValidationError
from api.models.custom_user import CustomUser

class SignUpSerializer(serializers.ModelSerializer):
    email=serializers.CharField(max_length=80)
    username=serializers.CharField(max_length=45)
    password=serializers.CharField(min_length=8,write_only=True)

    class Meta:
        model = CustomUser
        fields = ["email", "username", "password"]

    def validate(self, attrs):

        email_exists=CustomUser.objects.filter(email=attrs['email']).exists()

        if email_exists:
            raise ValidationError("El correo ya está en uso")
        return super().validate(attrs)