from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from main.models import CustomUser
from django.core.exceptions import ValidationError

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate_password(self, password):
        try:
            validate_password(password)
        except ValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return password

    def validate(self, passwords):
        if passwords['password'] != passwords['password2']:
            raise serializers.ValidationError({"password2": "Passwords don`t match"})

        return passwords

    def create(self, validated_data):
        validated_data.pop('password2')

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Користувач не активований")
                data['user'] = user
            else:
                raise serializers.ValidationError("Невірне ім'я користувача або пароль")
        else:
            raise serializers.ValidationError("Вкажіть ім'я користувача та пароль")

        return data





class QueueSerializer(serializers.ModelSerializer):
    pass


class QueueEntrySerializer(serializers.ModelSerializer):
    pass
