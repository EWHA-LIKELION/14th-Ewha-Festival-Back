from django.db import models
from django.contrib.postgres.fields import ArrayField, DateTimeRangeField
from django_nanoid.models import NANOIDField
from string import ascii_uppercase, digits

class BaseProgram(models.Model):
    id = models.CharField(
        help_text="예시:BOOTH_RELEASE",
        primary_key=True,
        max_length=20,
    )
    name = models.CharField(
        help_text="이름",
        max_length=20
    )
    is_ongoing = models.BooleanField(
        help_text="운영중 여부",
    )
    description = models.CharField(
        help_text="소개글",
        max_length=200,
        null=True,
        blank=True,
    )
    schedule = ArrayField(
        help_text="시간",
        base_field=DateTimeRangeField(),
        default=list,
    )
    location = models.ForeignKey(
        "booths.Location",
        help_text="위치",
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )
    location_description = models.CharField(
        help_text="위치 설명",
        max_length=50,
        null=True,
        blank=True,
    )
    sns = ArrayField(
        help_text="SNS 링크",
        base_field=models.URLField(),
        size=2,
        null=True,
        blank=True,
        default=list,
    )
    admin_code = NANOIDField(
        help_text="관리자 인증 코드",
        editable=False,
        alphabetically=ascii_uppercase+digits,
        size=10,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name