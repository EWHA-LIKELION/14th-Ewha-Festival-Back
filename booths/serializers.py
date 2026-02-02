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
    scraps_count = serializers.IntegerField()
    products = BoothProductSerializer(many=True, read_only=True, source='product')
    notices = BoothNoticeSerializer(many=True, read_only=True, source='booth_notice')
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Booth
        fields = (
            'id', 'thumbnail', 'name', 'is_ongoing', 'description',
            'schedule', 'location', 'location_description', 'roadview', 'sns',
            'category', 'host', 'scraps_count', 'products', 'notices', 'reviews',
        )

    def get_reviews(self, obj):
        reviews = BoothReview.objects.filter(user__booth=obj)
        return BoothReviewSerializer(reviews, many=True).data