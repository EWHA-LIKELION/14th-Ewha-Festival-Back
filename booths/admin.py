from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField
from django.contrib.postgres.forms.ranges import DateTimeRangeField as FormDateTimeRangeField

from .models import Booth, BoothNotice, Product, BoothReviewUser, BoothReview, BoothScrap


class BoothAdminForm(forms.ModelForm):
    # ✅ ArrayField delimiter를 콤마(,)가 아니라 세미콜론(;)로 바꿔서
    # range 내부의 콤마와 충돌을 피함
    schedule = SimpleArrayField(
        base_field=FormDateTimeRangeField(),
        delimiter=';',
        required=False,
    )

    class Meta:
        model = Booth
        fields = "__all__"


class BoothAdmin(admin.ModelAdmin):
    form = BoothAdminForm


# ✅ 기존 register(Booth) 대신 커스텀 admin으로 등록
admin.site.register(Booth, BoothAdmin)

# 나머지는 그대로
admin.site.register(BoothNotice)
admin.site.register(Product)
admin.site.register(BoothReviewUser)
admin.site.register(BoothReview)
admin.site.register(BoothScrap)
