from rest_framework import serializers
from utils.helpers import time_ago
from .location_serializers import LocationSerializer
from dataclasses import dataclass
from typing import Optional, Type, List, Dict, Any
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from rest_framework.exceptions import ValidationError
import json

class JsonParsingMixin:
    def to_internal_value(self, data):
        if hasattr(data, 'getlist'):
            plain = {}
            for key in data.keys():
                vals = data.getlist(key)
                plain[key] = vals[0] if len(vals) == 1 else vals
            data = plain
        elif hasattr(data, 'copy'):
            data = data.copy()

        json_fields = getattr(self.Meta, 'json_fields', [])

        for field in json_fields:
            if field in data:
                value = data.get(field)
                if value and isinstance(value, str):
                    try:
                        data[field] = json.loads(value)
                    except (json.JSONDecodeError, TypeError) as e:
                         raise serializers.ValidationError({
                            field: f"올바른 JSON 형식이 아닙니다. (에러: {str(e)})"
                            })

        return super().to_internal_value(data)
    
class BaseNoticeSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()
    is_updated = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = (
            'id', 'title', 'content', 'time_ago', 'is_updated',
        )

    def get_time_ago(self, obj):
        return time_ago(obj.created_at)

    def get_is_updated(self, obj):
        if obj.created_at is None or obj.updated_at is None:
            return False
        return (obj.updated_at - obj.created_at) > timedelta(seconds=1)

class BaseReviewSerializer(serializers.ModelSerializer):
    number = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = (
            'id', 'number', 'content', 'time_ago',
        )

    def get_number(self, obj):
        return obj.user.number
    
    def get_time_ago(self, obj):
        return time_ago(obj.created_at)

class BaseScrapSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    target_id = serializers.SerializerMethodField()
    scrap_field = ""

    class Meta:
        abstract = True
        fields = (
            'id', 'target_id', 'name', 'thumbnail',
        )

    def get_target(self, obj):
        return getattr(obj, self.scrap_field)

    def get_target_id(self, obj):
        return getattr(obj, f"{self.scrap_field}_id")
    
    def get_name(self, obj):
        return self.get_target(obj).name

    def get_thumbnail(self, obj):
        target = self.get_target(obj)
        thumbnail = target.thumbnail

        if thumbnail:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(thumbnail.url)
            return thumbnail.url

        return None

class BaseProgramDetailSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    schedule = serializers.SerializerMethodField()
    scraps_count = serializers.IntegerField()
    is_scraped = serializers.SerializerMethodField()
    latest_notice = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    sns = serializers.ListField(
        child=serializers.CharField(allow_blank=True, allow_null=True),
        required=False
    )

    class Meta:
        abstract = True
        fields = (
            'id', 'thumbnail', 'name', 'category', 'is_ongoing', 'scraps_count', 'is_scraped',
            'description', 'location', 'location_description', 'roadview',
            'schedule', 'sns', 'latest_notice', 'reviews', 'updated_at',
        )

    def get_is_scraped(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        
        scrap_model = self.get_scrap_model()
        model_name = obj._meta.model_name
        return scrap_model.objects.filter(
            user=request.user,
            **{model_name: obj}
        ).exists()

    def get_schedule(self, obj):
        if not obj or not obj.schedule:
            return []

        if isinstance(obj.schedule, list):
            raw_schedules = obj.schedule
        else:
            raw_schedules = [obj.schedule]

        result = []
        
        for r in raw_schedules:
            if r is None:
                continue
                
            start = timezone.localtime(r.lower)
            end = timezone.localtime(r.upper)

            result.append({
                "date": start.strftime("%m.%d"),
                "time": f"{start.strftime('%H:%M')}~{end.strftime('%H:%M')}",
            })

        return result
    
    def get_latest_notice(self, obj):
        model_name = obj._meta.model_name
        notice_set = getattr(obj, f"{model_name}_notice", None)
        
        if notice_set:
            latest = notice_set.order_by('-created_at').first()
            if latest:
                return self.get_notice_serializer()(latest).data
        return None
    
    def get_reviews(self, obj):
        model_name = obj._meta.model_name
        reviews = self.get_review_model().objects.filter(**{f"user__{model_name}": obj})
        return self.get_review_serializer()(reviews, many=True).data
    
    def get_notice_serializer(self): raise NotImplementedError
    def get_review_serializer(self): raise NotImplementedError
    def get_review_model(self): raise NotImplementedError
    def get_scrap_model(self): raise NotImplementedError
    
class BaseProgramListSerializer(BaseProgramDetailSerializer):
    product_images = serializers.SerializerMethodField()

    class Meta(BaseProgramDetailSerializer.Meta):
        fields = (
            "id",
            "name",
            "is_ongoing",
            "category",
            "schedule",
            "location",
            "scraps_count",
            "is_scraped",
            "description",
            "thumbnail",
            "product_images",
        )

    def get_product_images(self, obj):

        if not hasattr(obj, "product"):
            return []

        products = obj.product.all().order_by("id")[:3]

        product_images = []
        for p in products:
            product_images.append(p.image.url if p.image else None)
        return product_images

class BaseNoticeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required = False)
    
    class Meta:
        fields = ('id', 'title', 'content')

