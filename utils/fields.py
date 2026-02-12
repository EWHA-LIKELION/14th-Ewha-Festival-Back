from rest_framework import serializers

class ScheduleWriteField(serializers.Field):
    def to_internal_value(self, data):
        """
        data = [
          {"date":"05.16","time":"03:00~12:00"},
        ]
        """

        from django.utils import timezone
        from datetime import datetime

        result = []

        for item in data:
            date = item["date"]      # "05.16"
            time_range = item["time"]  # "03:00~12:00"

            month, day = map(int, date.split("."))
            start_str, end_str = time_range.split("~")

            year = timezone.now().year  # 현재년도 사용

            start = timezone.make_aware(
                datetime(year, month, day,
                         int(start_str[:2]), int(start_str[3:5]))
            )
            end = timezone.make_aware(
                datetime(year, month, day,
                         int(end_str[:2]), int(end_str[3:5]))
            )

            from psycopg2.extras import DateTimeTZRange
            result.append(DateTimeTZRange(start, end, '[]'))

        return result
