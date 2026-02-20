from django.shortcuts import render

# Create your views here.
    
class ScrapbookSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        booths_qs = (
            Booth.objects.select_related("location")
            .prefetch_related("product")
            .filter(booth_scrap__user=request.user)
        )
        shows_qs = (
            Show.objects.select_related("location")
            .filter(show_scrap__user=request.user)
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