class ProgramPatchMixin:
    program_fields = (
        'thumbnail', 'name', 'is_ongoing', 'description',
        'location_description', 'roadview', 'sns', 'schedule',
    )

    def get_root_update_fields(self, validated_data):
        return {k: v for k, v in validated_data.items() if k in self.program_fields}
    
    
@dataclass(frozen=True)
class CollectionPatchSpec:
    items_field_name: str          # payload 키: "product" / "notice" / "playlist"
    deleted_field_name: Optional[str]  # payload 키: "deleted_product_ids" ...
    manager_name: str              # instance의 related manager attr: "product" / "booth_notice"
    model_cls: Type[Any]
    parent_fk_name: str            # FK 필드명: "booth" / "program"
    serializer_class: Type[serializers.Serializer]

    
class BasePatchSerializer(JsonParsingMixin, serializers.ModelSerializer):
    
    version_header_name = "X-Resource-Version"
    
    sns = serializers.ListField(
        child=serializers.CharField(allow_blank=True, allow_null=True),
        required=False
    )
    
    nullable_string_fields = ('thumbnail', 'roadview')

    def to_internal_value(self, data):
        null_sentinels = {'null', 'None', '', 'undefined'}
        if any(data.get(f) in null_sentinels for f in self.nullable_string_fields if f in data):
            mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
            for f in self.nullable_string_fields:
                if f in mutable_data and mutable_data[f] in null_sentinels:
                    mutable_data[f] = None
            return super().to_internal_value(mutable_data)
        return super().to_internal_value(data)
    
    def get_collection_specs(self) -> List[CollectionPatchSpec]:
        return []
    
    def get_version_field_name(self) -> str:
        return "updated_at"
    
    def get_root_update_fields(self, validated_data: Dict[str, Any]) -> Dict[str,Any]:
        return dict(validated_data)
    
    def should_bump_updated_at(self) -> bool:
        return True
    
    def _get_client_version(self):
        request = self.context.get("request")
        if request is None:
            raise RuntimeError("Serializer context에 request가 없습니다. view에서 context={'request': request} 전달 필요.")

        version = request.headers.get(self.version_header_name)
        if not version:
            raise ValidationError({self.version_header_name: "동시성 제어를 위해 X-Resource-Version 헤더가 필요합니다."})

        dt = parse_datetime(version)
        if dt is None:
            raise ValidationError({self.version_header_name: "올바른 datetime 형식이 아닙니다. (ISO-8601)"} )

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())

        return dt

    def _get_latest_version(self, pk):
        vf = self.get_version_field_name()
        return self.Meta.model.objects.filter(pk=pk).values_list(vf, flat=True).first()  # type: ignore



class BaseManagedProgramSerializer(serializers.ModelSerializer):
    scrap_count = serializers.IntegerField()
    review_count = serializers.IntegerField()

    class Meta:
        fields = (
            "id", "name",
            "scrap_count", "review_count",
        )
