from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

@deconstructible
class FileSizeValidator:
    def __init__(self, min_size_MB:int|None=None, max_size_MB:int|None=None):
        self.min_size_MB = min_size_MB
        self.max_size_MB = max_size_MB

    def __call__(self, value):
        if (self.min_size_MB) and (value.size < self.min_size_MB *1024*1024):
            raise ValidationError(f"파일 '{value.name}'의 용량이 최소 용량 {self.min_size_MB}MB를 미만합니다.")

        if (self.max_size_MB) and (value.size > self.max_size_MB *1024*1024):
            raise ValidationError(f"파일 '{value.name}'의 용량이 최대 용량 {self.max_size_MB}MB를 초과합니다.")
