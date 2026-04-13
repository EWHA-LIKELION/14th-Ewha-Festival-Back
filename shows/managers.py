from django.db import models
from django.db.models import Case, When, Value, CharField
from django.db.models.expressions import RawSQL

class ShowManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            is_ongoing=Case(
                When(
                    condition=RawSQL("lower(schedule) > NOW()", []),
                    then=Value("BEFORE"),
                ),
                When(
                    condition=RawSQL("schedule @> NOW()", []),
                    then=Value("DURING"),
                ),
                When(
                    condition=RawSQL("upper(schedule) < NOW()", []),
                    then=Value("AFTER"),
                ),
                output_field=CharField(),
            )
        )
