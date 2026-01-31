from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from utils.abstracts import BaseProgram, BaseNotice, BaseReviewUser, BaseReview, BaseScrap
from utils.choices import BoothCategoryChoices, BoothHostChoices

# Create your models here.

class Booth(BaseProgram):
    category = ArrayField(
        help_text="카테고리",
        base_field=models.CharField(
            max_length=10,
            choices=BoothCategoryChoices.choices,
        ),
        default=list,
    )
    host = models.CharField(
        help_text = "주관",
        max_length = 20,
        choices = BoothHostChoices.choices,
    )

class BoothNotice(BaseNotice):
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="booth_notice",
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
        upload_to="product/image",
        null=True,
        blank=True,
        )
    is_selling = models.BooleanField(
        help_text="판매중 여부",
    )

    def __str__(self):
        return f"{self.booth.name} - {self.name}"

class BoothReviewUser(BaseReviewUser):
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="booth_review_user",
    )

    def __str__(self):
        return f"{self.booth.name} - 익명 {self.number}"
    
class BoothReview(BaseReview):
    user = models.ForeignKey(
        'BoothReviewUser',
        help_text="부스 후기 작성자",
        on_delete=models.CASCADE,
        related_name="booth_review",
    )

    def __str__(self):
        return f"{self.user.booth.name} - 익명 {self.user.number}"
    
class BoothScrap(BaseScrap):
    booth = models.ForeignKey(
        'Booth',
        help_text="부스",
        on_delete=models.CASCADE,
        related_name="booth_scrap",
    )

    def __str__(self):
        return f"{self.user.email} - {self.booth.name}"