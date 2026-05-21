from rest_framework.response import Response
from rest_framework_simplejwt.settings import api_settings

def response_jwt_cookie(status:int, detail:str, access_token:str, refresh_token:str)->Response:
    response = Response(
        status=status,
        data={"detail": detail},
    )
    response.set_cookie(
        key="access",
        value=access_token,
        max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
        secure=True,
        httponly=True,
        samesite="None",
    )
    response.set_cookie(
        key="refresh",
        value=refresh_token,
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
        secure=True,
        httponly=True,
        samesite="None",
    )
    return response
