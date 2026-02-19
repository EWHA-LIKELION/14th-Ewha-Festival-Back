from rest_framework.exceptions import APIException

class Conflict(APIException):
    status_code = 409
    default_detail = "최근 업데이트 전 정보를 보고 있습니다. 새로고침하여 최근 업데이트 내역을 확인하고 업데이트해 주십시오."
    default_code = "conflict"

    def __init__(self, server_updated_at=None, detail=None, code=None):
        if detail is None:
            detail = self.default_detail

        if server_updated_at:
            detail = {
                "detail": detail,
                "server_updated_at": server_updated_at.isoformat()
                if hasattr(server_updated_at, "isoformat")
                else server_updated_at,
            }

        super().__init__(detail=detail, code=code)
