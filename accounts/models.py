from django.db import models
from string import ascii_lowercase, digits
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(
        unique = True,
        error_messages = {'unique': '이미 존재하는 이메일입니다.'}
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []