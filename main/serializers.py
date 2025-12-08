from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from main.models import CustomUser, Queue, QueueEntry, Notification, Room

class CustomUserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'phone_number', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'phone_number': {'required': False, 'allow_blank': True}
        }

    def validate_password(self, password):
        validate_password(password)
        return password

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        phone_number = validated_data.pop('phone_number', None)

        if phone_number == '':
            phone_number = None

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=role
        )

        if phone_number is not None:
            user.phone_number = phone_number
            user.save()

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

class RoomSerializer(serializers.ModelSerializer):
    entry_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ('id', 'name', 'teacher', 'is_active', 'created_at', 'entry_count')
        read_only_fields = ('id', 'teacher', 'created_at')

    def get_entry_count(self, obj):
        return obj.entries.filter(status__in=['waiting', 'ready']).count()

class QueueEntryDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = QueueEntry
        fields = ('id', 'username', 'first_name', 'last_name', 'position', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'scheduled_time': {'required': True}
        }

class QueueEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueEntry
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'notification_type', 'subject', 'message', 'is_read', 'created_at')
        read_only_fields = ('created_at',)
