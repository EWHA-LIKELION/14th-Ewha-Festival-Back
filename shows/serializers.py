from rest_framework import serializers
from rest_framework import serializers
from .models import Show, Setlist, ShowNotice
from utils.abstract_serializers import ProgramPatchMixin, NestedCollectionPatchMixin, BaseNoticeWriteSerializer, BasePatchSerializer, CollectionPatchSpec
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
