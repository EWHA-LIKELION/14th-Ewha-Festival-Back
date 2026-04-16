from rest_framework import serializers
from utils.abstract_serializers import BaseProgramListSerializer
from booths.models import Booth, BoothScrap
from shows.models import Show, ShowScrap

class BoothSearchSerializer(BaseProgramListSerializer):
    is_ongoing = serializers.BooleanField(read_only=True)

    class Meta(BaseProgramListSerializer.Meta):
        model = Booth

    def get_scrap_model(self):
        return BoothScrap

class ShowSearchSerializer(BaseProgramListSerializer):
    is_ongoing = serializers.CharField(read_only=True)

    class Meta(BaseProgramListSerializer.Meta):
        model = Show

    def get_scrap_model(self):
        return ShowScrap
