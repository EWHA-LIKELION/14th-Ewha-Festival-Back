from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booth, BoothNotice, BoothScrap
from .serializers import BoothListSerializer, BoothDetailSerializer, BoothNoticeSerializer, BoothPatchSerializer, BoothScrapSerializer
from utils.filters_sorts import filter_and_sort
from utils.helpers import BasePagination

class BoothListView(APIView):
    # 페이지네이션 클래스 호출
    booth_pagination = BasePagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, format=None):
        booths = (
            Booth.objects.select_related("location")
            .annotate(scraps_count=Count("booth_scrap", distinct=True))
            .all()
        )

        booths = filter_and_sort(booths, request.query_params, program="booth")

        paginator = self.booth_pagination()
        paginated_booths = paginator.paginate_queryset(booths, request, view=self)

        serializer = BoothListSerializer(
            paginated_booths,
            many=True,
            context={"request":request},
        ).data

        return paginator.get_paginated_response(serializer)

class BoothDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ["GET", "PATCH"]:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_object(self, pk):
        try:
            return (
                Booth.objects
                .annotate(scraps_count=Count("booth_scrap"))
                .get(pk=pk)
            )
        except Booth.DoesNotExist:
            raise Http404
    
    def get(self, request:HttpRequest, pk, format=None):
        booth = self.get_object(pk)
        serializer = BoothDetailSerializer(
            booth,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk, format=None):
        booth = self.get_object(pk)

        patch_serializer = BoothPatchSerializer(
            booth,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        patch_serializer.is_valid(raise_exception=True)
        patch_serializer.save()

        booth = self.get_object(pk)  
        read_serializer = BoothDetailSerializer(booth, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)

class BoothNoticeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest, pk, format=None):
        get_object_or_404(Booth, pk=pk)
        
        notices = (
            BoothNotice.objects
            .filter(booth_id=pk)
            .order_by('-created_at')
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
        return Response(
            {"scrapped": True,
             "data": serializer.data},
             status=status.HTTP_201_CREATED
        )


    