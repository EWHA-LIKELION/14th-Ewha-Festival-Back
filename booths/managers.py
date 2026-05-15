from django.db import models
from django.db.models import BooleanField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce
from utils.querysets import FilterSortQuerySet

class BoothManager(models.Manager.from_queryset(FilterSortQuerySet)):
    def get_queryset(self):
        check_schedule = RawSQL("EXISTS(SELECT 1 FROM unnest(schedule) r WHERE r @> NOW())", ())

        return super().get_queryset().annotate(
            is_ongoing=Coalesce(
                models.F('ongoing'),
                check_schedule,
                output_field=BooleanField()
            )
        )
