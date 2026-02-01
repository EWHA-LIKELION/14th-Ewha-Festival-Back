from django.utils.deconstruct import deconstructible

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
