from django.db.models import TextChoices, IntegerChoices

class ExampleChoices(IntegerChoices):
    """
    예시 코드입니다.
    """
    ONE   = 1, "일"
    TWO   = 2, "이"
    THREE = 3, "삼"

class LocationChoices(TextChoices):
    MAIN_GATE = "MAIN_GATE", "정문"
    GRASS_GROUND = "GRASS_GROUND", "잔디광장"
    SPORT_TRACK = "SPORT_TRACK", "스포츠트랙"
    HYUUT_GIL = "HYUUT_GIL", "휴웃길"
    WELCH_RYANG_AUDITORIUM = "WELCH_RYANG_AUDITORIUM", "대강당"
    EWHA_POSCO_BUILDING = "EWHA_POSCO_BUILDING", "포스코관"
    STUDENT_UNION = "STUDENT_UNION", "학생문화관"
    HUMAN_ECOLOGY_BUILDING = "HUMAN_ECOLOGY_BUILDING", "생활환경관"
    HAK_GWAN = "HAK_GWAN", "학관"
    EDUCATION_BUILDING = "EDUCATION_BUILDING", "교육관"
    EWHA_SHINSEGAE_BUILDING = "EWHA_SHINSEGAE_BUILDING", "신세계관"

class BoothCategoryChoices(TextChoices):
    FOOD = "FOOD", "음식"
    GOODS = "GOODS", "굿즈"
    EXPERIENCE = "EXPERIENCE", "체험"

class BoothHostChoices(TextChoices):
    STUDENT = "STUDENT", "학생"
    COMMITTEE = "COMMITTEE", "축준위"
    SPONSOR = "SPONSOR", "협찬"
    FLEA_MARKET = "FLEA_MARKET", "플리마켓"

class ShowCategoryChoices(TextChoices):
    BAND = "BAND", "밴드"
    DANCE = "DANCE", "댄스"
    THEATER = "THEATER", "연극"