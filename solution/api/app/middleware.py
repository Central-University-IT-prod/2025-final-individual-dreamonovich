from django.utils.deprecation import MiddlewareMixin
from business.utils import set_local_cache_cur_min_max_score

initialized = False


class LocalCacheInitializationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        global initialized
        if not initialized:
            try:
                set_local_cache_cur_min_max_score()
            except Exception as e:
                pass
            initialized = True
