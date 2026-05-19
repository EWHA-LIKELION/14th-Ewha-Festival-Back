from utils.choices import LocationChoices
from .models import Booth

EARLY_CLOSING_BUILDINGS = (
    LocationChoices.GRASS_GROUND,
    LocationChoices.SENTENNIAL_MUSEUM,
    LocationChoices.SPORT_TRACK,
    LocationChoices.WELCH_RYANG_AUDITORIUM,
)

class BoothService:
    def reset_all(self):
        """모든 부스의 ongoing을 Null로 초기화"""
        updated_booths = Booth.objects.update(ongoing=None)
        return updated_booths

    def reset_early_closing_buildings(self):
        """잔디광장, 박물관, 스포츠트랙, 대강당 부스의 ongoing을 Null로 초기화"""
        updated_booths = (
            Booth.objects
            .filter(location__building__in=EARLY_CLOSING_BUILDINGS)
            .update(ongoing=None)
        )
        return updated_booths
