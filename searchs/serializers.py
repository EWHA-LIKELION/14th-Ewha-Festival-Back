from rest_framework import serializers
from utils.abstract_serializers import BaseProgramListSerializer
from booths.models import Booth

class BoothSearchSerializer(BaseProgramListSerializer):
    class Meta(BaseProgramListSerializer.Meta):
        model = Booth