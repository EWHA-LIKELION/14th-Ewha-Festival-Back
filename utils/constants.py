from enum import Enum

class Example(Enum):
    """
    예시 코드입니다.
    """
    example = 'example:{value}'

    def format(self, **kwargs):
        return self.value.format(**kwargs)