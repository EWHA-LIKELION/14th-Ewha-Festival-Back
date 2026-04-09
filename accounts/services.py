from django.http import HttpRequest

class PermissionService:
    def __init__(self, request:HttpRequest, pk:int|None=None):
        self.request = request
        self.pk = pk

    def _add_permission(self):
        # 해당 사용자 계정 인스턴스의 권한 필드를 수정한다.
        # 그 권한 필드에 부스/공연 인스턴스의 PK를 저장한다.

    def booth(self, password:str, day_list:list[str], location:str, number:str):
        # 부스 테이블에서 “부스 번호”에 해당하는 인스턴스를 가져온다.
        # “부스 번호”에 대한 “관리자 코드”가 일치하는지 검증한다.
        # 일치하지 않으면 예외 처리
        # 일치하면 사용자에게 권한을 추가한다.

    def show(self, password:str, day_list:list[str], schedule_start:str, location:str):
        # 공연 테이블에서 “공연 번호”에 해당하는 인스턴스를 가져온다.
        # “공연 번호”에 대한 “관리자 코드”가 일치하는지 검증한다.
        # 일치하지 않으면 예외 처리
        # 일치하면 사용자에게 권한을 추가한다.
