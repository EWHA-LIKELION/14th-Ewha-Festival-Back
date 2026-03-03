from django.http import HttpRequest, Http404
from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Show
from .serializers import ShowDetailSerializer, ShowPatchSerializer

class ShowDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ["GET", "PATCH"]:
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