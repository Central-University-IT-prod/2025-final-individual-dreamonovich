from django.db.models import Sum, Count
from rest_framework import serializers, status

from app.exceptions import CustomAPIException
from app.serializers import ClearNullMixin
from app.utils import get_current_day
from .models import Advertiser, Score, Campaign


class AdvertiserSerializer(ClearNullMixin, serializers.ModelSerializer):
    advertiser_id = serializers.UUIDField(source="id")

    class Meta:
        model = Advertiser
        fields = ("advertiser_id", "name")


class ScoreSerializer(ClearNullMixin, serializers.ModelSerializer):
    advertiser_id = serializers.UUIDField(source="advertiser.id")

    class Meta:
        model = Score
        fields = ("client_id", "advertiser_id", "score")


class CreateScoreBodySerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    advertiser_id = serializers.UUIDField()
    score = serializers.IntegerField()


class TargetingSerializer(serializers.Serializer):
    gender = serializers.ChoiceField(
        choices=Campaign.TARGET_GENDER_CHOICES.keys(), required=False
    )
    age_from = serializers.IntegerField(min_value=0, required=False)
    age_to = serializers.IntegerField(min_value=0, required=False)
    location = serializers.CharField(max_length=500, required=False)

    def validate(self, data):
        age_from = data.get("age_from")
        age_to = data.get("age_to")

        if age_from is not None and age_to is not None and age_from > age_to:
            raise serializers.ValidationError(
                {"age_to": "age_to must be greater than or equal to age_from"}
            )

        return data


class CreateCampaignSerializer(ClearNullMixin, serializers.ModelSerializer):
    campaign_id = serializers.UUIDField(source="id", read_only=True)
    advertiser_id = serializers.PrimaryKeyRelatedField(
        source="advertiser",
        queryset=Advertiser.objects.all(),
    )
    targeting = TargetingSerializer(required=False)

    class Meta:
        model = Campaign
        fields = [
            "campaign_id",
            "advertiser_id",
            "impressions_limit",
            "clicks_limit",
            "cost_per_impression",
            "cost_per_click",
            "ad_title",
            "ad_text",
            "start_date",
            "end_date",
            "erid",
            "targeting",
            "targeted_gender",
            "targeted_age_from",
            "targeted_age_to",
            "targeted_location",
        ]
        extra_kwargs = {
            "targeted_gender": {"required": False, "write_only": True},
            "targeted_age_from": {"required": False, "write_only": True},
            "targeted_age_to": {"required": False, "write_only": True},
            "targeted_location": {"required": False, "write_only": True},
        }

    def validate(self, attrs):
        if (
            attrs.get("impressions_limit") is not None
            and attrs.get("clicks_limit") is not None
        ):
            if attrs["impressions_limit"] < attrs["clicks_limit"]:
                raise serializers.ValidationError(
                    "impressions_limit должно быть больше clicks_limit"
                )
        if attrs.get("start_date") is not None and attrs.get("end_date") is not None:
            if attrs["start_date"] > attrs["end_date"]:
                raise serializers.ValidationError(
                    "end_date долно быть больше start_date"
                )
        return attrs

    def create(self, validated_data):
        if targeting := validated_data.get("targeting"):
            validated_data["targeted_gender"] = targeting.pop("gender", None)
            validated_data["targeted_age_from"] = targeting.pop("age_from", None)
            validated_data["targeted_age_to"] = targeting.pop("age_to", None)
            validated_data["targeted_location"] = targeting.pop("location", None)
        return super().create(validated_data)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["targeting"] = {
            "gender": instance.targeted_gender,
            "age_from": instance.targeted_age_from,
            "age_to": instance.targeted_age_to,
            "location": instance.targeted_location,
        }
        return self._remove_nulls(response)

    def to_internal_value(self, data):
        # For form-data
        flat_data = {}
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                flat_data[key] = value[0]
            else:
                flat_data[key] = value

        if flat_data and (targeting_data := flat_data.pop("targeting", None)):
            flat_data["targeted_gender"] = targeting_data.get("gender")
            flat_data["targeted_age_from"] = targeting_data.get("age_from")
            flat_data["targeted_age_to"] = targeting_data.get("age_to")
            flat_data["targeted_location"] = targeting_data.get("location")
        return super().to_internal_value(flat_data)


