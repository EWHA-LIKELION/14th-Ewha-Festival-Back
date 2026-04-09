from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied
from booths.models import Booth
from shows.models import Show

class PermissionService:
    def __init__(self, request:HttpRequest, pk:int|None=None):
        self.request = request
        self.pk = pk

    def booth(self, password:str):
        # 부스 테이블에서 “부스 번호”에 해당하는 인스턴스를 가져온다.
        booth = Booth.objects.get(pk=self.pk)
        # “부스 번호”에 대한 “관리자 코드”가 일치하는지 검증한다.
        # 일치하지 않으면 예외 처리
        if not booth.check_admincode(password):
            raise PermissionDenied(detail="관리자 코드가 올바르지 않아요.")
        # 일치하면 사용자에게 권한을 추가한다.
        # 해당 사용자 계정 인스턴스의 권한 필드에 부스/공연 인스턴스의 PK를 저장한다.
        self.request.user.permission_booth.add(booth)

    def show(self, password:str):
        # 공연 테이블에서 “공연 번호”에 해당하는 인스턴스를 가져온다.
        show = Show.objects.get(pk=self.pk)
        # “공연 번호”에 대한 “관리자 코드”가 일치하는지 검증한다.
        # 일치하지 않으면 예외 처리
        if not show.check_admincode(password):
            raise PermissionDenied(detail="관리자 코드가 올바르지 않아요.")
        # 일치하면 사용자에게 권한을 추가한다.
        # 해당 사용자 계정 인스턴스의 권한 필드에 부스/공연 인스턴스의 PK를 저장한다.
        self.request.user.permission_show.add(show)
