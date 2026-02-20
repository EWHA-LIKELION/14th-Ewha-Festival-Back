from django.http import HttpRequest, Http404
from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Show
from .serializers import ShowListSerializer, ShowDetailSerializer
# from utils.filters_sorts import filter_and_sort

# Create your views here.
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

        # shows = filter_and_sort(shows, request.query_params, program="show")

        serializer = ShowListSerializer(
            shows,
            many=True,
            context={"request":request},
        ).data

        return Response(
        {
            "counts":len(serializer),
            "search_result": serializer,
            "message":"검색 결과가 없습니다." if len(serializer) == 0 else "",
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