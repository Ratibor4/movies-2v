from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import MovieSearchView, TopMoviesAPIView, MovieViewSet, ReviewViewSet, MovieHomeAPIView

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    path('movies/<int:pk>/reviews/',
         ReviewViewSet.as_view({'post': 'create_review_for_movie'}),
         name='movie-reviews'),
]