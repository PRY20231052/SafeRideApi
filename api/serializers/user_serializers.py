from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'password',
            'phone_number',
            'full_name',

        )
        extra_kwargs = {
            'password': {
                'write_only': True,
            }
        }

        def create(self, data):
            password = data.pop('password')
            user = User(**data)
            user.set_password(password)
            user.save()
            return {
                'username': user.username,
                'email': user.email,
            }