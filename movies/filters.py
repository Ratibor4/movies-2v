import django_filters
from django.db.models import Q
from .models import Movie, Actor, Tag

class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', help_text="Фильтр по названию")
    actor = django_filters.CharFilter(method='filter_by_actor', help_text="Фильтр по актерам")
    tag = django_filters.CharFilter(method='filter_by_tag', help_text="Фильтр по тегам")
    year = django_filters.NumberFilter(field_name='release_date__year', help_text="Год выпуска")
    exclude_tag = django_filters.CharFilter(method='exclude_by_tag', help_text="Исключить тег")
    exclude_actor = django_filters.CharFilter(method='exclude_by_actor', help_text="Исключить актера")

    def exclude_by_tag(self, queryset, name, value):
        """Исключает фильмы с указанным тегом (регистронезависимо)"""
        return queryset.exclude(tags__name__iexact=value.strip())

    def exclude_by_actor(self, queryset, name, value):
        """Исключает фильмы с указанным актером (по частичному совпадению)"""
        return queryset.exclude(actors__name__icontains=value.strip())

    def filter_by_actor(self, queryset, name, value):
        """Фильтрация по актеру (по частичному совпадению)"""
        terms = [term.strip() for term in value.split(',')]
        q_objects = Q()
        for term in terms:
            q_objects |= Q(actors__name__icontains=term)
        return queryset.filter(q_objects).distinct()

    def filter_by_tag(self, queryset, name, value):
        """Фильтрация по тегу (точное совпадение, можно через запятую)"""
        terms = [term.strip() for term in value.split(',')]
        return queryset.filter(tags__name__in=terms).distinct()

    class Meta:
        model = Movie
        fields = []