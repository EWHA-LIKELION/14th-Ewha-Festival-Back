from rest_framework import serializers
from .models import Show, Setlist, ShowReview, ShowNotice
from utils.abstract_serializers import BaseProgramListSerializer, BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer
    
class ShowListSerializer(BaseProgramListSerializer):
    class Meta(BaseProgramListSerializer.Meta):
        model = Show

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