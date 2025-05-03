from rest_framework import serializers
from rest_framework.generics import ListAPIView
from movies.models import Review

from .models import Movie, Director, Actor, Tag
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = ['id', 'name']

class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ['id', 'name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class MovieSerializer(serializers.ModelSerializer):
    director = serializers.StringRelatedField()
    actors = serializers.StringRelatedField(many=True)
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Movie
        fields = '__all__'
        depth = 1

class InputSerializer(serializers.ModelSerializer):
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

class MovieListAPIView(ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer



class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # чтобы показывать username

    class Meta:
        model = Review
        fields = ['id', 'user', 'text', 'rating', 'created_at']

class MovieSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = '__all__'