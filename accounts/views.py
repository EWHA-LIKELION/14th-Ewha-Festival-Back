from django.http import HttpRequest
from django.db.models import Count, F
from django.db import IntegrityError
from .models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import logging
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from urllib.parse import urlencode
from .serializers import MyDataSerializer

from booths.models import Booth, BoothScrap
from shows.models import Show, ShowScrap
from searchs.views import search

# Create your views here.

User = get_user_model()
logger = logging.getLogger(__name__)

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
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code")
        #인가코드 없는 경우 
        if not code:
            return Response(
                {"message": "인가 코드가 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        if token_response.status_code != 200:
            return Response(
                {
                    "message": "Access token 발급 실패",
                    "error": token_response.json(),
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        #access_token 없는 경우
        if not access_token:
            return Response(
                {"message": "Access token이 응답에 존재하지 않습니다."},
                status=HTTP_401_UNAUTHORIZED
            )
        
        #사용자 정보 요청
        profile_response = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        #사용자 정보 요청 실패 
        if profile_response.status_code != 200:
            return Response(
                {"message": "사용자 정보 요청 실패"},
                status=HTTP_401_UNAUTHORIZED
            )

        profile_json = profile_response.json()

        kakao_id = profile_json.get("id")
        #kakao_id 없는 경우
        if not kakao_id:
            return Response(
                {"message": "카카오 사용자 ID가 존재하지 않습니다."},
                status=HTTP_401_UNAUTHORIZED
            )
        try:
            user, _ = User.objects.get_or_create(
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
        
        except IntegrityError:
            return Response(
                {"message": "사용자 생성 중 DB 오류 발생"}, 
                status=HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"카카오 로그인 오류: {e}") 
            return Response(
                {"message": "서버 내부 오류 발생"},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

class MyDataView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request:HttpRequest, format=None):
        user = User.objects.annotate(
            show_count=Count("showscrap", distinct=True),
            booth_count=Count("boothscrap", distinct=True),
            calculated_scrap_count=F("show_count") + F("booth_count"),
        ).get(pk=request.user.pk)

        booths = user.permission_booth.annotate(
            scrap_count=Count("booth_scrap", distinct=True),
            review_count=Count("booth_review_user", distinct=True),
        ).order_by("name")

        shows = user.permission_show.annotate(
            scrap_count=Count("show_scrap", distinct=True),
            review_count=Count("show_review_user", distinct=True),
        ).order_by("name")

        serializer = MyDataSerializer(
            user,
            context={"request": request, "managed_booths": booths, "managed_shows": shows},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

class MyScrapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        booths_qs = (
            Booth.objects.select_related("location")
            .prefetch_related("product")
            .filter(id__in=BoothScrap.objects.filter(user=request.user).values("booth_id"))
        )
        shows_qs = (
            Show.objects.select_related("location")
            .filter(id__in=ShowScrap.objects.filter(user=request.user).values("show_id"))
        )
        result = search(
            request=request,
            booths_qs=booths_qs,
            shows_qs=shows_qs,
        )
        return Response(
            result,
            status=status.HTTP_200_OK,
        )