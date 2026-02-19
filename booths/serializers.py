from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice, BoothScrap
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer, BaseScrapSerializer

class BoothProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'image', 'is_selling',
        )

class BoothNoticeSerializer(BaseNoticeSerializer):
    class Meta(BaseNoticeSerializer.Meta):
        model = BoothNotice

class BoothReviewSerializer(BaseReviewSerializer):
    class Meta(BaseReviewSerializer.Meta):
        model = BoothReview

class BoothScrapSerializer(BaseScrapSerializer):
    scrap_field = "booth"

    class Meta(BaseScrapSerializer.Meta):
        model = BoothScrap

class BoothDetailSerializer(BaseProgramDetailSerializer):
    product = serializers.SerializerMethodField()

    class Meta(BaseProgramDetailSerializer.Meta):
        model = Booth
        fields = BaseProgramDetailSerializer.Meta.fields + ('host', 'product',)

    def get_product(self, obj):
        products = obj.product.filter(is_selling=True)
        return BoothProductSerializer(products, many=True).data

    def get_notice_serializer(self): return BoothNoticeSerializer
    def get_review_serializer(self): return BoothReviewSerializer
    def get_review_model(self): 
        from .models import BoothReview
        return BoothReview