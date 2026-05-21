from enum import Enum

class Cachekey(Enum):
    BOOTH_LIST = 'booth_list:{user_id}:{params_hash}'
    BOOTH_DETAIL = 'booth_detail:{user_id}:{booth_id}'
    SHOW_LIST = 'show_list:{user_id}:{params_hash}'
    SHOW_DETAIL = 'show_detail:{user_id}:{show_id}'
    SEARCH_LIST = 'search_list:{user_id}:{params_hash}'
    SCRAP_LIST = 'scrap_list:{user_id}:{params_hash}'

    def format(self, **kwargs):
        return self.value.format(**kwargs)
