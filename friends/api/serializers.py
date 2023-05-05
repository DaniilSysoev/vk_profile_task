from rest_framework import serializers
from .models import FriendsList, Requests
from django.contrib.auth import get_user_model


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsList
        fields = '__all__'


class RequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}