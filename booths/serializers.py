from rest_framework import serializers
from .models import Booth, Product, BoothReview, BoothNotice
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer, ProgramPatchMixin, NestedCollectionPatchMixin, BaseNoticeWriteSerializer
from utils.serializer_fields import ScheduleWriteField
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from utils.exceptions import Conflict

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
        fields = BaseProgramDetailSerializer.Meta.fields + ('host', 'product')

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
            'deleted_product_ids', 'deleted_notice_ids'
        )
        
    def _get_client_version(self):
        request = self.context.get("request")
        if request is None:
            raise RuntimeError("Serializer context에 request가 없습니다. 뷰에서 context={'request': request}를 전달하세요.")

        version = request.headers.get("X-Resource-Version") 
        if not version:
            raise ValidationError({"X-Resource-Version": "동시성 제어를 위해 X-Resource-Version 헤더가 필요합니다."})

        dt = parse_datetime(version)
        if dt is None:
            raise ValidationError({"X-Resource-Version": "올바른 datetime 형식이 아닙니다. (예: 2026-02-19T13:00:00+09:00)"})

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())

        return dt

    def update(self, instance, validated_data):
        touched = False

        products_data = validated_data.pop("product", None)
        notices_data = validated_data.pop("notice", None)
        deleted_product_ids = validated_data.pop("deleted_product_ids", None)
        deleted_notice_ids = validated_data.pop("deleted_notice_ids", None)

        client_updated_at = self._get_client_version()
        now = timezone.now()

        with transaction.atomic():
            booth_update_fields = dict(validated_data)
            booth_update_fields["updated_at"] = now

            updated_rows = Booth.objects.filter(
                pk=instance.pk,
                updated_at=client_updated_at
            ).update(**booth_update_fields)

            if updated_rows == 0:
                latest = Booth.objects.filter(pk=instance.pk).values_list("updated_at", flat=True).first()
                raise Conflict(server_updated_at=timezone.localtime(latest))

            instance = Booth.objects.get(pk=instance.pk)

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
                Booth.objects.filter(pk=instance.pk).update(updated_at=now)
                instance.refresh_from_db(fields=["updated_at"])

        return instance