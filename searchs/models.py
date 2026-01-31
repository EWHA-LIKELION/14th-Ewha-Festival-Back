from django.db import models
from utils.choices import LocationChoices

# Create your models here.

class Location(models.Model):
    building = models.CharField(
        help_text = "위치",
        max_length=50,
        choices=LocationChoices.choices,
    )
    number = models.IntegerField(
        help_text="부스 번호/공연 시작 시각"
    )

    def __str__(self):
        return f"{self.building}{self.number}"