import logging
from utils.choices import LocationChoices
from .models import Booth

logger = logging.getLogger(__name__)

EARLY_CLOSING_BUILDINGS = (
    LocationChoices.GRASS_GROUND,
    LocationChoices.SENTENNIAL_MUSEUM,
    LocationChoices.SPORT_TRACK,
    LocationChoices.WELCH_RYANG_AUDITORIUM,
)

class BoothService:
    @staticmethod
    def reset_all():
        """모든 부스의 ongoing을 Null로 초기화"""
        updated_booths = Booth.objects.update(ongoing=None)
        logger.info(f"[BoothService] 전체 부스 총 {updated_booths}개 ongoing 초기화 완료")

    @staticmethod
    def reset_early_closing_buildings():
        """잔디광장, 박물관, 스포츠트랙, 대강당 부스의 ongoing을 Null로 초기화"""
        updated_booths = (
            Booth.objects
            .filter(location__building__in=EARLY_CLOSING_BUILDINGS)
            .update(ongoing=None)
        )
        logger.info(f"[BoothService] 잔디광장·박물관·스포츠트랙·대강당 부스 총 {updated_booths}개 ongoing 초기화 완료")
