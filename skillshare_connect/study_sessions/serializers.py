from rest_framework import serializers
from mainapp.models import Session
from django.contrib.auth import get_user_model


User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class SessionSerializer(serializers.ModelSerializer):
    host = UserMiniSerializer(read_only=True)
    participants = UserMiniSerializer(many=True, read_only=True)


    class Meta:
        model = Session
        fields = ("id", "title", "description", "start_time", "end_time", "host", "participants", "external_link", "created_at")


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ("title", "description", "start_time", "end_time", "external_link")


def validate(self, data):
    if data["start_time"] >= data["end_time"]:
        raise serializers.ValidationError("end_time must be after start_time")
    return data