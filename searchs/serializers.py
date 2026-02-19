from utils.abstract_serializers import BaseProgramListSerializer
from booths.models import Booth
from shows.models import Show

class BoothSearchSerializer(BaseProgramListSerializer):
    class Meta(BaseProgramListSerializer.Meta):
        model = Booth
    
class ShowSearchSerializer(BaseProgramListSerializer):
    class Meta(BaseProgramListSerializer.Meta):
        model = Show
