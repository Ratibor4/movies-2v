import django_filters
from rest_framework import viewsets

from .models import Movie


class MovieFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(field_name='tags__name', lookup_expr='icontains')

    class Meta:
        model = Movie
        fields = ['tags']


# Затем в views.py
from .filters import MovieFilter


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_class = MovieFilter