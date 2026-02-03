from django.http import HttpRequest, Http404
from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Booth
from .serializers import BoothDetailSerializer

# Create your views here.

class BoothDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
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