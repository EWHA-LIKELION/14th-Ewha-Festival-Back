from re import S
from rest_framework import serializers
from .models import Show, Setlist, ShowReview, ShowNotice
from utils.abstract_serializers import BaseProgramDetailSerializer, BaseNoticeSerializer, BaseReviewSerializer

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
        fields = tuple(
            f for f in BaseProgramDetailSerializer.Meta.fields
            if f != 'host'
        ) + ('setlist',)

    def get_notice_serializer(self): return ShowNoticeSerializer
    def get_review_serializer(self): return ShowReviewSerializer
    def get_review_model(self): 
        from .models import ShowReview
        return ShowReview