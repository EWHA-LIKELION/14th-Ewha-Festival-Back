from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer, ProgramPatchMixin, NestedCollectionPatchMixin, BaseNoticeWriteSerializer
from utils.serializer_fields import ScheduleWriteField
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

class BoothNoticeWriteSerializer(BaseNoticeWriteSerializer):
    class Meta(BaseNoticeWriteSerializer.Meta):
        model = BoothNotice
        
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

class BoothPatchSerializer(ProgramPatchMixin, NestedCollectionPatchMixin, serializers.ModelSerializer):
    product = BoothProductWriteSerializer(many = True, required = False)
    notice = BoothNoticeWriteSerializer(many = True, required = False)
    schedule = ScheduleWriteField(required=False)
    
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

            products_data = validated_data.pop("product", None)
            notices_data = validated_data.pop("notice", None)
            deleted_product_ids = validated_data.pop("deleted_product_ids", None)
            deleted_notice_ids = validated_data.pop("deleted_notice_ids", None)

            with transaction.atomic():
                self.update_program_fields(instance, validated_data)

                touched |= self.patch_collection(
                    instance=instance,
                    items_data=products_data,
                    deleted_ids=deleted_product_ids,
                    manager_name="product",
                    model_cls=Product,
                    parent_fk_name="booth",
                    serializer_class=BoothProductWriteSerializer,
                    items_field_name="product",
                    deleted_field_name="deleted_product_ids",
                )

                touched |= self.patch_collection(
                    instance=instance,
                    items_data=notices_data,
                    deleted_ids=deleted_notice_ids,
                    manager_name="booth_notice",
                    model_cls=BoothNotice,
                    parent_fk_name="booth",
                    serializer_class=BoothNoticeWriteSerializer,
                    items_field_name="notice",
                    deleted_field_name="deleted_notice_ids",
                )

                if touched:
                    instance.save(update_fields=["updated_at"])

            return instance