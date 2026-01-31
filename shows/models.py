from django.db import models
from django.conf import settings
from utils.abstracts import BaseProgram
from utils.choices import ShowCategoryChoices

# Create your models here.

class Show(BaseProgram):
    thumbnail = models.ImageField(
        help_text="썸네일",
        upload_to="show/thumbnail",
        null=True,
        blank=True,
    )
    category = models.CharField(
        help_text="카테고리",
        max_length=10,
        choices=ShowCategoryChoices.choices,
    )
    roadview = models.ImageField(
        help_text="로드뷰 사진",
        upload_to="show/roadview/",
        null=True,
        blank=True,
    )

class Setlist(models.Model):
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="setlist",
    )
    name = models.CharField(
        help_text="이름",
        max_length=20,
    )

    def __str__(self):
        return f"{self.show.name} - {self.name}"

class ShowNotice(models.Model):
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="show_notice",
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

    def __str__(self):
        return f"{self.show.name} - {self.title}"

class ShowReviewUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="사용자",
        on_delete=models.CASCADE,
        related_name="show_review_user",
    )
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="show_review_user",
    )
    number = models.IntegerField(
        help_text="익명 번호",
    )

    def __str__(self):
        return f"{self.show.name} - 익명 {self.number}"

class ShowReview(models.Model):
    user = models.ForeignKey(
        'ShowReviewUser',
        help_text="공연 후기 작성자",
        on_delete=models.CASCADE,
        related_name="show_review",
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
        return f"{self.user.show.name} - 익명 {self.user.number}"

class ShowScrap(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="사용자",
        on_delete=models.CASCADE,
        related_name="show_scrap",
    )
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="show_scrap",
    )
    created_at = models.DateTimeField(
        help_text="생성일시",
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.user.email} - {self.show.name}"