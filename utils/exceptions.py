from rest_framework.exceptions import APIException

class Conflict(APIException):
    status_code = 409
    default_detail = "최근 업데이트 전 정보를 보고 있습니다. 새로고침하여 최근 업데이트 내역을 확인하고 업데이트해 주십시오."
    default_code = "conflict"