from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice
from searchs.serializers import LocationSerializer
from utils.helpers import time_ago

class BoothProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'image', 'is_selling',
        )

class BoothReviewSerializer(serializers.ModelSerializer):
    number = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = BoothReview
        fields = (
            'id', 'number', 'content', 'time_ago',
        )

    def get_number(self, obj):
        return obj.user.number

    def get_time_ago(self, obj):
        return time_ago(obj.created_at) 

class BoothNoticeSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()
    is_updated = serializers.SerializerMethodField()

    class Meta:
        model = BoothNotice
        fields = (
            'id', 'title', 'content', 'image', 'time_ago', 'is_updated',
        )

    def get_time_ago(self, obj):
        return time_ago(obj.created_at)

    def get_is_updated(self, obj):
        return obj.updated_at != obj.created_at

class BoothDetailSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    schedule = serializers.SerializerMethodField()
    scraps_count = serializers.IntegerField()
    product = serializers.SerializerMethodField()
    latest_notice = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = (
            'id', 'thumbnail', 'name', 'category', 'host', 'is_ongoing', 'scraps_count',
            'description', 'location', 'location_description', 'roadview',
            'schedule', 'sns', 'latest_notice', 'product', 'reviews',
        )

    def get_schedule(self, obj):
        result = []

        for r in obj.schedule:
            start = r.lower
            end = r.upper

            result.append({
                "date": start.strftime("%m.%d"),
                "time": f"{start.strftime('%H:%M')}~{end.strftime('%H:%M')}",
            })

        return result

    def get_latest_notice(self, obj):
        latest_notice = BoothNotice.objects.filter(booth=obj).order_by('-created_at').first()
        if latest_notice:
            return BoothNoticeSerializer(latest_notice).data
        return None

    def get_product(self, obj):
        products = obj.product.filter(is_selling=True)
        return BoothProductSerializer(products, many=True).data

    def get_reviews(self, obj):
        reviews = BoothReview.objects.filter(user__booth=obj)
        return BoothReviewSerializer(reviews, many=True).data