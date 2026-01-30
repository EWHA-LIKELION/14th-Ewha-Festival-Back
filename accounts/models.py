from string import ascii_lowercase, digits
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager

class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(
        unique=True,
        error_messages={'unique': '이미 존재하는 이메일입니다.'},
    )
    permission_booth = models.ManyToManyField(
        'booths.Booth',
        help_text="부스 권한",
        related_name="user",
        null=True,
        blank=True,
    )
    permission_show = models.ManyToManyField(
        'shows.Show',
        help_text="공연 권한",
        related_name="user",
        null=True,
        blank=True,
    )
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
