from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice

class BoothProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'image', 'is_selling',
        )

class BoothReviewSerializer(serializers.ModelSerializer):
    number = serializers.SerializerMethodField()
    
    class Meta:
        model = BoothReview
        fields = (
            'id', 'content', 'created_at', 'updated_at', 'number',
        )

    def get_number(self, obj):
        return obj.user.number

class BoothNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoothNotice
        fields = (
            'id', 'title', 'content', 'image', 'created_at', 'updated_at',
        )

class BoothDetailSerializer(serializers.ModelSerializer):
    schedule = serializers.SerializerMethodField()
    scraps_count = serializers.IntegerField()
    product = BoothProductSerializer(many=True, read_only=True)
    latest_notice = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = (
            'id', 'thumbnail', 'name', 'is_ongoing', 'description',
            'schedule', 'location', 'location_description', 'roadview', 'sns',
            'category', 'host', 'scraps_count', 'product', 'latest_notice', 'reviews',
        )

    def get_latest_notice(self, obj):
        latest_notice = BoothNotice.objects.filter(booth=obj).order_by('-created_at').first()
        if latest_notice:
            return BoothNoticeSerializer(latest_notice).data
        return None

    def get_reviews(self, obj):
        reviews = BoothReview.objects.filter(user__booth=obj)
        return BoothReviewSerializer(reviews, many=True).data
    
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