from rest_framework import serializers
from searchs.models import Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            'building',
            'number',
        )