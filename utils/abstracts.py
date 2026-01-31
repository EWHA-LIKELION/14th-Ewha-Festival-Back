from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, DateTimeRangeField
from django_nanoid.models import NANOIDField
from string import ascii_uppercase, digits

def get_thumbnail_path(instance, filename):
    class_name = instance.__class__.__name__.lower()
    return f"{class_name}/thumbnail/{filename}"
    
def get_roadview_path(instance, filename):
    class_name = instance.__class__.__name__.lower()
    return f"{class_name}/roadview/{filename}"

def get_notice_image_path(instance, filename):
    class_name = instance.__class__.__name__.lower()
    return f"{class_name}/{filename}"

class BaseProgram(models.Model):
    id = models.CharField(
        help_text="예시:BOOTH_RELEASE",
        primary_key=True,
        max_length=20,
    )
    thumbnail = models.ImageField(
        help_text="썸네일",
        upload_to=get_thumbnail_path,
        null=True,
        blank=True,
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
    roadview = models.ImageField(
        help_text="로드뷰 사진",
        upload_to=get_roadview_path,
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

class BaseNotice(models.Model):
    title = models.CharField(
        help_text="제목",
        max_length=20,
    )
    content = models.CharField(
        help_text="내용",
        max_length=200,
    )
    image = models.ImageField(
        help_text="사진",
        upload_to="show_notice/image/",
        null=True,
        blank=True,
        )
    created_at = models.DateTimeField(
        help_text="생성일시",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        help_text="수정일시",
        auto_now=True,
    )

    class Meta:
        abstract = True

class BaseReviewUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="사용자",
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )
    number = models.IntegerField(
        help_text="익명 번호",
    )

    class Meta:
        abstract = True

class BaseReview(models.Model):
    content = models.TextField(
        help_text="내용",
    )
    created_at = models.DateTimeField(
        help_text="생성일시",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        help_text="수정일시",
        auto_now=True,
    )

    class Meta:
        abstract = True