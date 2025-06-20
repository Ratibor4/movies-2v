from sqlite3 import IntegrityError
from django.contrib.auth import get_user_model, authenticate, logout
from rest_framework import serializers, status
from rest_framework.generics import RetrieveUpdateAPIView, get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from authorization.constants import ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR
from movies.models import UserActivity
from authorization.serializers import UserProfileSerializer, UpdateProfileSerializer, UpdatePreferencesSerializer
from movies.models import Movie
from movies.serializers import MovieSerializer, MovieTitleSerializer


class HealthApiView(APIView):
    """Проверка работоспособности API (healthcheck endpoint)"""
    permission_classes = (AllowAny,)  # Доступ без аутентификации

    def get(self, request, *args, **kwargs):
        """Возвращает статус работы сервера"""
        # Логирование запроса (можно использовать logger вместо print)
        print(f"Health check request from IP: {request.META.get('REMOTE_ADDR')}")
        return Response({"status": "OK", "service": "Movie API"}, status=200)

class LoginApiView(APIView):
    """Аутентификация пользователя и выдача JWT-токенов"""
    permission_classes = (AllowAny,)

    class InputSerializer(serializers.Serializer):
        """Сериализатор для данных входа"""
        username = serializers.CharField(help_text="Имя пользователя")
        password = serializers.CharField(
            style={'input_type': 'password'},
            help_text="Пароль пользователя"
        )

    def post(self, request, *args, **kwargs):
        """Обработка запроса на вход в систему"""
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )

        if not user:
            return Response(
                {"detail": "Неверные учетные данные"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
            }
        })


class LogoutApiView(APIView):
    """Выход пользователя из системы"""

    def post(self, request, *args, **kwargs):
        """Завершает сеанс пользователя"""
        logout(request)
        return Response(
            {"message": "Выход выполнен успешно"},
            status=status.HTTP_200_OK
        )


class RegisterApiView(APIView):
    """Регистрация нового пользователя"""
    permission_classes = (AllowAny,)

    class InputSerializer(serializers.ModelSerializer):
        """Сериализатор для данных регистрации"""
        password = serializers.CharField(
            write_only=True,
            style={'input_type': 'password'},
            min_length=8,
            help_text="Пароль должен содержать минимум 8 символов"
        )

        class Meta:
            model = get_user_model()
            fields = ['username', 'password', 'email']
            extra_kwargs = {
                'email': {'required': True}
            }

    def post(self, request):
        """Создание нового пользователя"""
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = get_user_model().objects.create_user(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                email=serializer.validated_data['email']
            )
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"detail": "Пользователь с такими данными уже существует"},
                status=status.HTTP_400_BAD_REQUEST
            )

class MeApiView(APIView):

    class OutputSerializer(serializers.Serializer):
        ROLE_CHOICES = [ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR]

        id = serializers.IntegerField()
        username = serializers.CharField(max_length=255)
        first_name = serializers.CharField(allow_blank=True, allow_null=True)
        last_name = serializers.CharField(allow_blank=True, allow_null=True)
        role = serializers.ChoiceField(choices=ROLE_CHOICES)
        created_at = serializers.DateTimeField()

    def get(self, request, *args, **kwargs):
        return Response(self.OutputSerializer(request.user).data)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UpdatePreferencesSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UpdatePreferencesSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteMoviesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        """Добавить или удалить фильм из избранного (переключатель)"""
        movie = get_object_or_404(Movie, id=movie_id)
        user = request.user

        if movie in user.favorite_movies.all():
            user.favorite_movies.remove(movie)
            return Response({"detail": "Removed from favorites."}, status=status.HTTP_200_OK)
        else:
            user.favorite_movies.add(movie)
            return Response({"detail": "Added to favorites."}, status=status.HTTP_201_CREATED)

    def get(self, request):
        """Получить список избранных фильмов"""
        user = request.user
        favorite_movies = user.favorite_movies.all()
        serializer = MovieTitleSerializer(favorite_movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, movie_id):
        """Удалить фильм из избранного (конкретно, через DELETE-запрос)"""
        movie = get_object_or_404(Movie, id=movie_id)
        user = request.user

        if movie in user.favorite_movies.all():
            user.favorite_movies.remove(movie)
            return Response({"detail": "Removed from favorites."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "Movie not in favorites."}, status=status.HTTP_404_NOT_FOUND)
class UserHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities = UserActivity.objects.filter(user=request.user).select_related('movie')
        movies = [activity.movie for activity in activities]
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)