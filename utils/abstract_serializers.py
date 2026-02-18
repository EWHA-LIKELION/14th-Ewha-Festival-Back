from rest_framework import serializers
from utils.helpers import time_ago
from searchs.serializers import LocationSerializer

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

class BaseScrapSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    scrap_field = ""

    class Meta:
        abstract = True
        fields = (
            'id', 'name', 'thumbnail',
        )

    def get_target(self, obj):
        return getattr(obj, self.scrap_field)
    
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
    latest_notice = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = (
            'id', 'thumbnail', 'name', 'category', 'is_ongoing', 'scraps_count',
            'description', 'location', 'location_description', 'roadview',
            'schedule', 'sns', 'latest_notice', 'reviews',
        )

    def get_schedule(self, obj):
        result = []

        for r in obj.schedule:
            start = r.lower
            end = r.upper

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

class BaseManagedProgramSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    scrap_count = serializers.IntegerField()
    review_count = serializers.IntegerField()

    class Meta:
        fields = (
            "id", "name",
            "scrap_count", "review_count",
        )