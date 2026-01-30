from django.contrib import admin
from .models import Show, Setlist, ShowNotice, ShowReviewUser, ShowReview, ShowScrap

# Register your models here.

admin.site.register(Show)
admin.site.register(Setlist)
admin.site.register(ShowNotice)
admin.site.register(ShowReviewUser)
admin.site.register(ShowReview)
admin.site.register(ShowScrap)