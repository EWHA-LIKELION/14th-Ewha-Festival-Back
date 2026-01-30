from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField
from django_nanoid.models import NANOIDField
from django.conf import settings
from utils.choices import LocationChoices, BoothCategoryChoices, BoothHostChoices

# Create your models here.

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
    schedule = models.ArrayField(
        help_text="시간",
        base_field=models.DateTimeRangeField(),
        default=list,
    )
    location = models.ForeignKey(
        "Location",
        on_delete=models.PROTECT,
    )
    location_description = models.CharField(
        help_text="위치 설명",
        max_length=50,
        null=True,
        blank=True,
    )
    sns = models.ArrayField(
        help_text="SNS 링크",
        base_field=models.URLField(),
        size=2,
        null=True,
        blank=True,
        default=list,
    )
    admin_code = NANOIDField(
        help_text="관리자 인증 코드",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class Location(models.Model):
    building = models.CharField(
        help_text = "위치",
        max_length=50,
        choices=LocationChoices.choices,
    )
    number = models.IntegerField(
        help_text="부스 번호/공연 시작 시각"
    )

    def __str__(self):
        return f"{self.building} - {self.number}"

class Booth(BaseProgram):
    thumbnail = models.ImageField(
        help_text="썸네일",
        null=True,
        blank=True,
        upload_to="booth/thumbnail/",
    )
    cateory = models.CharField(
        help_text = "카테고리",
        max_length=10,
        choices = BoothCategoryChoices.choices,
    )
    roadview = models.ImageField(
        help_text="로드뷰 사진",
        null=True,
        blank=True,
        upload_to="booth/roadview/",
    )
    host = models.CharField(
        help_text = "주관",
        max_length = 10,
        choices = BoothHostChoices.choices,
    )

class BoothNotice(models.Model):
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="booth_notice",
    )
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
        upload_to="booth_notice/image/",
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

    def __str__(self):
        return f"{self.booth.name} - {self.title}"
    
class Product(models.Model):
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="product",
    )
    name = models.CharField(
        help_text="이름",
        max_length=20,
    )
    description = models.CharField(
        help_text="설명",
        max_length=200,
        null=True,
        blank=True,
    )
    price = models.IntegerField(
        help_text="가격",
    )
    image = models.ImageField(
        help_text="사진",
        upload_to="product/image/",
        null=True,
        blank=True,
        )
    is_selling = models.BooleanField(
        help_text="판매중 여부",
    )

    def __str__(self):
        return f"{self.booth.name} - {self.name}"


class BoothReviewUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="사용자",
        on_delete=models.CASCADE,
        related_name="booth_review_user",
    )
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="booth_review_user",
    )
    number = models.IntegerField(
        help_text="익명 번호",
    )

    def __str__(self):
        return f"{self.booth.name} - 익명 {self.number}"
    
class BoothReview(models.Model):
    user = models.ForeignKey(
        'BoothReviewUser',
        help_text="부스 후기 작성자",
        on_delete=models.CASCADE,
        related_name="booth_review",
    )
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

    def __str__(self):
        return f"{self.user.booth.name} - 익명 {self.user.number}"
    
class BoothScrap(models.model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="사용자",
        on_delete=models.CASCADE,
        related_name="booth_scrap",
    )
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="booth_scrap",
    )
    created_at = models.DateTimeField(
        help_text="생성일시",
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.user.email} - {self.booth.name}"