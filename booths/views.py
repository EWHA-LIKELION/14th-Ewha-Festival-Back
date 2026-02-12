from django.http import HttpRequest, Http404
from django.db.models import Count
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from .models import Booth
from .serializers import BoothDetailSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .serializers import BoothDetailSerializer, BoothPatchSerializer

# Create your views here.

class Conflict(APIException):
    status_code = 409
    default_detail = "최근 업데이트 전 정보를 보고 있습니다. 새로고침하여 최근 업데이트 내역을 확인하고 업데이트해 주십시오."
    default_code = "conflict"

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
    
    def patch(self, request: HttpRequest, pk, format=None):
        booth = self.get_object(pk)
        
        client_ts = request.headers.get("X-Resource-Version")
        if not client_ts:
            return Response(
                {"detail": "X-Resource-Version 헤더가 누락되었습니다."},
                status=status.HTTP_428_PRECONDITION_REQUIRED,  
            )
        
        dt = parse_datetime(client_ts)
        if dt is None:
            return Response({"detail": "datetime format이 잘못되었습니다."}, status=400)
        
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
            
        if booth.updated_at and booth.updated_at > dt:
            raise Conflict(
                detail={
                    "detail": "최근 업데이트 전 정보를 보고 있습니다. 새로고침하여 최근 업데이트 내역을 확인하고 업데이트해 주십시오.",
                    "server_updated_at": booth.updated_at.isoformat(),
                }
            )
        
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