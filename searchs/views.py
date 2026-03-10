from django.db.models import Q, Count, Value, CharField, Case, When
from django.db.models.functions import Concat, Cast
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booths.models import Booth
from shows.models import Show
from .serializers import BoothSearchSerializer, ShowSearchSerializer
from utils.filters_sorts import filter_and_sort
from utils.choices import LocationChoices
from utils.helpers import BasePagination

def search(*, request, booths_qs, shows_qs):
    q = (request.query_params.get("q") or "").strip()

    booths_qs = booths_qs.annotate(
    building_label=Case(
        When(location__building=LocationChoices.MAIN_GATE, then=Value("정문")),
        When(location__building=LocationChoices.GRASS_GROUND, then=Value("잔디광장")),
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
        Q(name__icontains=q) |
        Q(product__name__icontains=q) |
        Q(location__building__icontains=q) |
        Q(full_location__icontains=q)
    )

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

    booths = filter_and_sort(booths, request.query_params, program="booth")
    shows = filter_and_sort(shows, request.query_params, program="show")

    booth_paginator = BasePagination()
    paginated_booths = booth_paginator.paginate_queryset(booths, request)
    
    booths_serializer = BoothSearchSerializer(
            paginated_booths,
            many=True,
            context={"request": request}
        ).data
    
    show_paginator = BasePagination()
    paginated_shows = show_paginator.paginate_queryset(shows, request)

    shows_serializer = ShowSearchSerializer(
            paginated_shows,
            many=True,
            context={"request":request}
        ).data

    return {
        "booths":{
            "counts": booth_paginator.count,
            "next": booth_paginator.get_next_link() is not None,
            "search_result": booths_serializer,
        },
        "shows":{
            "counts": show_paginator.count,
            "next": show_paginator.get_next_link() is not None,
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