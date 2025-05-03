from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from authorization.constants import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER





class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if email:
            email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", ROLE_ADMIN)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        (ROLE_ADMIN, 'Администратор'),
        (ROLE_MODERATOR, 'Модератор'),
        (ROLE_USER, 'Пользователь'),
    )

    username = models.CharField('Логин', max_length=255, unique=True, db_index=True)
    email = models.EmailField('Email', max_length=255, unique=True, blank=True, null=True)
    role = models.CharField('Роль', max_length=20, choices=ROLES, default=ROLE_USER)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    favorite_movies = models.ManyToManyField('movies.Movie', related_name='favorited_by', blank=True)
    preferred_tags = models.ManyToManyField('movies.Tag', blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return self.username


