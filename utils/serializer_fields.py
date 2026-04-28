from rest_framework import serializers

class ExampleField(serializers.Field):
    """
    예시 코드입니다.
    """
    def to_representation(self, value):
        pass
    
class ScheduleWriteField(serializers.Field):
    def to_internal_value(self, data):
        """
        data = [{"date":"05.16","time":"15:00~22:00"}, ...]
        """
        from django.utils import timezone
        from datetime import datetime
        from psycopg2.extras import DateTimeTZRange
        from rest_framework.exceptions import ValidationError

        if not data:
            return None

        # 1. 데이터가 리스트 형식이 아닐 경우 예외 처리
        if not isinstance(data, list):
            raise ValidationError("스케줄 데이터는 리스트([]) 형식이어야 합니다.")

        result = []
        for item in data:
            if not isinstance(item, dict):
                raise ValidationError("스케줄 항목은 객체({}) 형식이어야 합니다.")
            
            try:
                date = item["date"]
                time_range = item["time"]
                month, day = map(int, date.split("."))
                start_str, end_str = time_range.split("~")
                year = timezone.now().year

                start = timezone.make_aware(
                    datetime(year, month, day, int(start_str[:2]), int(start_str[3:5]))
                )
                end = timezone.make_aware(
                    datetime(year, month, day, int(end_str[:2]), int(end_str[3:5]))
                )
                result.append(DateTimeTZRange(start, end, '[]'))
            except (KeyError, ValueError, IndexError):
                raise ValidationError("스케줄 형식이 올바르지 않습니다. (예: 05.16 / 15:00~22:00)")

        # 2. 🔥 단일 필드 여부 체크 및 개수 제한 예외 처리
        # 현재 시리얼라이저가 연결된 모델 정보를 가져옵니다.
        model = self.parent.Meta.model
        field_name = self.field_name # 'schedule'
        
        # 모델의 필드가 ArrayField가 아닌 경우 (즉, Show처럼 단일 필드인 경우)
        from django.contrib.postgres.fields import ArrayField
        model_field = model._meta.get_field(field_name)

        if not isinstance(model_field, ArrayField):
            # 단일 필드인데 데이터가 2개 이상 들어오면 400 에러 발생
            if len(result) > 1:
                raise ValidationError(f"{model.__name__} 모델의 스케줄은 하나만 등록할 수 있습니다.")
            
            return result[0] if result else None

        # 부스(Booth)처럼 ArrayField인 경우 전체 리스트 반환
        return result