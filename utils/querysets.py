from typing import Literal
from datetime import datetime, timedelta
from django.db import models
from django.db.models import Q, Count, Value, Case, When, F, Exists, OuterRef, CharField, IntegerField, DateTimeField, BooleanField
from django.db.models.functions import Concat, Cast, Replace, Collate, Coalesce
from django.db.models.expressions import RawSQL
from django.utils.dateparse import parse_date
from .choices import LocationChoices

# 필터링
def base_filter(qs, params, *, program: str):
    q = Q()

    # 종료 제외 (default=ON)
    if params.get("is_ongoing", "true").lower() == "true":
        if program == "booth":
            q &= ~Q(is_ongoing=False)
        elif program == "show":
            q &= ~Q(is_ongoing="AFTER")

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
    dates = [parse_date(d) for d in params.getlist("date") if parse_date(d)]

    if dates:
        if program == "booth":
            range_conditions = " OR ".join(
                "EXISTS(SELECT 1 FROM unnest(schedule) AS r WHERE r && tstzrange(%s, %s, '[)'))"
                for _ in dates
            )
            sql_params = [p for d in dates for p in (
                datetime.combine(d, datetime.min.time()),
                datetime.combine(d, datetime.min.time()) + timedelta(days=1),
            )]
            qs = qs.annotate(
                has_overlap_date=RawSQL(range_conditions, sql_params)
            ).filter(has_overlap_date=True)
            
        elif program == "show":
            date_q = Q()
            for d in dates:
                start = datetime.combine(d, datetime.min.time())
                end = start + timedelta(days=1)
                date_q |= Q(schedule__overlap=(start, end))
            qs = qs.filter(date_q)
    
    return qs

# 정렬
BOOTH_BUILDING_PRIORITY = [
    LocationChoices.HUMAN_ECOLOGY_BUILDING,
    LocationChoices.STUDENT_UNION,
    LocationChoices.EWHA_POSCO_BUILDING,
    LocationChoices.HAK_GWAN,
    LocationChoices.WELCH_RYANG_AUDITORIUM,
    LocationChoices.GRASS_GROUND,
    LocationChoices.EDUCATION_BUILDING,
    LocationChoices.HYUUT_GIL,
    LocationChoices.SENTENNIAL_MUSEUM,
    LocationChoices.SPORT_TRACK,
    LocationChoices.EWHA_SHINSEGAE_BUILDING,
]

def annotate_building_priority(qs):
    whens = [
        When(location__building=building, then=Value(i))
        for i, building in enumerate(BOOTH_BUILDING_PRIORITY)
    ]
    return qs.annotate(
        building_priority_index=Case(
            *whens,
            default=Value(999),
            output_field=IntegerField(),
        )
    )

def base_sort(qs, sorting: str | None, *, program: str):
    sorting = (sorting or "").lower().strip()
    
    # 스크랩순
    if sorting == "scrap":
        qs = annotate_building_priority(qs)
        return qs.order_by("-scraps_count", "building_priority_index", "location__number", "id")
    
    # 이름순
    if sorting == "name":
        name_column = f"{qs.model._meta.db_table}.name"

        qs = qs.annotate(
            name_priority = Case(
                When(name__regex=r'^[가-힣ㄱ-ㅎㅏ-ㅣ]', then=Value(0)),
                When(name__regex=r'^[A-Za-z]', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            name_number=Coalesce(
                Cast(
                    RawSQL(
                        f"NULLIF(regexp_replace({name_column}, '[^0-9]', '', 'g'), '')",
                        ()
                    ),
                    output_field=IntegerField()
                ),
                Value(0),
            ),
            name_text=RawSQL(
                f"regexp_replace({name_column}, '[0-9]', '', 'g')",
                (),
                output_field=CharField(),
            ),
        )
        return qs.order_by(
            "name_priority", 
            Collate("name_text", "ko-KR-x-icu"),
            "name_number", 
            "id"
        )
    
    # 부스 default - 번호순
    if program == "booth" and sorting in ("number", ""):
        qs = annotate_building_priority(qs)
        
        sql_unnest = "(SELECT MIN(lower(r)) FROM unnest(schedule) AS r)"

        return qs.annotate(
            unnest_time=RawSQL(sql_unnest, []),
        ).order_by("building_priority_index", "location__number", "unnest_time", "id")

    # 공연 default - 시간순
    if program == "show" and sorting in ("time", ""):
        return qs.annotate(
            unnest_time=RawSQL("lower(schedule)", (), output_field=DateTimeField())
        ).order_by("unnest_time", "id")

    return qs

class FilterSortQuerySet(models.QuerySet):
    def with_name_no_space(self):
        return self.annotate(
            name_no_space=Replace(
                F('name'),
                Value(' '),
                Value(''),
            )
        )
    
    def with_building_label(self):
        return self.with_name_no_space().annotate(
            building_label=Case(
                *[
                    When(location__building=choice, then=Value(label))
                    for choice, label in LocationChoices.choices
                ],
                default=Value(""),
                output_field=CharField(),
                ),
            ).annotate(
                full_location=Concat(
                    "building_label",
                    Cast("location__number", CharField()),
                    output_field=CharField(),
                )
            )

    def with_location(self):
        return self.select_related(
            "location"
        )
    
    def with_scraps_count(self, *, program: str):
        if program == "booth":
            return self.annotate(
                scraps_count=Count("booth_scrap", distinct=True)
            )     
        elif program == "show":
            return self.annotate(
                scraps_count=Count("show_scrap", distinct=True)
            )
        
        return self

    def with_is_scraped(self, user, program:Literal['booth','show']):
        from django.apps import apps

        if program == 'booth':
            scrap_model = apps.get_model('booths', 'BoothScrap')
        elif program == 'show':
            scrap_model = apps.get_model('shows', 'ShowScrap')

        if user.is_authenticated:
            return self.annotate(
                is_scraped=Exists(
                    scrap_model.objects.filter(
                        **{program: OuterRef('pk')},
                        user=user
                    )
                )
            )
        else:
            return self.annotate(
                is_scraped=Value(False, output_field=BooleanField())
            )

    def filter_and_sort(self, params, *, program: str):
        qs = base_filter(self, params, program=program)
        return base_sort(qs, params.get("sorting"), program=program)