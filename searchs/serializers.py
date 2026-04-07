from rest_framework import serializers
from utils.abstract_serializers import BaseProgramListSerializer
from booths.models import Booth, BoothScrap
from shows.models import Show, ShowScrap

class BoothSearchSerializer(BaseProgramListSerializer):
    class Meta(BaseProgramListSerializer.Meta):
        model = Booth
    
    def get_scrap_model(self):
        return BoothScrap

class ShowSearchSerializer(BaseProgramListSerializer):
    class Meta(BaseProgramListSerializer.Meta):
        model = Show

    def get_scrap_model(self):
        return ShowScrap