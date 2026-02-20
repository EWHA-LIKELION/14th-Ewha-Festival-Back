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

# 정렬
BOOTH_BUILDING_PRIORITY = [
    LocationChoices.HUMAN_ECOLOGY_BUILDING,
    LocationChoices.STUDENT_UNION,
    LocationChoices.HAK_GWAN,
    LocationChoices.EWHA_POSCO_BUILDING,
    LocationChoices.MAIN_GATE,
    LocationChoices.WELCH_RYANG_AUDITORIUM,
    LocationChoices.HYUUT_GIL,
    LocationChoices.EDUCATION_BUILDING,
    LocationChoices.EWHA_SHINSEGAE_BUILDING,
    LocationChoices.SPORT_TRACK,
]

def base_sort(qs, sorting: str | None, *, program: str):
    sorting = (sorting or "").lower().strip()
    
    # 스크랩순
    if sorting == "scrap":
        return qs.order_by("-scraps_count", "id")
    
    # 이름순
    if sorting == "name":
        return qs.order_by("name", "id")
    
    # 부스 default - 번호순
    if program == "booth" and sorting in ("number", ""):
        whens = [
            When(location__building=building, then=Value(i))
            for i, building in enumerate(BOOTH_BUILDING_PRIORITY)
        ]

        sql_unnest = "(SELECT MIN(lower(r)) FROM unnest(schedule) AS r)"

        return qs.annotate(
            building_priority_index=Case(
                *whens,
                default=Value(999),
                output_field=IntegerField(),
            ),
            unnest_time=RawSQL(sql_unnest, []),
        ).order_by("building_priority_index", "location__number", "unnest_time", "id")

    # 공연 default - 시간순
    if program == "show" and sorting in ("time", ""):
        sql_unnest = "(SELECT MIN(lower(r)) FROM unnest(schedule) AS r)"
        return qs.annotate(
            unnest_time=RawSQL(sql_unnest, [])
        ).order_by("unnest_time", "id")
        
    return qs

def filter_and_sort(qs, params, *, program: str):
    qs = base_filter(qs, params, program=program)
    return base_sort(qs, params.get("sorting"), program=program)