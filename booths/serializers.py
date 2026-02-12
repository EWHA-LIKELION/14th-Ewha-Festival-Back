from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer

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

class BoothPatchSerializer(serializrs.ModelSerialzier):
    product = BoothProductSerializer(many = True, required = False)
    
    class Meta:
        model = Booth
        fields = (
            'thumbnail', 'name', 'category', 'is_ongoing',
            'description', 'location_description', 'roadview', 'sns',
            'host', 'product',
        )
        
    def update(self, instance, validated_data):
        products_data = validated_data.pip('product', None)
        
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            if products_data is not None:
                for p in products_data:
                    product_id = p.get('id', None)
                    
                    if product_id is None:
                        Product.objects.create(booth=instance, **p)
                        continue
                
                # 이 booth의 product인지 확인
                qs = instance.product.filter(id=product_id)
                if not qs.exists():
                    raise serializers.ValidationError({
                        "product": [f"Invalid product id = {product_id} for this booth."]
                    })
                    
                obj = qs.first()
                for k, v in p.items():
                    if k == 'id':
                        continue
                    setattr(obj, k, v)
                obj.save()
                
        return instance