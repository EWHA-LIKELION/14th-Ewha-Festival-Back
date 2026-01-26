from functools import wraps

def example(view_func):
    """
    예시 코드입니다.
    """
    @wraps(view_func)
    def wrapper(self, *args, **kwargs):
        # 여기에 데코레이터 코드를 작성하세요.
        return view_func(self, *args, **kwargs)
    return wrapper