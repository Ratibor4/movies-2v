

from django.contrib.auth import get_user_model, authenticate, logout

from django.http import HttpResponse
from rest_framework import serializers, status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authorization.constants import ROLE_ADMIN, ROLE_USER, ROLE_MODERATOR
from movies.models import UserActivity
from authorization.serializers import UserProfileSerializer, UpdateProfileSerializer, UpdatePreferencesSerializer
from movies.models import Movie
from movies.serializers import MovieSerializer


class HealthApiView(APIView):

    permission_classes = (IsAuthenticated,)
    # permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):

        print("Get request was sent by:", request.user)

        return HttpResponse("Ok!")


class LoginApiView(APIView):
    permission_classes = (AllowAny,)

    class InputSerializer(serializers.Serializer):
        username = serializers.CharField()
        password = serializers.CharField()

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': user.username,
                'id': user.id,
                'role': user.role,
            })
        return Response({"detail": "Invalid credentials"}, status=401)

class LogoutApiView(APIView):

    def post(self, request, *args, **kwargs):
        logout(request)

        return Response({"message": "Logout successful!"})


class RegisterApiView(APIView):
    permission_classes = (AllowAny,)

    class InputSerializer(serializers.ModelSerializer):
        password = serializers.CharField(write_only=True)

        class Meta:
            model = get_user_model()
            fields = ['username', 'password', 'email']
            extra_kwargs = {
                'password': {'write_only': True}
            }

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_model().objects.create_user(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            email=serializer.validated_data.get('email')
        )

        return Response({
            'id': user.id,
            'username': user.username,
            'role': user.role
        }, status=201)


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

class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateProfileSerializer
        return UserProfileSerializer


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

    def get(self, request):
        movies = request.user.liked_movies.all()
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

    def post(self, request, movie_id):
        try:
            movie = Movie.objects.get(pk=movie_id)
            request.user.liked_movies.add(movie)
            return Response({'status': 'added to favorites'})
        except Movie.DoesNotExist:
            return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, movie_id):
        try:
            movie = Movie.objects.get(pk=movie_id)
            request.user.liked_movies.remove(movie)
            return Response({'status': 'removed from favorites'})
        except Movie.DoesNotExist:
            return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)


class UserHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities = UserActivity.objects.filter(user=request.user).select_related('movie')
        movies = [activity.movie for activity in activities]
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)