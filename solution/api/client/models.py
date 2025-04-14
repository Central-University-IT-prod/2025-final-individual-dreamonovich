import logging

from django.core.cache import caches
from django.db import models
from django.db.models import (
    Q,
    QuerySet,
    Max,
    Min,
    Count,
    Subquery,
    OuterRef,
    Value,
    F, Exists,
)

from app.validators import profanity_validator
from django.db.models.functions import Coalesce

from business.algorithm import compute_ad_score, normalize_ml_score
from business.models import Campaign, Advertiser, Score

from business.algorithm import get_max_profit

logger = logging.getLogger(__name__)


class Client(models.Model):
    CLIENT_GENDER_CHOICES = {
        "MALE": "Male",
        "FEMALE": "Female",
    }

    id = models.UUIDField(primary_key=True)
    login = models.CharField(max_length=100, validators=[profanity_validator])
    age = models.PositiveIntegerField()
    location = models.CharField(max_length=500, validators=[profanity_validator])
    gender = models.CharField(max_length=6, choices=CLIENT_GENDER_CHOICES)

    def get_relevant_advertisement(self, current_day):
        local_cache = caches['local']
        ml_min, ml_max = local_cache.get("score_ml_min"), local_cache.get("score_ml_max")

        campaigns = list(
            self.get_targeted_and_not_impressed_campaigns(current_day)
            .annotate(
                ml_score=Coalesce(
                    Subquery(
                        Score.objects.filter(
                            client=self, advertiser_id=OuterRef("advertiser_id")
                        ).values("score")[:1]
                    ),
                    Value(0),
                ),
            )
            .filter(
                impressions_count__lt=F("impressions_limit"),
                clicks_count__lt=F("clicks_limit"),
            )
        )

        if not campaigns:
            return None

        campaign_ids = tuple(campaign.id for campaign in campaigns)

        max_profit = get_max_profit(self.id, campaign_ids)

        for campaign in campaigns:
            # Normalize ML score inline
            if ml_max > ml_min:
                ml_norm = (campaign.ml_score - ml_min) / (ml_max - ml_min)
            else:
                ml_norm = 1.0 if ml_max == 0 else 0.0

            # Profit calculation
            P = campaign.cost_per_impression + (ml_norm * campaign.cost_per_click)
            P_min = campaign.cost_per_impression
            P_max = campaign.cost_per_impression + campaign.cost_per_click
            P_norm = (P - P_min) / (P_max - P_min) if (P_max - P_min) else 0.0
            revenue_multiplier = (P / max_profit) if max_profit > 0 else 1.0
            profit_component = P_norm * revenue_multiplier

            # Relevancy is the normalized ML score
            R = ml_norm

            # Performance based on predicted next impression and click:
            impression_perf = min((campaign.impressions_count + 1) / campaign.impressions_limit, 1)
            predicted_clicks = ml_norm  # simple model
            click_perf = min((campaign.clicks_count + predicted_clicks) / campaign.clicks_limit, 1)
            T = (impression_perf + click_perf) / 2

            base_score = 0.525 * profit_component + 0.275 * R + 0.175 * T

            # Impression deficit factor
            impressions_remaining = max(0, campaign.impressions_limit - campaign.impressions_count)
            D = (impressions_remaining / campaign.impressions_limit) if campaign.impressions_limit > 0 else 0.0

            campaign.ad_score = base_score * D

        campaigns.sort(key=lambda c: c.ad_score, reverse=True)
        return campaigns

    def get_targeted_and_not_impressed_campaigns(self, current_day):
        return (
            Campaign.objects
            .filter(
                start_date__lte=current_day,
                end_date__gte=current_day,
            )
            .filter(
                Q(targeted_gender=self.gender) | Q(targeted_gender="ALL") | Q(targeted_gender__isnull=True),
                Q(targeted_age_from__lte=self.age) | Q(targeted_age_from__isnull=True),
                Q(targeted_age_to__gte=self.age) | Q(targeted_age_to__isnull=True),
                Q(targeted_location=self.location) | Q(targeted_location__isnull=True),
            )
            .annotate(
                has_impression=Exists(
                    Impression.objects.filter(
                        client_id=self.id,
                        advertisement_id=OuterRef("pk"),
                    )
                )
            )
            .filter(has_impression=False)
        )

    def get_normalized_ml_score(self, advertiser: Advertiser):
        score = Score.objects.filter(advertiser=advertiser, client=self).first()
        ml_min, ml_max = Score.get_min_and_max()

        ml_score_value = score.score if score else 0
        ml_min_value = ml_min if ml_min else 0
        ml_max_value = ml_max if ml_max else 0
        return normalize_ml_score(ml_score_value, ml_min_value, ml_max_value)


class Impression(models.Model):
    client_id = models.UUIDField(db_index=True)
    cost = models.FloatField()
    advertiser_id = models.UUIDField(db_index=True)
    # Create a foreign key to Campaign so that the reverse relation "impression_set" is available.
    advertisement = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="impression_set"
    )
    day = models.BigIntegerField(db_index=True)

    class Meta:
        unique_together = (("client_id", "advertisement",),)
        indexes = [
            models.Index(fields=["client_id"]),
            models.Index(fields=["advertisement"]),
            models.Index(fields=["day"]),
        ]

    def __str__(self):
        return f"Impression(advertisement_id={self.advertisement.id}, day={self.day})"


class Click(models.Model):
    client_id = models.UUIDField(db_index=True)
    cost = models.FloatField()
    advertiser_id = models.UUIDField(db_index=True)
    # Create a foreign key to Campaign so that the reverse relation "click_set" is available.
    advertisement = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="click_set"
    )
    day = models.BigIntegerField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["client_id"]),
            models.Index(fields=["advertisement"]),
            models.Index(fields=["day"]),
        ]

    def __str__(self):
        return f"Click(advertisement_id={self.advertisement.id}, day={self.day})"
