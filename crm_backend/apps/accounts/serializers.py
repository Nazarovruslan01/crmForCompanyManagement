"""Accounts app serializers for REST API."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'full_name',
            'role', 'role_display',
            'phone', 'tc_kimlik_no',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login',
        ]
        read_only_fields = [
            'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password',
            'first_name', 'last_name',
            'role', 'phone', 'tc_kimlik_no',
        ]

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
