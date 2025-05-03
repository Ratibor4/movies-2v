from rest_framework import serializers
from .models import User
from movies.models import Tag
from movies.serializers import MovieSerializer, TagSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    favorite_movies = MovieSerializer(many=True, read_only=True)
    preferred_tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar', 'role',
            'date_joined', 'favorite_movies', 'preferred_tags'
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']


class UpdatePreferencesSerializer(serializers.ModelSerializer):
    preferred_tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = ['preferred_tags']
