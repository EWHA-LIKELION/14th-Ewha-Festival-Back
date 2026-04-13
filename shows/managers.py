from django.db import models
from django.db.models import Case, When, Value, CharField
from django.db.models.functions import Now

class ShowManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            is_ongoing=Case(
                # 스케줄의 시작(lower)이 현재 시각보다 클 때
                When(schedule__fully_gt=Now(), then=Value("BEFORE")),
                # 현재 시각이 스케줄 범위 안에 포함될 때
                When(schedule__contains=Now(), then=Value("DURING")),
                # 스케줄의 종료(upper)가 현재 시각보다 작을 때
                When(schedule__fully_lt=Now(), then=Value("AFTER")),
                output_field=CharField()
            )
        )
