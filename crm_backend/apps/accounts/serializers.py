"""Accounts app serializers for REST API."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.validators import (
    validate_email,
    validate_password_strength,
    validate_phone_turkey,
    validate_tc_kimlik_no,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "role_display",
            "phone",
            "tc_kimlik_no",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["is_staff", "is_superuser", "date_joined", "last_login"]


class UserMeSerializer(UserSerializer):
    """Serializer for /me/ endpoint — role is read-only for self-update."""

    class Meta(UserSerializer.Meta):
        read_only_fields = [
            *UserSerializer.Meta.read_only_fields,
            "role",
            "is_active",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password_strength],
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone",
            "tc_kimlik_no",
        ]

    def validate_email(self, value: str) -> str:
        return validate_email(value)

    def validate_phone(self, value: str | None) -> str | None:
        if value:
            return validate_phone_turkey(value)
        return value

    def validate_tc_kimlik_no(self, value: str | None) -> str | None:
        if value:
            return validate_tc_kimlik_no(value)
        return value

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
