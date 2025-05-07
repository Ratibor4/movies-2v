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
    is_favorite = serializers.SerializerMethodField()
    director = DirectorSerializer()
    actors = ActorSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'description', 'release_date', 'rating',
            'poster_url', 'director', 'actors', 'tags', 'is_favorite'
        ]

    def get_is_favorite(self, obj):
        """Проверяем, есть ли фильм в избранном у пользователя"""
        user = self.context.get('user')
        if user and user.is_authenticated:
            return user.favorite_movies.filter(id=obj.id).exists()
        return False
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
    user = serializers.StringRelatedField(read_only=True)
    movie = serializers.PrimaryKeyRelatedField(queryset=Movie.objects.all())

    class Meta:
        model = Review
        fields = ['id', 'user', 'movie', 'text', 'rating', 'created_at']
        read_only_fields = ['user', 'created_at']
        extra_kwargs = {
            'movie': {'required': True}
        }

    def validate_rating(self, value):
        """Проверка рейтинга (1-10)"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 10")
        return value
class MovieSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = '__all__'

class MovieTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title']

class MovieListSerializer(serializers.ModelSerializer):
    director = serializers.StringRelatedField()

    class Meta:
        model = Movie
        fields = ['id', 'title', 'director']