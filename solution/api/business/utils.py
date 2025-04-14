from django.core.cache import caches

from business.models import Score


def set_local_cache_cur_min_max_score():
    local_cache = caches['local']

    ml_min, ml_max = Score.get_min_and_max()

    local_cache.set("score_ml_min", ml_min or 0, None)
    local_cache.set("score_ml_max", ml_max or 0, None)
