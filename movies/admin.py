from django.contrib import admin
from .models import Movie, Director, Actor, Tag, Review


class ActorInline(admin.TabularInline):
    model = Movie.actors.through
    extra = 1
    verbose_name = 'Актер'
    verbose_name_plural = 'Актеры'


class TagInline(admin.TabularInline):
    model = Movie.tags.through
    extra = 1
    verbose_name = 'Тег'
    verbose_name_plural = 'Теги'


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'rating', 'director')
    list_filter = ('release_date', 'tags', 'rating')
    search_fields = ('title', 'description')
    filter_horizontal = ('actors', 'tags', 'liked_by')
    readonly_fields = ('created_at', 'updated_at')

    def display_actors(self, obj):
        return ", ".join([actor.name for actor in obj.actors.all()[:3]])

    display_actors.short_description = 'Актеры'


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'movie', 'rating', 'created_at')
    search_fields = ('text',)
    list_filter = ('movie', 'rating', 'created_at')