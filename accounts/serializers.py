from rest_framework import serializers
from .models import User
from booths.models import Booth
from shows.models import Show, ShowScrap
from utils.abstract_serializers from BaseManagedProgramSerializer
from booths.serializers import BoothScrapSerializer
from shows.serializers import ShowScrapSerializer

class ManagedBoothSerializer(BaseManagedProgramSerializer):
    class Meta(BaseManagedProgramSerializer.Meta):
        model = Booth

class ManagedShowSerializer(BaseManagedProgramSerializer):
    class Meta(BaseManagedProgramSerializer.Meta):
        model = Show

class MyDataSerializer(serializers.ModelSerializer):
    scrap_count = serializers.SerializerMethodField()
    recent_scraps = serializers.SerializerMethodField()
    managed_booths = ManagedBoothSerializer(many=True, read_only=True)
    managed_shows = ManagedShowSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            # 'nickname', # 카카오톡 닉네임은 아직 user 모델에 없으므로 추후 추가 예정
            'scrap_count', 'recent_scraps',
            'managed_booths', 'managed_shows',
        )
    
    def get_scrap_count(self, obj):
        scrap_count = obj.show_scrap.count() + obj.booth_scrap.count()
        return scrap_count
    
    def get_recent_scraps(self, obj):
        shows = obj.show_scrap.select_related('show').order_by('-created_at')[:4]
        booths = obj.booth_scrap.select_related('booth').order_by('-created_at')[:4]

        combined = sorted(
            list(shows) + list(booths),
            key=lambda x: x.created_at,
            reverse=True
        )[:4]

        return [
            ShowScrapSerializer(scrap).data
            if isinstance(scrap, ShowScrap)
            else BoothScrapSerializer(scrap).data
            for scrap in combined
        ]