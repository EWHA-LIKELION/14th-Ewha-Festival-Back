from .models import Booth

class BoothService:
    def reset_all(self):
        """모든 부스의 ongoing을 Null로 초기화"""
        updated_booths = Booth.objects.update(ongoing=None)
        return updated_booths
