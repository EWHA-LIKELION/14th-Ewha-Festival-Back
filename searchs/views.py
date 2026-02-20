from django.db.models import Q, Count
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booths.models import Booth, BoothScrap
from shows.models import Show, ShowScrap
from .serializers import BoothSearchSerializer, ShowSearchSerializer
# from utils.filters_sorts import filter_and_sort

def search(*, request, booths_qs, shows_qs):
    q = (request.query_params.get("q") or "").strip()

    booth_q = Q(name__icontains=q) | Q(product__name__icontains=q)
    if q.isdigit():
        booth_q |= Q(location__number=int(q))

    booths = (
        booths_qs
        .filter(booth_q)
        .annotate(scraps_count=Count("booth_scrap", distinct=True))
        .distinct()
    )

    show_q = Q(name__icontains=q)
    shows = (
        shows_qs
        .filter(show_q)
        .annotate(scraps_count=Count("show_scrap", distinct=True))
        .distinct()
    )

    # booths = filter_and_sort(booths, request.query_params, program="booth")
    booths_serializer = BoothSearchSerializer(
            booths,
            many=True,
            context={"request": request}
        ).data

    # shows = filter_and_sort(shows, request.query_params, program="show")
    shows_serializer = ShowSearchSerializer(
            shows,
            many=True,
            context={"request":request}
        ).data
    
    return {
        "booths":{
            "counts":len(booths_serializer),
            "search_result": booths_serializer,
        },
        "shows":{
                "counts":len(shows_serializer),
                "search_result": shows_serializer,
        },
    }

class SearchView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, format=None):
        booths_qs = (
            Booth.objects.select_related("location")
            .prefetch_related("product")
        )
        shows_qs = (
            Show.objects.select_related("location")
        )
        result = search(
            request=request,
            booths_qs=booths_qs,
            shows_qs=shows_qs,
        )
        return Response(
            result,
            status=status.HTTP_200_OK,
        )