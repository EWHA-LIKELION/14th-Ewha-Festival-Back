from rest_framework import serializers
from .models import Show, Setlist, ShowNotice, ShowReview
from utils.abstract_serializers import ProgramPatchMixin, NestedCollectionPatchMixin, BaseNoticeWriteSerializer, BasePatchSerializer, CollectionPatchSpec, BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer
from utils.serializer_fields import ScheduleWriteField

class SetlistWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required = False)
    
    class Meta:
        model = Setlist
        fields = (
            'id', 'name'
        )

class ShowNoticeWriteSerializer(BaseNoticeWriteSerializer):
    class Meta(BaseNoticeWriteSerializer.Meta):
        model = ShowNotice
        
class ShowPatchSerializer(
    BasePatchSerializer,           
    ProgramPatchMixin,              
    NestedCollectionPatchMixin,
    serializers.ModelSerializer,
):
    setlist = SetlistWriteSerializer(many=True, required=False)
    notice = ShowNoticeWriteSerializer(many=True, required=False)
    schedule = ScheduleWriteField(required=False)

    deleted_setlist_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    deleted_notice_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = Show 
        fields = (
            "thumbnail", "name", "category", "is_ongoing", "description", "schedule",
            "location_description", "roadview", "sns",
            # nested
            "setlist",
            "notice",
            "deleted_setlist_ids",
            "deleted_notice_ids",
        )

    def get_collection_specs(self):
        return [
            CollectionPatchSpec(
                items_field_name="setlist",
                deleted_field_name="deleted_setlist_ids",
                manager_name="setlist",          
                model_cls=Setlist,               
                parent_fk_name="show",           
                serializer_class=SetlistWriteSerializer,
            ),
            CollectionPatchSpec(
                items_field_name="notice",
                deleted_field_name="deleted_notice_ids",
                manager_name="show_notice",      
                model_cls=ShowNotice,            
                parent_fk_name="show",          
                serializer_class=ShowNoticeWriteSerializer,
            ),
        ]

class ShowSetlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setlist
        fields = (
            'id', 'name',
        )

class ShowNoticeSerializer(BaseNoticeSerializer):
    class Meta(BaseNoticeSerializer.Meta):
        model = ShowNotice

class ShowReviewSerializer(BaseReviewSerializer):
    class Meta(BaseReviewSerializer.Meta):
        model = ShowReview

class ShowDetailSerializer(BaseProgramDetailSerializer):
    setlist = ShowSetlistSerializer(many=True)

    class Meta(BaseProgramDetailSerializer.Meta):
        model = Show
        fields = BaseProgramDetailSerializer.Meta.fields + ('setlist',)

    def get_notice_serializer(self): return ShowNoticeSerializer
    def get_review_serializer(self): return ShowReviewSerializer
    def get_review_model(self): 
        from .models import ShowReview
        return ShowReview