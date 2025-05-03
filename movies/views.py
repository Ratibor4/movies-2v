

from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers, status, viewsets, permissions
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404
from rest_framework.viewsets import ReadOnlyModelViewSet

from authorization.constants import ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR
from movies.filters import MovieFilter
from movies.models import Movie, Review
from movies.serializers import MovieSerializer, ReviewSerializer


class HealthApiView(APIView):

    permission_classes = (IsAuthenticated,)
    # permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):

        print("Get request was sent by:", request.user)

        return HttpResponse("Ok!")


class LoginApiView(APIView):

    permission_classes = (AllowAny,)

    class InputSerializer(serializers.Serializer):
        username = serializers.CharField(max_length=150)
        password = serializers.CharField(max_length=128)
        test = serializers.CharField(max_length=128)

        class Meta:
            ref_name = "LoginInputSerializer"

    class OutputSerializer(serializers.Serializer):
        message = serializers.CharField()

        class Meta:
            ref_name = "LoginOutputSerializer"

    @extend_schema(
        request=InputSerializer,
        responses={200: OutputSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            print(serializer.validated_data)

            user = authenticate(
                request,
                username=serializer.validated_data.get("username"),
                password=serializer.validated_data.get("password")
            )

            if user:
                login(request, user)
                print("user:", user.username)
            else:
                return Response({"message": "Invalid credentials!"}, status=401)

        return Response({"message": "Login successful!"})


class LogoutApiView(APIView):

    def post(self, request, *args, **kwargs):
        logout(request)

        return Response({"message": "Logout successful!"})


class RegisterApiView(APIView):

    permission_classes = (AllowAny,)

    class InputSerializer(serializers.ModelSerializer):
        class Meta:
            model = get_user_model()
            fields = ['username', 'password']
            ref_name = "RegisterInputSerializer"

    class OutputSerializer(serializers.Serializer):
        ROLE_CHOICES = [ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR]

        id = serializers.IntegerField()
        username = serializers.CharField(max_length=255)
        first_name = serializers.CharField(allow_blank=True, allow_null=True)
        last_name = serializers.CharField(allow_blank=True, allow_null=True)
        role = serializers.ChoiceField(choices=ROLE_CHOICES)
        created_at = serializers.DateTimeField()

        class Meta:
            ref_name = "RegisterOutputSerializer"


    @extend_schema(
        description="Register new users.",
        request=InputSerializer,
        responses={
            201: OutputSerializer,
            404: {"message": "User Not Found"}
        },
        tags=['auth']
    )
    def post(self, request, *args, **kwargs):

        serializer = self.InputSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            print(serializer.validated_data)
            hashed_password = make_password(serializer.validated_data.get("password"))
            print("hashed_password:", hashed_password)

            serializer.validated_data["password"] = hashed_password
            user = serializer.save()

        return Response(
            self.OutputSerializer(user).data,
            status=status.HTTP_201_CREATED
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


class MovieViewSet(ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filterset_class = MovieFilter

class MovieSearchView(ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description']



class TopMoviesAPIView(APIView):
    def get(self, request, *args, **kwargs):
        movies = Movie.objects.order_by('-rating')[:10]  # или сортировка по другому полю
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['movie']  # фильтрация по фильму

    def perform_create(self, serializer):
        user = self.request.user
        movie_id = self.request.query_params.get('movie')

        # Проверяем, что передан ID фильма
        if not movie_id:
            raise serializers.ValidationError("ID фильма обязателен (например, ?movie=2)")

        # Получаем фильм или возвращаем 404
        movie = get_object_or_404(Movie, id=movie_id)

        # Проверяем, есть ли уже отзыв от этого пользователя
        if Review.objects.filter(user=user, movie=movie).exists():
            raise serializers.ValidationError("Вы уже оставляли отзыв к этому фильму.")

        # Сохраняем отзыв с привязкой к пользователю и фильму
        serializer.save(user=user, movie=movie)
