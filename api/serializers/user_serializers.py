from api.models.user import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'password',
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
            return user


# # IMPLEMENTACION DE PABLO
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ["id", "email", "username", "password"]

#     def create(self, validated_data):
#         user = CustomUser.objects.create(
#             email=validated_data['email'],
#             username=validated_data['username']
#         )
#         user.set_password(validated_data['password'])
#         user.save()
#         return user