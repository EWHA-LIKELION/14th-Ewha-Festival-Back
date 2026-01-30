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

class Setlist(models.Model):
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="setlist",
    )

    def __str__(self):
        return f"{self.show.name} - {self.name}"