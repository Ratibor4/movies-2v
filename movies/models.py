from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Director(models.Model):
    """
    Модель режиссера фильма.
     основная информацию о режиссере.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Полное имя",
        help_text="Введите полное имя режиссера"
    )

    def __str__(self):
        """ представление  админки и API"""
        return self.name

    class Meta:
        verbose_name = "Режиссер"
        verbose_name_plural = "Режиссеры"
        ordering = ['name']  # Сортировка по умолчанию


class Actor(models.Model):
    """
    Модель актера.
    Может быть связана с несколькими фильмами через ManyToMany.
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Полное имя",
        help_text="Введите полное имя актера"
    )

    def __str__(self):
        return f"Актер: {self.name}"

    class Meta:
        verbose_name = "Актер"
        verbose_name_plural = "Актеры"
        indexes = [
            models.Index(fields=['name']),  # Индекс для ускорения поиска
        ]


class Tag(models.Model):
    """
    Жанр или тег для категоризации фильмов.
    Примеры: "боевик", "комедия", "фантастика".
    """
    name = models.CharField(
        max_length=50,
        unique=True,  # Уникальное название тега
        verbose_name="Название тега",
        help_text="Максимум 50 символов"
    )

    def __str__(self):
        return self.name.capitalize()  # Всегда с заглавной буквы

    class Meta:
        verbose_name = "Жанр/Тег"
        verbose_name_plural = "Жанры/Теги"


class Movie(models.Model):
    """
    Основная модель фильма.
    Содержит полную информацию.
    """
    # Основные атрибуты
    title = models.CharField(
        max_length=255,
        verbose_name="Название фильма",
        help_text="Полное официальное название"
    )
    release_date = models.DateField(
        verbose_name="Дата премьеры",
        help_text="Дата первого показа"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Полное описание сюжета"
    )
    rating = models.FloatField(
        default=0.0,
        verbose_name="Рейтинг",
        help_text="Средняя оценка от 0 до 10"
    )

    # Связи с другими моделями
    director = models.ForeignKey(
        Director,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Режиссер",
        related_name="movies",
        help_text="Основной режиссер фильма"
    )
    actors = models.ManyToManyField(
        Actor,
        related_name="movies",
        verbose_name="Актерский состав",
        blank=True
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        verbose_name="Жанры и теги",
        help_text="Выберите подходящие жанры"
    )

    # Медиа-контент
    poster_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Постер фильма",
        help_text="Ссылка на изображение постера",
        default=''
    )

    # Пользовательские взаимодействия
    liked_by = models.ManyToManyField(
        User,
        related_name='liked_movies',
        blank=True,
        verbose_name="В избранном у пользователей"
    )

    # Технические поля
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления в систему"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата последнего обновления"
    )

    def __str__(self):
        return f"{self.title} ({self.release_date.year})"

    class Meta:
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        ordering = ['-rating', 'title']  # Сортировка по рейтингу и названию
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['rating']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=0) & models.Q(rating__lte=10),
                name="rating_range"
            )
        ]


class Review(models.Model):
    """
    Отзыв пользователя.
    пользователь может оставить только один отзыв.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Автор отзыва"
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Фильм"
    )
    text = models.TextField(
        verbose_name="Текст отзыва",
        help_text="Ваше мнение о фильме"
    )
    rating = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Оценка",
        help_text="Оценка от 1 до 10"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    def __str__(self):
        return f"Отзыв {self.user.username} на {self.movie.title} ({self.rating}/10)"

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ('user', 'movie')  # Один отзыв на фильм от пользователя
        ordering = ['-created_at']


class UserActivity(models.Model):
    """
    История действий пользователя.
    Фиксирует просмотры фильмов и другие активности.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Пользователь"
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Фильм"
    )
    activity_type = models.CharField(
        max_length=50,
        default='view',
        verbose_name="Тип активности",
        help_text="Например: 'view', 'like', 'review'"
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата активности"
    )

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.movie.title}"

    class Meta:
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
        ]