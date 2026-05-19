def reset_ongoing():
    """모든 부스의 ongoing을 Null로 초기화"""
    from .models import Booth  # 순환 import 방지를 위해 내부 import
    updated = Booth.objects.update(ongoing=None)
    print(f"[Scheduler] {updated}개 부스 ongoing 초기화 완료")
