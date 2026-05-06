import os
from uuid import uuid4
from storages.backends.s3boto3 import S3Boto3Storage

class CustomS3Storage(S3Boto3Storage):
    def get_available_name(self, name, max_length=None):
        dir_name, file_name = os.path.split(name)
        ext = os.path.splitext(file_name)[1]

        new_name = f"{uuid4()}{ext.lower()}"

        return os.path.join(dir_name, new_name)
