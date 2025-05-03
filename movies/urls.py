from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import MovieSearchView, TopMoviesAPIView, MovieViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movies')
router.register(r'reviews', ReviewViewSet, basename='review')


urlpatterns = [
    path('', include(router.urls)),
    path('search/', MovieSearchView.as_view(), name='movie-search'),
    path('top/', TopMoviesAPIView.as_view(), name='top-movies'),
] + router.urls