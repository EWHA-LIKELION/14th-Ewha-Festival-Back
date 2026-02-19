from django.shortcuts import render
import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from urllib.parse import urlencode

# Create your views here.
User = get_user_model()

class KakaoLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = {
            "client_id": settings.KAKAO_REST_API_KEY,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code",
        }

        kakao_auth_url = "https://kauth.kakao.com/oauth/authorize?" + urlencode(params)
        return redirect(kakao_auth_url)
    
class KakaoCallbackView(APIView):
    def get(self, request):
        code = request.GET.get("code")

        #access_token 요청
        token_response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_REST_API_KEY,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code": code,
                "client_secret": settings.KAKAO_CLIENT_SECRET, 
            },
        )

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        #사용자 정보 요청
        profile_response = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        profile_json = profile_response.json()

        kakao_id = profile_json["id"]
        user, created = User.objects.get_or_create(
            kakao_id=str(kakao_id),
            defaults={
                "nickname": profile_json.get("properties", {}).get("nickname")
            }
        )

        #JWT 발급 
        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })