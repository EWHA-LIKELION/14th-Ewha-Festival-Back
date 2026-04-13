from django.db import models
from django.db.models import BooleanField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce

class BoothManager(models.Manager):
    def get_queryset(self):
        check_schedule = RawSQL("Now() @> ANY(schedule)")

        return super().get_queryset().annotate(
            is_ongoing=Coalesce(
                models.F('ongoing'),
                check_schedule,
                output_field=BooleanField()
            )
        )
