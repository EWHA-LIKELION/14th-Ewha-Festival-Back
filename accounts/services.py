from typing import Literal
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from booths.models import Booth
from shows.models import Show

User = get_user_model()

class JWTService:
    def refresh(self, old_refresh_token:str)->tuple[str,str]:
        # 1. 서명·만료·blacklist 검증
        try:
            old_token = RefreshToken(old_refresh_token)  
        except TokenError:
            raise

        # 2. 페이로드에서 user_id 추출 후 유저 조회
        try:
            user_id = old_token.payload.get("user_id")
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise

        # 3. 기존 Refresh Token blacklist 등록 (Rotation)
        try:
            old_token.blacklist()
        except Exception:
            raise

        # 4. User 기반으로 새 토큰 쌍 발급
        new_refresh = RefreshToken.for_user(user)
        new_access_token = str(new_refresh.access_token)
        new_refresh_token = str(new_refresh)

        return new_access_token, new_refresh_token

class PermissionService:
    def __init__(self, request:HttpRequest, pk:int|None=None):
        self.request = request
        self.pk = pk

    def validate(self, kind:Literal["booth","show"], password:str)->bool:
        if kind == "booth":
            model_cls = Booth
        elif kind == "show":
            model_cls =Show

        obj = get_object_or_404(model_cls, pk=self.pk)
        return obj.check_admincode(password), obj

    def add_permission(self, kind:Literal["booth","show"], obj:Booth|Show):
        user_permission_field = getattr(self.request.user, f"permission_{kind}")
        user_permission_field.add(obj)
