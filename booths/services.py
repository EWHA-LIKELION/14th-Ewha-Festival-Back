from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Booth

class BoothService:
    def __init__(self, booth_model:Booth):
        self.booth_model = booth_model

    def reset_all(self):
        """모든 부스의 ongoing을 Null로 초기화"""
        updated_booths = self.booth_model.objects.update(ongoing=None)
        return updated_booths
