import argparse
import os
from django.utils.deconstruct import deconstructible
from django.utils import timezone
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework import status

@deconstructible
class FilePathBuilder:
    """
    thumbnail = models.ImageField(upload_to=FilePathBuilder("thumbnail"))
    """
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, file_name):
        class_name = instance.__class__.__name__.lower()
        return f"{class_name}/{self.sub_path}/{file_name}"

def time_ago(dt):
    now = timezone.now()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "방금 전"
    if seconds < 3600:
        return f"{seconds // 60}분 전"
    if seconds < 86400:
        return f"{seconds // 3600}시간 전"
    return f"{seconds // 86400}일 전"

# 페이지네이션
class BasePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    limit_query_param = "limit"
    offset_query_param = "offset"

    def get_paginated_response(self, data):
        return Response({
            "count": self.count,
            "next": self.get_next_link() is not None,
            "previous": self.get_previous_link() is not None,
            "result": data,
        },
        status=status.HTTP_200_OK,
        )

def tsv_file(value:str):
    if not value.endswith('.tsv'):
        raise argparse.ArgumentTypeError(f"'{value}'은 .tsv 파일이 아닙니다.")
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError(f"{value} 파일을 찾을 수 없습니다.")
    return value
