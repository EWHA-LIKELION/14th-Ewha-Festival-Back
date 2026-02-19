from rest_framework import serializers
from .models import User
from booths.models import Booth, BoothScrap
from shows.models import Show, ShowScrap
from utils.abstract_serializers import BaseManagedProgramSerializer
from booths.serializers import BoothScrapSerializer
from shows.serializers import ShowScrapSerializer

class ManagedBoothSerializer(BaseManagedProgramSerializer):
    class Meta(BaseManagedProgramSerializer.Meta):
        model = Booth

class ManagedShowSerializer(BaseManagedProgramSerializer):
    class Meta(BaseManagedProgramSerializer.Meta):
        model = Show

class MyDataSerializer(serializers.ModelSerializer):
    scrap_count = serializers.IntegerField(source='calculated_scrap_count')
    recent_scraps = serializers.SerializerMethodField()
    managed_booths = serializers.SerializerMethodField()
    managed_shows = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            # 'nickname', # 카카오톡 닉네임은 아직 user 모델에 없으므로 추후 추가 예정
            'scrap_count', 'recent_scraps',
            'managed_booths', 'managed_shows',
        )
    
    def get_scrap_count(self, obj):
        return obj.showscrap.count() + obj.boothscrap.count()
    
    def get_recent_scraps(self, obj):
        shows = obj.showscrap.select_related('show').order_by('-created_at')[:4]
        booths = obj.boothscrap.select_related('booth').order_by('-created_at')[:4]

        combined = sorted(
            list(shows) + list(booths),
            key=lambda x: x.created_at,
            reverse=True
        )[:4]

        serializer_map = {
            ShowScrap: ShowScrapSerializer,
            BoothScrap: BoothScrapSerializer,
        }

        return [
            serializer_map[type(scrap)](scrap, context=self.context).data
            for scrap in combined
        ]
    
    def get_managed_booths(self, obj):
        booths = self.context.get("managed_booths", [])
        return ManagedBoothSerializer(
            booths, many=True, context=self.context
        ).data

    def get_managed_shows(self, obj):
        shows = self.context.get("managed_shows", [])
        return ManagedShowSerializer(
            shows, many=True, context=self.context
        ).data