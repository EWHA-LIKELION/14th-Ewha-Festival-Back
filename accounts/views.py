from django.http import HttpRequest
from django.db.models import Count, F
from .models import User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import MyDataSerializer

# Create your views here.

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