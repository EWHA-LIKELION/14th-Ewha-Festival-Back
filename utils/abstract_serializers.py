from rest_framework import serializers
from utils.helpers import time_ago
from searchs.serializers import LocationSerializer
from django.utils import timezone


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
            start = timezone.localtime(r.lower, tz)
            end = timezone.localtime(r.upper, tz)

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

    def update_program_fields(self, instance, validated_data):
        changed = False
        for field in self.program_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
                changed = True

        if changed:
            instance.save()
        return instance
    
    
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
    

