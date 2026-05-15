import re

from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booths.models import Booth
from shows.models import Show
from booths.serializers import BoothListSerializer
from shows.serializers import ShowListSerializer
from utils.helpers import BasePagination
from searchs.services import record_search, get_popular_searches

def search(*, request, booths_qs, shows_qs):
    q = (request.query_params.get("q") or "").strip()
    q_normalize = re.sub(r'\s+', '', q)

    booths_qs = booths_qs.with_building_label()
    
    booth_q = (
        Q(name__icontains=q) | Q(name__icontains=q_normalize) | Q(name_no_space__icontains=q_normalize) |
        Q(product__name__icontains=q) | Q(product__name__icontains=q_normalize) |
        Q(building_label__icontains=q) | Q(building_label__icontains=q_normalize) |
        Q(full_location=q) | Q(full_location=q_normalize)
    )

    if q_normalize.isdigit():
        booth_q |= Q(location__number=int(q_normalize))

    booths = (
        booths_qs
        .filter(booth_q)
        .with_scraps_count(program="booth")
        .distinct()
        .filter_and_sort(request.query_params, program="booth")
    )

    show_q = (
        Q(name__icontains=q) | Q(name__icontains=q_normalize) | Q(name_no_space__icontains=q_normalize)
    )
    shows = (
        shows_qs.with_name_no_space()
        .filter(show_q)
        .with_scraps_count(program="show")
        .distinct()
        .filter_and_sort(request.query_params, program="show")
    )

    booth_paginator = BasePagination()
    paginated_booths = booth_paginator.paginate_queryset(booths, request)
    
    booths_serializer = BoothListSerializer(
            paginated_booths,
            many=True,
            context={"request": request}
        ).data
    
    show_paginator = BasePagination()
    paginated_shows = show_paginator.paginate_queryset(shows, request)

    shows_serializer = ShowListSerializer(
            paginated_shows,
            many=True,
            context={"request":request}
        ).data

    return {
        "booths":{
            "counts": booth_paginator.count,
            "next": booth_paginator.get_next_link() is not None,
            "previous": booth_paginator.get_previous_link() is not None,
            "search_result": booths_serializer,
        },
        "shows":{
            "counts": show_paginator.count,
            "next": show_paginator.get_next_link() is not None,
            "previous": show_paginator.get_previous_link() is not None,
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
        q = (request.query_params.get("q") or "").strip()
        if q and (result["booths"]["counts"] > 0 or result["shows"]["counts"] > 0):
            record_search(q)
        return Response(
            result,
            status=status.HTTP_200_OK,
        )

class PopularSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        return Response(
            get_popular_searches(),
            status=status.HTTP_200_OK
        )
