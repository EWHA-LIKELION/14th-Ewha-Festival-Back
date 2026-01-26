from functools import wraps

def example(service_func):
    """
    예시 코드입니다.
    """
    @wraps(service_func)
    def wrapper(self, *args, **kwargs):
        # 여기에 데코레이터 코드를 작성하세요.
        return service_func(self, *args, **kwargs)
    return wrapper