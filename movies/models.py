from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Director(models.Model):
    """Модель режиссера фильма"""
    name = models.CharField(
        max_length=255,
        verbose_name="Имя режиссера"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Режиссер"
        verbose_name_plural = "Режиссеры"


class Actor(models.Model):
    """Модель актера"""
    name = models.CharField(
        max_length=255,
        verbose_name="Имя актера"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Актер"
        verbose_name_plural = "Актеры"


class Tag(models.Model):
    """Модель тега/жанра фильма"""
    name = models.CharField(
        max_length=50,
        verbose_name="Тег"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Movie(models.Model):
    """Основная модель фильма"""
    # Основная информация
    title = models.CharField(
        max_length=255,
        verbose_name="Название"
    )
    release_date = models.DateField(
        verbose_name="Дата выхода"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    rating = models.FloatField(
        default=0.0,
        verbose_name="Рейтинг"
    )

    # Связи с другими моделями
    director = models.ForeignKey(
        Director,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Режиссер",
        related_name="movies"
    )
    actors = models.ManyToManyField(
        Actor,
        related_name="movies",
        verbose_name="Актеры"
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        verbose_name="Теги"
    )

    # Медиа и пользовательские данные
    poster_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на постер",
        default=''
    )
    liked_by = models.ManyToManyField(
        User,
        related_name='liked_movies',
        blank=True,
        verbose_name="Понравилось пользователям"
    )

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    def __str__(self):
        return f"{self.title} ({self.release_date.year})"

    class Meta:
        ordering = ['-rating']
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['rating']),
        ]



    def __str__(self):
        return f"Отзыв {self.user} на {self.movie}"

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=0)  # от 0 до 10
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"{self.user.username} – {self.movie.title} – {self.rating}"