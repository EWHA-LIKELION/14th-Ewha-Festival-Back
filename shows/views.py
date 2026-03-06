from django.http import HttpRequest, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Show, ShowNotice
from .serializers import ShowListSerializer, ShowDetailSerializer, ShowNoticeSerializer, ShowPatchSerializer
from utils.filters_sorts import filter_and_sort

class ShowListView(APIView):
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

        serializer = ShowListSerializer(
            shows,
            many=True,
            context={"request":request},
        ).data

        return Response(
        {
            "counts":len(serializer),
            "search_result": serializer,
        },
        status=status.HTTP_200_OK,
        )

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