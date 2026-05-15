from django.db import models
from django.db.models import CharField
from django.db.models.expressions import RawSQL
from utils.querysets import FilterSortQuerySet

class ShowManager(models.Manager.from_queryset(FilterSortQuerySet)):
    def get_queryset(self):
        return super().get_queryset().annotate(
            is_ongoing=RawSQL(
                """
                CASE
                    WHEN lower(schedule) > NOW() THEN 'BEFORE'
                    WHEN schedule @> NOW()       THEN 'DURING'
                    WHEN upper(schedule) < NOW() THEN 'AFTER'
                    ELSE NULL
                END
                """,
                [],
                output_field=CharField(),
            )
        )
