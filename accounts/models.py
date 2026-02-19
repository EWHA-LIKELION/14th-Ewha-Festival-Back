from string import ascii_lowercase, digits
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager

class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    kakao_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    ) 
    nickname = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )
    permission_booth = models.ManyToManyField(
        'booths.Booth',
        help_text="부스 권한",
        related_name="user",
    )
    permission_show = models.ManyToManyField(
        'shows.Show',
        help_text="공연 권한",
        related_name="user",
    )
    objects = UserManager()
    USERNAME_FIELD = 'kakao_id'
    REQUIRED_FIELDS = []
