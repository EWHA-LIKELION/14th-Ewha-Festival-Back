from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer, ProgramPatchMixin
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
        fields = BaseProgramDetailSerializer.Meta.fields + ('host', 'product','updated_at')

    def get_product(self, obj):
        products = obj.product.filter(is_selling=True)
        return BoothProductSerializer(products, many=True).data

    def get_notice_serializer(self): return BoothNoticeSerializer
    def get_review_serializer(self): return BoothReviewSerializer
    def get_review_model(self): 
        from .models import BoothReview
        return BoothReview

class BoothPatchSerializer(ProgramPatchMixin, serializers.ModelSerializer):
    product = BoothProductWriteSerializer(many = True, required = False)
    notice = BoothNoticeWriteSerializer(many = True, required = False)
    
    deleted_product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required = False
    )
    deleted_notice_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required = False
    )
    class Meta:
        model = Booth
        fields = (
            'thumbnail', 'name', 'category', 'is_ongoing',
            'description', 'location_description', 'roadview', 'sns',
            'host',
            'product',
            'notice',
            'schedule',
            'deleted_product_ids', 'deleted_notice_ids',
        )
        
    def update(self, instance, validated_data):
        touched = False
        
        products_data = validated_data.pop('product', None)
        notices_data = validated_data.pop('notice', None)
        
        deleted_product_ids = validated_data.pop('deleted_product_ids', None)
        deleted_notice_ids = validated_data.pop('deleted_notice_ids', None)
        
        with transaction.atomic():
            self.update_program_fields(instance, validated_data)
            
            if products_data is not None:
                for p in products_data:
                    product_id = p.get('id', None)
                    
                    if product_id is None:
                        Product.objects.create(booth=instance, **p)
                        touched = True
                        continue
                
                    qs = instance.product.filter(id=product_id)
                    if not qs.exists():
                        raise serializers.ValidationError({
                            "product": [f"{product_id} 번 상품은 이 부스에 속하지 않습니다."]
                        })
                
                    
                    obj = qs.first()
                    for k, v in p.items():
                        if k == 'id':
                            continue
                        setattr(obj, k, v)
                    obj.save()
                    touched = True
                    
            if deleted_product_ids is not None:
                ids = set(deleted_product_ids)
                found = set(instance.product.filter(id__in=ids).values_list('id', flat=True))
                missing = ids - found
                if missing:
                    raise serializers.ValidationError({"deleted_product_ids": [f"이 부스에 속하지 않는 상품 ID: {sorted(missing)}"]})
                instance.product.filter(id__in=ids).delete()
                touched = True
            
            if notices_data is not None:
                for n in notices_data:
                    notice_id = n.get('id')
                    
                    if notice_id is None:
                        BoothNotice.objects.create(booth=instance, **n)
                        touched = True
                        continue
                    

                    obj = instance.booth_notice.filter(id=notice_id).first()
                    if obj is None:
                        raise serializers.ValidationError({
                            "notice": [f"{notice_id}번 공지는 이 부스에 속하지 않습니다."]
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
                        touched = True
                        
            if deleted_notice_ids is not None:
                ids = set(deleted_notice_ids)
                found = set(instance.booth_notice.filter(id__in=ids).values_list('id', flat=True))
                missing = ids - found
                if missing:
                    raise serializers.ValidationError({"deleted_notice_ids": [f"이 부스에 속하지 않는 공지 ID: {sorted(missing)}"]})
                instance.notice.filter(id__in=ids).delete()
                touched = True

            if touched:
                instance.save(update_fields=["updated_at"])

                
                
        return instance