from rest_framework import serializers
from .models import User
from movies.models import Tag
from movies.serializers import MovieSerializer, TagSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для полного профиля пользователя.
    Включает все основные данные + связанные сущности:
    - Избранные фильмы (как полные объекты)
    - Предпочитаемые жанры (теги)
    """
    favorite_movies = MovieSerializer(many=True, read_only=True)
    preferred_tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar', 'role',
            'date_joined', 'favorite_movies', 'preferred_tags'
        ]
        read_only_fields = ['id', 'role', 'date_joined']  # Эти поля нельзя менять


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления основных данных профиля.
    Ограниченный набор полей, доступных для изменения.
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']  # Только эти поля можно обновлять


class UpdatePreferencesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления предпочтений пользователя.
    Позволяет изменять только список любимых жанров (тегов).
    Принимает список ID тегов.
    """
    preferred_tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),  # Валидация существования тегов
        required=False  # Не обязательно передавать при обновлении
    )

    class Meta:
        model = User
        fields = ['preferred_tags']  # Только теги можно обновлять