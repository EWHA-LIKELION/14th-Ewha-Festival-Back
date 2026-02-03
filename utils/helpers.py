from django.utils.deconstruct import deconstructible
from django.utils import timezone

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