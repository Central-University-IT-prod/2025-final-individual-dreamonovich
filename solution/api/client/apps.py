from django.apps import AppConfig


class ClientConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "client"

    def ready(self):
        from business.models import Score

        # local_cache = caches['local']
        # score_agg = Score.objects.aggregate(ml_max=Max("score"), ml_min=Min("score"))
        # ml_max, ml_min = score_agg.get("ml_max"), score_agg.get("ml_min")
        #
        # local_cache.set("ml_max", ml_max, None)
        # local_cache.set("ml_min", ml_min, None)
