from rest_framework import serializers
from utils.helpers import time_ago
from searchs.serializers import LocationSerializer
from django.utils import timezone
from dataclasses import dataclass
from typing import Optional, Type, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from utils.exceptions import Conflict


class BaseNoticeSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()
    is_updated = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = (
            'id', 'title', 'content', 'image', 'time_ago', 'is_updated',
        )

    def get_time_ago(self, obj):
        return time_ago(obj.created_at)

    def get_is_updated(self, obj):
        return obj.updated_at != obj.created_at

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

class BaseProgramDetailSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    schedule = serializers.SerializerMethodField()
    scraps_count = serializers.IntegerField()
    latest_notice = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = (
            'id', 'thumbnail', 'name', 'category', 'is_ongoing', 'scraps_count',
            'description', 'location', 'location_description', 'roadview',
            'schedule', 'sns', 'latest_notice', 'reviews', 'updated_at',
        )

    def get_schedule(self, obj):
        result = []
        tz = timezone.get_current_timezone()

        for r in obj.schedule:
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
    
class BaseNoticeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required = False)
    
    class Meta:
        fields = ('id', 'title', 'content', 'image')

class ProgramPatchMixin:
    program_fields = (
        'thumbnail', 'name', 'is_ongoing', 'description',
        'location_description', 'roadview', 'sns', 'schedule',
    )

    def get_root_update_fields(self, validated_data):
        return {k: v for k, v in validated_data.items() if k in self.program_fields}

    
    
class NestedCollectionPatchMixin:
    def patch_collection(
        self,
        *,
        instance,
        items_data,
        deleted_ids,
        manager_name: str,      # 예: "product", "booth_notice", "show_notice", "setlist"
        model_cls,              # Product / BoothNotice / ShowNotice / Setlist
        parent_fk_name: str,    # "booth" / "show"
        serializer_class,
        items_field_name: str,   # 예: "product" / "notice" / "setlist"
        deleted_field_name: str  # 예: "deleted_product_ids" / "deleted_notice_ids" ...
    ) -> bool:
        """
        items_data: list[dict] or None
        deleted_ids: list[int] or None
        return: touched(bool)
        """
        touched = False
        manager = getattr(instance, manager_name, None)
        if manager is None:
            raise NotImplementedError(f"Invalid manager_name: {manager_name}")

        # upsert
        if items_data is not None:
            for item in items_data:
                item_id = item.get("id")

                if item_id is None:
                    s = serializer_class(data=item, context=self.context)
                    try:
                        s.is_valid(raise_exception=True)
                    except serializers.ValidationError as e:
                        raise serializers.ValidationError({items_field_name: e.detail})

                    
                    payload = dict(s.validated_data)
                    payload[parent_fk_name] = instance
                    model_cls.objects.create(**payload)
                    touched = True
                    continue

                obj = manager.filter(id=item_id).first()
                if obj is None:
                    raise serializers.ValidationError({
                        items_field_name: [f"{item_id} is not in this resource."]
                    })
                
                s = serializer_class(obj, data=item, partial=True, context=self.context)
                s.is_valid(raise_exception=True)
                s.save()
                touched = True

        # delete
        if deleted_ids is not None:
            ids = set(deleted_ids)
            found = set(manager.filter(id__in=ids).values_list("id", flat=True))
            missing = ids - found
            if missing:
                raise serializers.ValidationError({
                    deleted_field_name: [f"Invalid ids: {sorted(missing)}"]
                })
            manager.filter(id__in=ids).delete()
            touched = True

        return touched
    
@dataclass(frozen=True)
class CollectionPatchSpec:
    items_field_name: str          # payload 키: "product" / "notice" / "playlist"
    deleted_field_name: Optional[str]  # payload 키: "deleted_product_ids" ...
    manager_name: str              # instance의 related manager attr: "product" / "booth_notice"
    model_cls: Type[Any]
    parent_fk_name: str            # FK 필드명: "booth" / "program"
    serializer_class: Type[serializers.Serializer]

    
class BasePatchSerializer(serializers.ModelSerializer):
    version_header_name = "X-Resource-Version"
    
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

    def update(self, instance, validated_data):
        specs = self.get_collection_specs()

        nested_map = {}
        deleted_map = {}

        for spec in specs:
            nested_map[spec.items_field_name] = validated_data.pop(spec.items_field_name, None)
            if spec.deleted_field_name:
                deleted_map[spec.deleted_field_name] = validated_data.pop(spec.deleted_field_name, None)

        client_version = self._get_client_version()
        now = timezone.now()
        version_field = self.get_version_field_name()

        with transaction.atomic():
            root_fields = self.get_root_update_fields(validated_data)
            root_fields[version_field] = now

            updated_rows = self.Meta.model.objects.filter(  # type: ignore
                pk=instance.pk,
                **{version_field: client_version},
            ).update(**root_fields)

            if updated_rows == 0:
                latest = self._get_latest_version(instance.pk)
                raise Conflict(server_updated_at=latest)

            instance = self.Meta.model.objects.get(pk=instance.pk)  

            touched = False
            for spec in specs:
                items_data = nested_map.get(spec.items_field_name)
                deleted_ids = deleted_map.get(spec.deleted_field_name) if spec.deleted_field_name else None

                touched |= self.patch_collection(
                    instance=instance,
                    items_data=items_data,
                    deleted_ids=deleted_ids,
                    manager_name=spec.manager_name,
                    model_cls=spec.model_cls,
                    parent_fk_name=spec.parent_fk_name,
                    serializer_class=spec.serializer_class,
                    items_field_name=spec.items_field_name,
                    deleted_field_name=spec.deleted_field_name or "",
                )

            if touched and self.should_bump_updated_at():
                self.Meta.model.objects.filter(pk=instance.pk).update(**{version_field: timezone.now()})
                instance.refresh_from_db(fields=[version_field])

        return instance