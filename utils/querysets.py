from django.db import models
from django.db.models import Count, Value, CharField, Case, When, F
from django.db.models.functions import Concat, Cast, Replace
from utils.choices import LocationChoices
from .filters_sorts import base_filter, base_sort

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
                When(location__building=LocationChoices.GRASS_GROUND, then=Value("잔디광장")),
                When(location__building=LocationChoices.SENTENNIAL_MUSEUM, then=Value("박물관")),
                When(location__building=LocationChoices.SPORT_TRACK, then=Value("스포츠트랙")),
                When(location__building=LocationChoices.HYUUT_GIL, then=Value("휴웃길")),
                When(location__building=LocationChoices.WELCH_RYANG_AUDITORIUM, then=Value("대강당")),
                When(location__building=LocationChoices.EWHA_POSCO_BUILDING, then=Value("포스코관")),
                When(location__building=LocationChoices.STUDENT_UNION, then=Value("학생문화관")),
                When(location__building=LocationChoices.HUMAN_ECOLOGY_BUILDING, then=Value("생활환경관")),
                When(location__building=LocationChoices.HAK_GWAN, then=Value("학관")),
                When(location__building=LocationChoices.EDUCATION_BUILDING, then=Value("교육관")),
                When(location__building=LocationChoices.EWHA_SHINSEGAE_BUILDING, then=Value("신세계관")),
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
        
        if program == "show":
            return self.annotate(
                scraps_count=Count("show_scrap", distinct=True)
            )
        
        return self
    
    def filter_and_sort(self, params, *, program: str):
        qs = base_filter(self, params, program=program)
        return base_sort(qs, params.get("sorting"), program=program)