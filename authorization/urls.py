from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView,
)

from authorization import views
from authorization.views import FavoriteMoviesView

urlpatterns = [
    path('auth/health/', views.HealthApiView.as_view()),
    path('auth/me/', views.MeApiView.as_view()),
    path('auth/register/', views.RegisterApiView.as_view()),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/login/', views.LoginApiView.as_view()),
    path('auth/logout/', views.LogoutApiView.as_view()),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('auth/preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    path('favorites/<int:movie_id>/', FavoriteMoviesView.as_view(), name='favorite-movie'),
    path('auth/favorites/<int:movie_id>/', views.FavoriteMoviesView.as_view(), name='favorite-movie-toggle'),
    path('auth/history/', views.UserHistoryView.as_view(), name='user-history'),
]
