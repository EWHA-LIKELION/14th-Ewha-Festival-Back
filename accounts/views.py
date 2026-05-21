from django.core.cache import cache
from django.http import HttpRequest
from django.db.models import Count, F
from django.db import IntegrityError
from .models import User
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import logging
from django.conf import settings
from django.shortcuts import redirect 
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from urllib.parse import urlencode
from .serializers import MyDataSerializer, PermissionSerializer
from .services import JWTService, PermissionService

from utils.constants import Cachekey
from utils.helpers import get_user_id, calc_params_hash
from booths.models import Booth, BoothScrap
from shows.models import Show, ShowScrap
from searchs.views import search

# Create your views here.

User = get_user_model()
logger = logging.getLogger(__name__)

class KakaoLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        state = request.query_params.get("state", "prod")

        params = {
            "client_id": settings.KAKAO_REST_API_KEY,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code",
            "state": state, 
        }

        kakao_auth_url = "https://kauth.kakao.com/oauth/authorize?" + urlencode(params)
        return redirect(kakao_auth_url)
    
class KakaoCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        #프론트 테스트용 분기(삭제 예정) 
        FRONT_URLS = settings.KAKAO_FRONT_REDIRECT_URL
        state = request.query_params.get("state")

        if state == "local":
            front_url = FRONT_URLS[0]
        else:
            front_url = FRONT_URLS[1]
    
        code = request.query_params.get("code")
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
                status=status.HTTP_401_UNAUTHORIZED
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
                status=status.HTTP_401_UNAUTHORIZED
            )

        profile_json = profile_response.json()

        kakao_id = profile_json.get("id")
        #kakao_id 없는 경우
        if not kakao_id:
            return Response(
                {"message": "카카오 사용자 ID가 존재하지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED
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

            response = redirect(front_url)
            #response = redirect(f"{settings.KAKAO_FRONT_REDIRECT_URL}")

            response.set_cookie(
                "access",
                str(refresh.access_token),
                httponly=True,
                samesite="None",
                secure=True,
            )
            response.set_cookie(
                "refresh",
                str(refresh),
                httponly=True,
                samesite="None",
                secure=True,
            )
            return response

        
        except IntegrityError:
            return Response(
                {"message": "사용자 생성 중 DB 오류 발생"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"카카오 로그인 오류: {e}") 
            return Response(
                {"message": "서버 내부 오류 발생"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class KakaoLogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        response = Response(
            {"message": "로그아웃 성공"},
            status=status.HTTP_200_OK
        )
        
        response.delete_cookie("access")
        response.delete_cookie("refresh")

        return response

class Refresh(APIView):
    permission_classes = [AllowAny]

    def post(self, request:HttpRequest, format=None):
        old_refresh_token = request.COOKIES.get("refresh")
        if not old_refresh_token:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={"detail": "Refresh Token이 없어요."},
            )

        jwt_service = JWTService()

        try:
            new_access_token, new_refresh_token = jwt_service.refresh(old_refresh_token=old_refresh_token)
        except TokenError:
            raise Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={"detail": "유효하지 않은 Refresh Token이에요."},
            )
        except User.DoesNotExist:
            raise Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"detail": "존재하지 않는 사용자예요."},
            )
        except Exception:
            raise Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"detail": "토큰 무효화 중 오류가 발생했어요."},
            )

        response = Response(
            status=status.HTTP_200_OK,
            data={"detail": "토큰을 재발급했어요."},
        )
        response.set_cookie("access", new_access_token, httponly=True, samesite="None", secure=True)
        response.set_cookie("refresh", new_refresh_token, httponly=True, samesite="None", secure=True)
        return response

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
        cache_key = Cachekey.SCRAP_LIST.format(
            user_id=get_user_id(request.user),
            params_hash=calc_params_hash(request.query_params)
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(
                status=status.HTTP_200_OK,
                data=cached
            )

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

        cache.set(cache_key, result, 60*3)

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

class Permission(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request:HttpRequest, format=None):
        # 요청 수신, 요청값 검증
        permission_serializer = PermissionSerializer(data=request.data)
        permission_serializer.is_valid(raise_exception=True)
        programname:str = permission_serializer.validated_data['programname']
        password:str = permission_serializer.validated_data['password']

        # 요청값 분석, 비즈니스 로직
        prefix = programname.partition("-")[0].lower()
        permission_service = PermissionService(request=request, pk=programname)
        is_valid, obj = permission_service.validate(kind=prefix, password=password)

        if not is_valid:
            raise PermissionDenied(detail="관리자 코드가 올바르지 않아요.")

        permission_service.add_permission(kind=prefix, obj=obj)

        # 응답 송신
        return Response(
            status=status.HTTP_200_OK,
            data={"detail":"인증되었어요."},
        )
