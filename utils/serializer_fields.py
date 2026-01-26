from rest_framework import serializers

class ExampleField(serializers.Field):
    """
    예시 코드입니다.
    """
    def to_representation(self, value):
        pass