from django.core.cache import cache
from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booth, BoothNotice, BoothScrap
from .serializers import BoothListSerializer, BoothDetailSerializer, BoothNoticeSerializer, BoothPatchSerializer, BoothScrapSerializer
from utils.constants import Cachekey
from utils.helpers import BasePagination, get_user_id, calc_params_hash

class BoothListView(APIView):
    # 페이지네이션 클래스 호출
    booth_pagination = BasePagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, format=None):
        cache_key = Cachekey.BOOTH_LIST.format(
            user_id=get_user_id(request.user),
            params_hash=calc_params_hash(request.query_params)
        )
        cached = cache.get(cache_key)

        if cached is not None:
            return Response(
                status=status.HTTP_200_OK,
                data=cached
            )

        booths = (
            Booth.objects
            .with_location()
            .with_scraps_count(program="booth")
            .with_is_scraped(request.user, program='booth')
            .filter_and_sort(request.query_params, program="booth")
        )

        paginator = self.booth_pagination()
        paginated_booths = paginator.paginate_queryset(booths, request, view=self)

        serializer = BoothListSerializer(
            paginated_booths,
            many=True,
            context={"request":request},
        ).data

        response_data = paginator.get_paginated_response(serializer).data
        cache.set(cache_key, response_data, 60*3)

        return Response(
            status=status.HTTP_200_OK,
            data=response_data
        )

class BoothDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_object(self, request:HttpRequest, pk):
        try:
            return (
                Booth.objects
                .with_scraps_count(program="booth")
                .with_is_scraped(request.user, program='booth')
                .get(pk=pk)
            )
        except Booth.DoesNotExist:
            raise Http404
    
    def get(self, request:HttpRequest, pk, format=None):
        cache_key = Cachekey.BOOTH_DETAIL.format(
            user_id=get_user_id(request.user),
            booth_id=pk
        )
        cached = cache.get(cache_key)

        if cached is not None:
            return Response(
                status=status.HTTP_200_OK,
                data=cached
            )

        booth = self.get_object(request, pk)
        serializer = BoothDetailSerializer(
            booth,
            context={"request": request},
        )

        response_data = serializer.data
        cache.set(cache_key, response_data, 60*3)

        return Response(
            status=status.HTTP_200_OK,
            data=response_data
        )

    def patch(self, request, pk, format=None):
        booth = self.get_object(request, pk)
        
        def has_permission(user, booth):
            return user.permission_booth.filter(id=booth.id).exists()
        if not has_permission(request.user, booth):
            return Response(
                {"detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        patch_serializer = BoothPatchSerializer(
            booth,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        patch_serializer.is_valid(raise_exception=True)
        patch_serializer.save()

        booth = self.get_object(request, pk)
        read_serializer = BoothDetailSerializer(booth, context={"request": request})

        cache.delete_pattern(Cachekey.BOOTH_LIST.format(user_id="*", params_hash="*"))
        cache.delete_pattern(Cachekey.BOOTH_DETAIL.format(user_id="*", booth_id=pk))
        cache.delete_pattern(Cachekey.SEARCH_LIST.format(user_id="*", params_hash="*"))

        return Response(read_serializer.data, status=status.HTTP_200_OK)

class BoothNoticeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest, pk, format=None):
        get_object_or_404(Booth, pk=pk)
        
        notices = (
            BoothNotice.objects
            .filter(booth_id=pk)
            .order_by('-created_at', '-id')
        )

        serializer = BoothNoticeSerializer(
            notices,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class BoothScrapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest, pk, format=None):
        booth = get_object_or_404(Booth, pk=pk)
        scrap, created = BoothScrap.objects.get_or_create(
            user=request.user, booth=booth
        )

        if not created:
            scrap.delete()
            return Response(
                {"scrapped": False},
                status=status.HTTP_200_OK
            )

        serializer = BoothScrapSerializer(scrap, context={"request": request})

        cache.delete_pattern(Cachekey.BOOTH_LIST.format(user_id=request.user.id, params_hash="*"))
        cache.delete_pattern(Cachekey.BOOTH_DETAIL.format(user_id=request.user.id, booth_id=pk))
        cache.delete_pattern(Cachekey.SEARCH_LIST.format(user_id=request.user.id, params_hash="*"))

        return Response(
            {"scrapped": True,
             "data": serializer.data},
             status=status.HTTP_201_CREATED
        )