class CampaignSerializer(ClearNullMixin, serializers.ModelSerializer):
    campaign_id = serializers.UUIDField(source="id", read_only=True)
    advertiser_id = serializers.PrimaryKeyRelatedField(
        source="advertiser",
        queryset=Advertiser.objects.all(),
        required=False,
    )
    targeting = TargetingSerializer(required=False)

    class Meta:
        model = Campaign
        fields = [
            "campaign_id",
            "advertiser_id",
            "impressions_limit",
            "clicks_limit",
            "cost_per_impression",
            "cost_per_click",
            "ad_title",
            "ad_text",
            "start_date",
            "end_date",
            "targeting",
            "image",
            "erid",
            "targeted_gender",
            "targeted_age_from",
            "targeted_age_to",
            "targeted_location",
        ]
        read_only_fields = (
            "campaign_id",
            "advertiser_id",
            "impressions_limit",
            "clicks_limit",
        )
        extra_kwargs = {
            "targeted_gender": {"required": False, "write_only": True},
            "targeted_age_from": {"required": False, "write_only": True},
            "targeted_age_to": {"required": False, "write_only": True},
            "targeted_location": {"required": False, "write_only": True},
            "cost_per_impression": {
                "required": False,
            },
            "cost_per_click": {
                "required": False,
            },
            "ad_title": {
                "required": False,
            },
            "ad_text": {
                "required": False,
            },
            "start_date": {
                "required": False,
            },
            "end_date": {
                "required": False,
            },
        }

    def update(self, instance, validated_data):
        (validated_data.pop("impressions_limit", instance.impressions_limit),)
        (validated_data.pop("clicks_limit", instance.impressions_limit),)
        start_date = validated_data.pop("start_date", None)
        end_date = validated_data.pop("end_date", None)

        if start_date is not None or end_date is not None:
            if instance.is_started():
                raise CustomAPIException(
                    detail="Нельзя менять дату начала или конца после старта кампании.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            current_day = get_current_day()
            if (
                start_date is not None
                and start_date < current_day
                or end_date is not None
                and end_date < current_day
            ):
                raise CustomAPIException(
                    detail="Дата окончания или начала не может быть в прошлом.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        if start_date is not None and end_date is not None:
            instance.start_date = start_date
            instance.end_date = end_date
            if start_date > end_date:
                raise CustomAPIException(
                    detail="Дата начала больше даты конца.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if targeting := validated_data.get("targeting", None):
            instance.targeted_gender = targeting.pop("gender", instance.targeted_gender)
            instance.targeted_age_from = targeting.pop(
                "age_from", instance.targeted_age_from
            )
            instance.targeted_age_to = targeting.pop("age_to", instance.targeted_age_to)
            instance.targeted_location = targeting.pop(
                "location", instance.targeted_location
            )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["targeting"] = {
            "gender": instance.targeted_gender,
            "age_from": instance.targeted_age_from,
            "age_to": instance.targeted_age_to,
            "location": instance.targeted_location,
        }
        return response

    def to_internal_value(self, data):
        if data and (targeting_data := data.pop("targeting", None)):
            data["targeted_gender"] = targeting_data.get("gender")
            data["targeted_age_from"] = targeting_data.get("age_from")
            data["targeted_age_to"] = targeting_data.get("age_to")
            data["targeted_location"] = targeting_data.get("location")
        return super().to_internal_value(data)


class CampaignForClientSerializer(ClearNullMixin, serializers.ModelSerializer):
    ad_id = serializers.UUIDField(source="id")

    class Meta:
        model = Campaign
        fields = (
            "ad_id",
            "ad_title",
            "ad_text",
            "advertiser_id",
        )


class CampaignStatisticsSerializer(ClearNullMixin, serializers.ModelSerializer):
    impressions_count = serializers.SerializerMethodField()
    clicks_count = serializers.SerializerMethodField()
    conversion = serializers.SerializerMethodField()
    spent_impressions = serializers.SerializerMethodField()
    spent_clicks = serializers.SerializerMethodField()
    spent_total = serializers.SerializerMethodField()

    def get_impressions_count(self, obj):
        self.impressions_count = obj.impressions.count()  # FIX
        return self.impressions_count

    def get_clicks_count(self, obj):
        self.clicks_count = obj.clicks.count()  # FIX
        return self.clicks_count

    def get_conversion(self, obj):
        self.conversion = 0
        if not self.impressions_count == 0:
            self.conversion = (self.clicks_count / self.impressions_count) * 100
        return self.conversion

    def get_spent_impressions(self, obj):
        self.spent_impressions = obj.impressions.aggregate(total=Sum("cost"))[
            "total"
        ]  # FIX
        if not self.spent_impressions:
            self.spent_impressions = 0
        return self.spent_impressions

    def get_spent_clicks(self, obj):
        self.spent_clicks = obj.clicks.aggregate(total=Sum("cost"))["total"]  # FIX
        if not self.spent_clicks:
            self.spent_clicks = 0
        return self.spent_clicks

    def get_spent_total(self, obj):
        return self.spent_clicks + self.spent_impressions

    class Meta:
        model = Campaign
        fields = (
            "impressions_count",
            "clicks_count",
            "conversion",
            "spent_impressions",
            "spent_clicks",
            "spent_total",
        )


class AdvertiserStatisticsSerializer(ClearNullMixin, serializers.ModelSerializer):
    impressions_count = serializers.SerializerMethodField()
    clicks_count = serializers.SerializerMethodField()
    conversion = serializers.SerializerMethodField()
    spent_impressions = serializers.SerializerMethodField()
    spent_clicks = serializers.SerializerMethodField()
    spent_total = serializers.SerializerMethodField()

    def get_impressions_count(self, obj):
        self.impressions_count = obj.campaigns.aggregate(total=Count("impressions"))[
            "total"
        ]  # FIX
        if not self.impressions_count:
            self.impressions_count = 0
        return self.impressions_count

    def get_clicks_count(self, obj):
        self.clicks_count = obj.campaigns.aggregate(total=Count("clicks"))[
            "total"
        ]  # FIX
        if not self.clicks_count:
            self.clicks_count = 0
        return self.clicks_count

    def get_conversion(self, obj):
        self.conversion = 0
        if not self.impressions_count == 0:
            self.conversion = (self.clicks_count / self.impressions_count) * 100
        return self.conversion

    def get_spent_impressions(self, obj):
        self.spent_impressions = obj.campaigns.aggregate(
            total=Sum("impressions__cost")
        )["total"]  # FIX
        if not self.spent_impressions:
            self.spent_impressions = 0
        return self.spent_impressions

    def get_spent_clicks(self, obj):
        self.spent_clicks = obj.campaigns.aggregate(total=Sum("clicks__cost"))[
            "total"
        ]  # FIX
        if not self.spent_clicks:
            self.spent_clicks = 0
        return self.spent_clicks

    def get_spent_total(self, obj):
        return self.spent_clicks + self.spent_impressions

    class Meta:
        model = Advertiser
        fields = (
            "impressions_count",
            "clicks_count",
            "conversion",
            "spent_impressions",
            "spent_clicks",
            "spent_total",
        )


class StatisticsSerializer(serializers.Serializer):
    impressions_count = serializers.IntegerField()
    clicks_count = serializers.IntegerField()
    conversion = serializers.FloatField()
    spent_impressions = serializers.FloatField()
    spent_clicks = serializers.FloatField()
    spent_total = serializers.FloatField()
