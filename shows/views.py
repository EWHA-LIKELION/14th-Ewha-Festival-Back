from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Show, ShowNotice, ShowScrap
from .serializers import ShowListSerializer, ShowDetailSerializer, ShowNoticeSerializer, ShowPatchSerializer, ShowScrapSerializer
from utils.filters_sorts import filter_and_sort
from utils.helpers import BasePagination

class ShowListView(APIView):
    # 페이지네이션 클래스 호출
    show_pagination = BasePagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, format=None):
        shows = (
            Show.objects.select_related("location")
            .annotate(scraps_count=Count("show_scrap", distinct=True))
            .all()
        )

        shows = filter_and_sort(shows, request.query_params, program="show")

        paginator = self.show_pagination()
        paginated_shows = paginator.paginate_queryset(shows, request, view=self)

        serializer = ShowListSerializer(
            paginated_shows,
            many=True,
            context={"request":request},
        ).data

        return paginator.get_paginated_response(serializer)

class ShowDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_object(self, pk):
        try:
            return (
                Show.objects
                .annotate(scraps_count=Count("show_scrap"))
                .get(pk=pk)
            )
        except Show.DoesNotExist:
            raise Http404
    
    def get(self, request:HttpRequest, pk, format=None):
        show = self.get_object(pk)
        serializer = ShowDetailSerializer(
            show,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk, format=None):
        show = self.get_object(pk)

        patch_serializer = ShowPatchSerializer(
            show,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        patch_serializer.is_valid(raise_exception=True)
        patch_serializer.save()

        show = self.get_object(pk)

        read_serializer = ShowDetailSerializer(
            show,
            context={"request": request},
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

class ShowNoticeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest, pk, format=None):
        get_object_or_404(Show, pk=pk)
    
        notices = (
            ShowNotice.objects
            .filter(show_id=pk)
            .order_by('-created_at')
        )

        serializer = ShowNoticeSerializer(
            notices,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ShowScrapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest, pk, format=None):
        show = get_object_or_404(Show, pk=pk)
        scrap, created = ShowScrap.objects.get_or_create(
            user=request.user, show=show
        )

        if not created:
            scrap.delete()
            return Response(
                {"scrapped": False},
                status=status.HTTP_200_OK
            )
        
        serializer = ShowScrapSerializer(scrap, context={"request": request})

        return Response(
            {"scrapped": True,
             "data": serializer.data},
             status=status.HTTP_201_CREATED
        )