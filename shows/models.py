from django.db import models
from django.conf import settings
from utils.abstracts import BaseProgram, BaseNotice, BaseReviewUser, BaseReview, BaseScrap
from utils.choices import ShowCategoryChoices

# Create your models here.

class Show(BaseProgram):
    category = models.CharField(
        help_text="카테고리",
        max_length=10,
        choices=ShowCategoryChoices.choices,
    )

class ShowNotice(BaseNotice):
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="show_notice",
    )

    def __str__(self):
        return f"{self.show.name} - {self.title}"

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

class ShowReviewUser(BaseReviewUser):
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="show_review_user",
    )

    def __str__(self):
        return f"{self.show.name} - 익명 {self.number}"

class ShowReview(BaseReview):
    user = models.ForeignKey(
        'ShowReviewUser',
        help_text="공연 후기 작성자",
        on_delete=models.CASCADE,
        related_name="show_review",
    )

    def __str__(self):
        return f"{self.user.show.name} - 익명 {self.user.number}"

class ShowScrap(BaseScrap):
    show = models.ForeignKey(
        'Show',
        help_text="공연",
        on_delete=models.CASCADE,
        related_name="show_scrap",
    )

    def __str__(self):
        return f"{self.user.email} - {self.show.name}"