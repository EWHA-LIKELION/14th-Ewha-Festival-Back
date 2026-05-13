import re

from django.db.models import Q, Count, Value, CharField, Case, When, F
from django.db.models.functions import Concat, Cast, Replace
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booths.models import Booth
from shows.models import Show
from booths.serializers import BoothListSerializer
from shows.serializers import ShowListSerializer
from utils.filters_sorts import filter_and_sort
from utils.choices import LocationChoices
from utils.helpers import BasePagination
from searchs.services import record_search, get_popular_searches

def search(*, request, booths_qs, shows_qs):
    q = (request.query_params.get("q") or "").strip()
    q_normalize = re.sub(r'\s+', '', q)
    qs_no_space = Replace(F('name'), Value(' '), Value(''))

    booths_qs = booths_qs.annotate(
        name_no_space=qs_no_space,
    building_label=Case(
        When(location__building=LocationChoices.GRASS_GROUND, then=Value("잔디광장")),
        When(location__building=LocationChoices.SENTENNIAL_MUSEUM, then=Value("박물관")),
        When(location__building=LocationChoices.SPORT_TRACK, then=Value("스포츠트랙")),
        When(location__building=LocationChoices.HYUUT_GIL, then=Value("휴웃길")),
        When(location__building=LocationChoices.WELCH_RYANG_AUDITORIUM, then=Value("대강당")),
        When(location__building=LocationChoices.EWHA_POSCO_BUILDING, then=Value("포스코관")),
        When(location__building=LocationChoices.STUDENT_UNION, then=Value("학생문화관")),
        When(location__building=LocationChoices.HUMAN_ECOLOGY_BUILDING, then=Value("생활환경관")),
        When(location__building=LocationChoices.HAK_GWAN, then=Value("학관")),
        When(location__building=LocationChoices.EDUCATION_BUILDING, then=Value("교육관")),
        When(location__building=LocationChoices.EWHA_SHINSEGAE_BUILDING, then=Value("신세계관")),
        default=Value(""),
        output_field=CharField(),
        ),
    ).annotate(
        full_location=Concat(
            "building_label",
            Cast("location__number", CharField()),
            output_field=CharField(),
        )
    )

    booth_q = (
        Q(name__icontains=q) | Q(name__icontains=q_normalize) | Q(name_no_space__icontains=q_normalize) |
        Q(product__name__icontains=q) | Q(product__name__icontains=q_normalize) |
        Q(location__building__icontains=q) | Q(location__building__icontains=q_normalize) |
        Q(full_location__icontains=q) | Q(full_location__icontains=q_normalize)
    )

    if q_normalize.isdigit():
        booth_q |= Q(location__number=int(q_normalize))

    booths = (
        booths_qs
        .filter(booth_q)
        .annotate(scraps_count=Count("booth_scrap", distinct=True))
        .distinct()
    )

    show_q = (
        Q(name__icontains=q) | Q(name__icontains=q_normalize) | Q(name_no_space__icontains=q_normalize)
    )
    shows = (
        shows_qs.annotate(name_no_space=qs_no_space)
        .filter(show_q)
        .annotate(scraps_count=Count("show_scrap", distinct=True))
        .distinct()
    )

    booths = filter_and_sort(booths, request.query_params, program="booth")
    shows = filter_and_sort(shows, request.query_params, program="show")

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
