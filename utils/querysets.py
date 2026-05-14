from django.db import models
from .filters_sorts import base_filter, base_sort

class FilterSortQuerySet(models.QuerySet):
    def filter_and_sort(self, params, *, program: str):
        qs = base_filter(self, params, program=program)
        return base_sort(qs, params.get("sorting"), program=program)