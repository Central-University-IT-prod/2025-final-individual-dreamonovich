from rest_framework import serializers

from app.serializers import ClearNullMixin
from .models import Client


class ClientSerializer(ClearNullMixin, serializers.ModelSerializer):
    client_id = serializers.UUIDField(source="id")

    class Meta:
        model = Client
        fields = ("client_id", "login", "age", "location", "gender")
