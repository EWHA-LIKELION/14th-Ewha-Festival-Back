from django.db.models import Q, Case, When, Value, IntegerField
from django.db.models.expressions import RawSQL
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_date
from .choices import LocationChoices

# 필터링
def base_filter(qs, params, *, program: str):
    q = Q()

    # 종료 제외 (default=ON)
    if params.get("is_ongoing", "true").lower() == "true":
        if program == "booth":
            q &= Q(is_ongoing=True)
        elif program == "show":
            now = timezone.now()
            qs = qs.annotate(
                has_not_ended=RawSQL(
                    """
                    EXISTS(
                        SELECT 1
                        FROM unnest(schedule) AS r
                        WHERE upper(r) > %s
                    )
                    """,
                    [now],
                )
            ).filter(has_not_ended=True)