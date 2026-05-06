from django.db import models
from utils.choices import LocationChoices

class Location(models.Model):
    building = models.CharField(
        help_text = "위치",
        max_length=50,
        choices=LocationChoices.choices,
    )
    number = models.IntegerField(
        help_text="부스 번호",
        null=True, # 공연은 number 필드가 Null인 레코드를 참조한다.
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['building','number'],
                name='unique_building_number',
            )
        ]
        ordering = ['building','number']

    def __str__(self):
        return f"{LocationChoices(self.building).label} {self.number if self.number else '공연'}"
