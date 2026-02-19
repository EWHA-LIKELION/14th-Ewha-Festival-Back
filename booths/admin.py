from django.contrib import admin
from .models import Booth, BoothNotice, Product, BoothReviewUser, BoothReview, BoothScrap

admin.site.register(Booth)
admin.site.register(BoothNotice)
admin.site.register(Product)
admin.site.register(BoothReviewUser)
admin.site.register(BoothReview)
admin.site.register(BoothScrap)
