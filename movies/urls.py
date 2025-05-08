from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import MovieViewSet, ReviewViewSet, MovieSearchView

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'reviews', ReviewViewSet, basename='reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('api/search/', MovieSearchView.as_view(), name='movie-search'),
    path('movies/<int:pk>/reviews/',
         ReviewViewSet.as_view({'post': 'create_review_for_movie'}),
         name='movie-reviews'),
]