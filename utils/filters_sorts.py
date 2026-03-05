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

    # 카테고리
    category = params.getlist("category")
    if category:
        if program == "booth":
            q &= Q(category__overlap=category)
        else:
            q &= Q(category__in=category)

    # 위치
    location = params.getlist("building")
    if location:
        q &= Q(location__building__in=location)
    
    # 주관 (booth만)
    if program == "booth":
        host = params.getlist("host")
        if host:
            q &= Q(host__in=host)

    # 요일
    qs = qs.filter(q)

    d = parse_date(params.get("date") or "")
    if d:
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)

        qs = qs.annotate(
            has_overlap_date=RawSQL(
                """
                EXISTS(
                    SELECT 1
                    FROM unnest(schedule) AS r
                    WHERE r && tstzrange(%s, %s, '[)')
                )
                """,
                [start, end],
            )
        ).filter(has_overlap_date=True)
    
    return qs