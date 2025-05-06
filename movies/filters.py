import django_filters
from django.db.models import Q
from .models import Movie, Actor, Tag


class MovieFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    actor = django_filters.CharFilter(method='filter_by_actor')
    tag = django_filters.CharFilter(method='filter_by_tag')
    year = django_filters.NumberFilter(field_name='release_date__year')

    class Meta:
        model = Movie
        fields = []

    def filter_by_actor(self, queryset, name, value):
        """Фильтрация по актеру (точное совпадение)"""
        return queryset.filter(actors__name__iexact=value)

    def filter_by_actor(self, queryset, name, value):
        """Поиск по части имени актера"""
        return queryset.filter(actors__name__icontains=value)


    def filter_by_tag(self, queryset, name, value):
        """Фильтрация по тегу (точное совпадение)"""
        return queryset.filter(tags__name__iexact=value)

    def filter_queryset(self, queryset):
        """Основная логика фильтрации с условием """
        queryset = super().filter_queryset(queryset)

        # Получаем все примененные фильтры
        filters = {}
        for key, value in self.form.cleaned_data.items():
            if value not in (None, ''):
                filters[key] = value



        # Если переданы и actor, и tag - применяем условие И
        if 'actor' in filters and 'tag' in filters:
            queryset = queryset.filter(
                actors__name__iexact=filters['actor'],
                tags__name__iexact=filters['tag']
            ).distinct()

        return queryset