from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from authorization.constants import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей для работы с нашей моделью User.
    Добавляет методы для создания обычного пользователя и суперпользователя.
    """

    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Создает и сохраняет обычного пользователя.

        Args:
            username: Обязательное поле, логин пользователя
            email: Опционально, будет нормализован (приведен к нижнему регистру)
            password: Пароль, который будет хеширован перед сохранением
            extra_fields: Дополнительные поля модели

        Returns:
            User: созданный объект пользователя

        Raises:
            ValueError: если не указан username
        """
        if not username:
            raise ValueError("Необходимо указать имя пользователя")

        if email:
            email = self.normalize_email(email)  # Приводим email к нормальной форме

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        user.set_password(password)  # Хешируем пароль
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Создает суперпользователя с расширенными правами.
        По умолчанию назначает роль ADMIN и выставляет флаги staff/superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", ROLE_ADMIN)

        # Дополнительные проверки для суперпользователя
        if not extra_fields.get("is_staff"):
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Суперпользователь должен иметь is_superuser=True")

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя, заменяющая стандартную django.contrib.auth.models.User.
    Добавляет:
    - Роли пользователей (админ, модератор, обычный пользователь)
    - Аватар
    - Связи с фильмами (избранное) и тегами (предпочтения)
    """

    # Варианты ролей пользователя
    ROLES = (
        (ROLE_ADMIN, 'Администратор'),
        (ROLE_MODERATOR, 'Модератор'),
        (ROLE_USER, 'Пользователь'),
    )

    # Основные поля
    username = models.CharField(
        'Логин',
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Уникальное имя для входа в систему"
    )
    email = models.EmailField(
        'Email',
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="Необязательно, но должно быть уникальным"
    )

    # Права и роли
    role = models.CharField(
        'Роль',
        max_length=20,
        choices=ROLES,
        default=ROLE_USER,
        help_text="Определяет уровень доступа"
    )

    # Персональные данные
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text="Изображение профиля"
    )

    # Связи с другими моделями
    favorite_movies = models.ManyToManyField(
        'movies.Movie',
        related_name='favorited_by',
        blank=True,
        help_text="Фильмы, добавленные в избранное"
    )
    preferred_tags = models.ManyToManyField(
        'movies.Tag',
        blank=True,
        help_text="Предпочитаемые жанры/теги"
    )

    # Технические поля
    is_active = models.BooleanField(
        default=True,
        help_text="Активен ли пользователь (не удален)"
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Может ли заходить в админку"
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Когда зарегистрировался"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда создана запись"
    )

    # Поля для аутентификации
    USERNAME_FIELD = 'username'  # Поле для входа (логин)
    REQUIRED_FIELDS = []  # Доп. поля при createsuperuser

    objects = UserManager()  # Наш кастомный менеджер

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']  # Сортировка по дате создания (новые первые)

    def __str__(self):
        """Строковое представление пользователя"""
        return self.username