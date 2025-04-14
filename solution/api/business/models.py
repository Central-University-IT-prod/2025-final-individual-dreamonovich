import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Min

from app.utils import get_current_day
from app.validators import profanity_validator


class Advertiser(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100, validators=[profanity_validator])


class Score(models.Model):
    client = models.ForeignKey("client.Client", on_delete=models.CASCADE)
    advertiser = models.ForeignKey(Advertiser, on_delete=models.CASCADE)
    score = models.IntegerField()

    @staticmethod
    def get_min_and_max():
        score_agg = Score.objects.aggregate(ml_max=Max("score"), ml_min=Min("score"))
        return score_agg.get("ml_min"), score_agg.get("ml_max")

class Campaign(models.Model):
    TARGET_GENDER_CHOICES = {"MALE": "Male", "FEMALE": "Female", "ALL": "All"}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    impressions_limit = models.PositiveIntegerField()
    clicks_limit = models.PositiveIntegerField()
    impressions_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)
    cost_per_impression = models.FloatField(validators=[MinValueValidator(0)])
    cost_per_click = models.FloatField(validators=[MinValueValidator(0)])
    ad_title = models.CharField(max_length=100, validators=[profanity_validator])
    ad_text = models.CharField(max_length=500, validators=[profanity_validator])
    start_date = models.PositiveIntegerField()
    end_date = models.PositiveIntegerField()
    image = models.ImageField(null=True, blank=True)
    targeted_gender = models.CharField(
        max_length=6, choices=TARGET_GENDER_CHOICES, null=True, blank=True
    )
    targeted_age_from = models.PositiveIntegerField(null=True, blank=True)
    targeted_age_to = models.PositiveIntegerField(null=True, blank=True)
    targeted_location = models.CharField(
        max_length=500, null=True, blank=True, validators=[profanity_validator]
    )
    erid = models.CharField(max_length=20, null=True, blank=True)  # Для РФ

    advertiser = models.ForeignKey(
        Advertiser, on_delete=models.CASCADE, related_name="campaigns"
    )

    class Meta:
        indexes = [
            models.Index(fields=["impressions_count"]),
            models.Index(fields=["clicks_count"]),
            models.Index(fields=["impressions_limit"]),
            models.Index(fields=["clicks_limit"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["targeted_gender"]),
            models.Index(fields=["targeted_age_from"]),
            models.Index(fields=["targeted_age_to"]),
            models.Index(fields=["targeted_location"]),
            models.Index(fields=["erid"]),
        ]

    def is_started(self):
        return self.start_date < get_current_day()


