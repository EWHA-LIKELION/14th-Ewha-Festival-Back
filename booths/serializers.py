from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer
from django.db import transaction

class BoothProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'image', 'is_selling',
        )
        
class BoothProductWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'image', 'is_selling')


class BoothNoticeSerializer(BaseNoticeSerializer):
    class Meta(BaseNoticeSerializer.Meta):
        model = BoothNotice

class BoothNoticeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required = False)
    
    class Meta:
        model = BoothNotice
        fields = ('id', 'title', 'content', 'image')
        
        
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

class BoothPatchSerializer(serializers.ModelSerializer):
    product = BoothProductWriteSerializer(many = True, required = False)
    
    notice = BoothNoticeWriteSerializer(many = True, required = False)
    
    class Meta:
        model = Booth
        fields = (
            'thumbnail', 'name', 'category', 'is_ongoing',
            'description', 'location_description', 'roadview', 'sns',
            'host',
            'product',
            'notice',
        )
        
    def update(self, instance, validated_data):
        products_data = validated_data.pop('product', None)
        notices_data = validated_data.pop('notice', None)
        
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
            
            if notices_data is not None:
                for n in notices_data:
                    notice_id = n.get('id')
                    
                    if notice_id is None:
                        BoothNotice.objects.create(booth=instance, **n)
                        continue
                    
                    qs = instance.booth_notice.filter(id=notice_id)
                    if not qs.exists():
                        raise serializers.ValidationError({
                             "notice": [f"Invalid notice id={notice_id} for this booth."]
                        })
                        
                    obj = qs.first()
                    
                    changed = False
                    for k, v in n.items():
                        if k == 'id': 
                            continue
                        if getattr(obj, k) != v:
                            setattr(obj, k, v)
                            changed = True

                    if changed:
                        obj.save()
                
                
        return instance