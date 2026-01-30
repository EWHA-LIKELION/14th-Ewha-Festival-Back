from django.db import models
from booths.models import BaseProgram
from utils.choices import ShowCategoryChoices

# Create your models here.

class Show(BaseProgram):
    category = models.CharField(
        help_text="카테고리",
        max_length=10,
        choices=ShowCategoryChoices.choices,
    )