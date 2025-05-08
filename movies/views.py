from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import  ListAPIView, get_object_or_404
from rest_framework.viewsets import ReadOnlyModelViewSet
from authorization.constants import ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR
from movies.models import Movie, Review
from movies.serializers import MovieSerializer, ReviewSerializer, MovieListSerializer
from rest_framework import filters



class HealthApiView(APIView):
    """
    эндпоинт для проверки работоспособности API.
    Используется для просмотра  системами.
    """
    permission_classes = (IsAuthenticated,)  # Только для авторизованных

    def get(self, request, *args, **kwargs):
        """
        Возвращает статус 200 OK, если сервер работает.
        """
        # В продакшене лучше использовать logging вместо print
        print(f"Health check from user: {request.user.username}")
        return HttpResponse("OK", status=200)


class LoginApiView(APIView):
    """
    для аутентификации пользователей.
    При успешном входе создает сессию пользователя.
    """
    permission_classes = (AllowAny,)  # Доступно без авторизации

    class InputSerializer(serializers.Serializer):
        """входящие данные для логина"""
        username = serializers.CharField(max_length=150)
        password = serializers.CharField(max_length=128, write_only=True)

        # Поле для тестирования (можно удалить в продакшене)
        test = serializers.CharField(
            max_length=128,
            required=False,
            help_text="Тестовое поле для отладки"
        )

    class OutputSerializer(serializers.Serializer):
        """Формат успешного ответа"""
        message = serializers.CharField()

    @extend_schema(
        request=InputSerializer,
        responses={
            200: OutputSerializer,
            401: {"detail": "Invalid credentials"}
        },
        tags=['auth'],
        description="""
        Аутентификация пользователя.
        При успехе создает  возвращает 200 OK.
        """
    )
    def post(self, request, *args, **kwargs):
        """
        Обрабатывает POST-запрос на вход в систему.
        """
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )

        if not user:
            return Response(
                {"detail": "Неверные учетные данные"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)
        return Response({"message": "Авторизация успешна"})


class LogoutApiView(APIView):
    """
    Завершает сеанс пользователя.
    Очищает данные сессии на сервере.
    """

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает выход пользователя из системы.
        """
        logout(request)
        return Response({"message": "Сеанс завершен"})


class RegisterApiView(APIView):
    """
    Регистрация новых пользователей в системе.
    Создает запись и возвращает данные пользователя.
    """
    permission_classes = (AllowAny,)

    class InputSerializer(serializers.ModelSerializer):
        """Сериализатор для входящих данных при  регистрации"""

        class Meta:
            model = get_user_model()
            fields = ['username', 'password']
            extra_kwargs = {
                'password': {'write_only': True}
            }

    class OutputSerializer(serializers.Serializer):
        """ответ после успешной регистрации"""
        id = serializers.IntegerField()
        username = serializers.CharField()
        role = serializers.ChoiceField(choices=[
            ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR
        ])
        created_at = serializers.DateTimeField()

    @extend_schema(
        request=InputSerializer,
        responses={
            201: OutputSerializer,
            400: {"detail": "Validation error"}
        },
        tags=['auth'],
        description="""
        Регистрирует нового пользователя.
        Пароль хешируется перед сохранением.
        """
    )
    def post(self, request, *args, **kwargs):
        """
        Создает нового пользователя в системе.
        """
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Хеширование пароля перед сохранением
        hashed_password = make_password(serializer.validated_data["password"])
        serializer.validated_data["password"] = hashed_password

        user = serializer.save()
        return Response(
            self.OutputSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class MeApiView(APIView):
    """
    Возвращает информацию о текущем АВТОРИЗОВАННОМ пользователе.
    """
    permission_classes = (IsAuthenticated,)

    class OutputSerializer(serializers.Serializer):
        """Структура ответа с данными пользователя"""
        id = serializers.IntegerField()
        username = serializers.CharField()
        role = serializers.ChoiceField(choices=[
            ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR
        ])
        created_at = serializers.DateTimeField()

    def get(self, request, *args, **kwargs):
        """
        Возвращает данные текущего пользователя.
        """
        return Response(self.OutputSerializer(request.user).data)


class MovieViewSet(ReadOnlyModelViewSet):
    queryset = Movie.objects.all().prefetch_related('actors', 'tags', 'reviews', 'liked_by').select_related('director')
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user  # чтобы is_favorite работал
        return context

    def list(self, request, *args, **kwargs):
        search_query = request.query_params.get('search')
        if search_query:
            try:
                movie = self.get_queryset().get(title__icontains=search_query)
                serializer = self.get_serializer(movie)
                return Response(serializer.data)
            except Movie.DoesNotExist:
                return Response({'detail': 'Фильм не найден'}, status=404)

        return super().list(request, *args, **kwargs)
    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.query_params.get('search'):
                return MovieSerializer
            return MovieListSerializer
        return self.serializer_class

class MovieSearchView(ListAPIView):
    """
    Поиск фильмов по названию и описанию.
    Использует встроенный SearchFilter DRF.
    """
    permission_classes = [AllowAny]
    def get(self, request):
        query = request.query_params.get('search', '')
        movies = Movie.objects.filter(title__icontains=query)
        serializer = MovieListSerializer(movies, many=True)
        return Response(serializer.data)
class TopMoviesAPIView(APIView):
    """
    Возвращает топ-10 фильмов по рейтингу.
    Используется для главной страницы и рекомендаций.
    """

    def get(self, request, *args, **kwargs):
        """
        Возвращает отсортированный список лучших фильмов.
        """
        top_movies = Movie.objects.order_by('-rating')[:10]
        serializer = MovieSerializer(top_movies, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API для управления отзывами.
    Поддерживает создание/редактирование отзывов к фильмам.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['movie']

    def get_queryset(self):
        """Возвращает только отзывы текущего пользователя"""
        return Review.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Создание отзыва через POST /api/movies/reviews/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'], url_path='reviews')
    def create_review_for_movie(self, request, pk=None):
        """
        Создание отзыва через POST /api/movies/12/reviews/
        """
        movie = get_object_or_404(Movie, pk=pk)

        # Проверяем существование отзыва
        if Review.objects.filter(user=request.user, movie=movie).exists():
            return Response(
                {"error": "Вы уже оставляли отзыв на этот фильм"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем отзыв
        serializer = self.get_serializer(data={
            **request.data,
            'movie': movie.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, movie=movie)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """Общая логика сохранения отзыва"""
        serializer.save(user=self.request.user)

class MovieHomeAPIView(APIView):
    """Главная страница с популярными фильмами"""
    def get(self, request):
        movies = Movie.objects.order_by('-rating')[:10]  # Топ-10 по рейтингу
        serializer = MovieSerializer(movies, many=True, context={
            'user': request.user
        })
        return Response({
            'movies': serializer.data,
            'description': 'Добро пожаловать в нашу кинотеку!'
        })