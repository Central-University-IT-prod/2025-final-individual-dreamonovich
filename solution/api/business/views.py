import logging
from concurrent.futures import ThreadPoolExecutor

from django.db.models import Sum, Min, Max
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import (
    RetrieveAPIView,
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from app.exceptions import CustomAPIException
from app.paginations import PurePageNumberPagination
from app.utils import get_current_day
from business.ai import generate_advertising_text
from business.algorithm import compute_ad_score, get_max_P
from business.models import Advertiser, Score, Campaign
from business.serializers import (
    AdvertiserSerializer,
    CreateScoreBodySerializer,
    CampaignSerializer,
    CreateCampaignSerializer,
    StatisticsSerializer,
)
from business.grafana import (
    process_grafana_user,
    delete_advertiser_from_grafana,
)
from business.utils import set_local_cache_cur_min_max_score
from client.models import Client, Impression, Click

from django.db import transaction


logger = logging.getLogger(__name__)


class BulkCreateAdvertisersView(APIView):
    def post(self, request, *args, **kwargs):
        advertisers_data = request.data
        advertisers = []
        processed_ids = set()

        for advertiser_data in advertisers_data:
            serializer = AdvertiserSerializer(data=advertiser_data)
            serializer.is_valid(raise_exception=True)

            advertiser_id = serializer.validated_data["id"]
            if advertiser_id in processed_ids:
                raise CustomAPIException(
                    detail=f"{advertiser_id} встречается несколько раз.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            processed_ids.add(advertiser_id)
            advertisers.append(Advertiser(**serializer.validated_data))

        with transaction.atomic():
            Advertiser.objects.bulk_create(
                advertisers,
                update_conflicts=True,
                unique_fields=["id"],
                update_fields=["name"],
            )

        logger.info("Starting advertisers grafana accounts creation")
        executor = ThreadPoolExecutor(max_workers=10)
        executor.map(process_grafana_user, advertisers)

        return Response(
            AdvertiserSerializer(advertisers, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class GetAdvertiserView(RetrieveAPIView):
    serializer_class = AdvertiserSerializer
    queryset = Advertiser.objects.all()
    lookup_field = "id"


class CreateScoreView(APIView):
    def post(self, request, *args, **kwargs):
        scores_data = request.data
        body_serializer = CreateScoreBodySerializer(data=scores_data)
        body_serializer.is_valid(raise_exception=True)

        if not (
            client := Client.objects.filter(
                pk=body_serializer.validated_data.get("client_id")
            ).first()
        ):
            raise CustomAPIException(
                detail="Клиент не найден.", status_code=status.HTTP_404_NOT_FOUND
            )
        if not (
            advertiser := Advertiser.objects.filter(
                pk=body_serializer.validated_data.get("advertiser_id")
            ).first()
        ):
            raise CustomAPIException(
                detail="Рекламодатель не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        Score.objects.update_or_create(
            client=client,
            advertiser=advertiser,
            score=body_serializer.validated_data.get("score"),
        )
        set_local_cache_cur_min_max_score()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class CreateCampaignView(ListAPIView, CreateAPIView):
    serializer_class = CampaignSerializer
    pagination_class = PurePageNumberPagination

    def create(self, request, *args, **kwargs):
        advertiser_id = kwargs.get("advertiser_id")
        if not Advertiser.objects.filter(pk=advertiser_id).exists():
            raise CustomAPIException(
                detail="Рекламодатель не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer_data = {**request.data, "advertiser_id": advertiser_id}
        serializer = CreateCampaignSerializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        advertiser_id = self.kwargs.get("advertiser_id")
        return Campaign.objects.filter(advertiser_id=advertiser_id)


class RetrieveUpdateDestroyCampaignView(RetrieveUpdateDestroyAPIView):
    serializer_class = CampaignSerializer

    def get_object(self):
        advertiser_id = self.kwargs.get("advertiser_id")
        if not Advertiser.objects.filter(pk=advertiser_id).exists():
            raise CustomAPIException(
                detail="Рекламодатель не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        campaign_id = self.kwargs.get("campaign_id")
        if not (campaign := Campaign.objects.filter(pk=campaign_id).first()):
            raise CustomAPIException(
                detail="Кампания не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return campaign


class StatisticsView(GenericAPIView):
    def get_impressions(self, day=None):
        return Impression.objects.all()

    def get_clicks(self, day=None):
        return Click.objects.all()

    def get_statistics_values(self, impressions, clicks):
        impressions_count = impressions.count()
        clicks_count = clicks.count()
        conversion = round(
            ((clicks_count / impressions_count * 100) if impressions_count > 0 else 0),
            2,
        )
        spent_impressions = impressions.aggregate(total=Sum("cost"))["total"] or 0
        spent_clicks = clicks.aggregate(total=Sum("cost"))["total"] or 0  # FIX
        spent_total = spent_impressions + spent_clicks

        return {
            "impressions_count": impressions_count,
            "clicks_count": clicks_count,
            "conversion": conversion,
            "spent_impressions": spent_impressions,
            "spent_clicks": spent_clicks,
            "spent_total": spent_total,
        }

    def get_statistics(self):
        return self.get_statistics_values(self.get_impressions(), self.get_clicks())

    def get(self, request, *args, **kwargs):
        statistics_data = self.get_statistics()
        return Response(
            StatisticsSerializer(statistics_data).data, status=status.HTTP_200_OK
        )


class DailyStatisticsView(StatisticsView):
    def get_statistics(self):
        current_day = get_current_day()

        daily_stats = []
        for day in range(1, current_day + 1):  # TODO: Ticket 8373
            impressions = self.get_impressions(day)
            clicks = self.get_clicks(day)
            daily_stats.append(self.get_statistics_values(impressions, clicks))

        return daily_stats

    def get(self, request, *args, **kwargs):
        statistics_data = self.get_statistics()
        return Response(
            StatisticsSerializer(statistics_data, many=True).data,
            status=status.HTTP_200_OK,
        )


class AdvertiserStatisticsView(StatisticsView):
    def get_advertiser(self):
        advertiser_id = self.kwargs.get("advertiser_id")
        if not (advertiser := Advertiser.objects.filter(pk=advertiser_id).first()):
            raise CustomAPIException(
                detail="Рекламодатель не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return advertiser

    def get_impressions(self, day=None):
        advertiser = self.get_advertiser()
        if day is None:
            return Impression.objects.filter(advertiser_id=advertiser.id)
        return Impression.objects.filter(advertiser_id=advertiser.id, day=day)

    def get_clicks(self, day=None):
        advertiser = self.get_advertiser()
        if day is None:
            return Click.objects.filter(advertiser_id=advertiser.id)
        return Click.objects.filter(advertiser_id=advertiser.id, day=day)


class CampaignStatisticsView(StatisticsView):
    def get_campaign(self):
        campaign_id = self.kwargs.get("campaign_id")
        if not (campaign := Campaign.objects.filter(pk=campaign_id).first()):
            raise CustomAPIException(
                detail="Кампания не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return campaign

    def get_impressions(self, day=None):
        campaign = self.get_campaign()
        if day is None:
            return Impression.objects.filter(advertisement_id=campaign.id)
        return Impression.objects.filter(advertisement_id=campaign.id, day=day)

    def get_clicks(self, day=None):
        campaign = self.get_campaign()
        if day is None:
            return Click.objects.filter(advertisement_id=campaign.id)
        return Click.objects.filter(advertisement_id=campaign.id, day=day)


class AdvertiserDailyStatisticsView(DailyStatisticsView, AdvertiserStatisticsView):
    pass


class CampaignDailyStatisticsView(DailyStatisticsView, CampaignStatisticsView):
    pass


@api_view(["POST", "PUT"])
def update_add_campaign_image_view(request, *args, **kwargs):
    advertiser_id = kwargs.get("advertiser_id")
    if not Advertiser.objects.filter(pk=advertiser_id).exists():
        raise CustomAPIException(
            detail="Рекламодатель не найден.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    campaign_id = kwargs.get("campaign_id")
    if not (campaign := Campaign.objects.filter(pk=campaign_id).first()):
        raise CustomAPIException(
            detail="Кампания не найден.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if not (image := request.FILES.get("image")):
        raise CustomAPIException(
            detail="image обязателен.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    campaign.image.save(image.name, image)
    return Response({"image": campaign.image.url}, status=status.HTTP_200_OK)


class GenerateAdTextView(APIView):
    def get(self, request, *args, **kwargs):
        targeting = request.query_params.get("targeting")
        if not (title := request.query_params.get("title")):
            raise CustomAPIException(
                "Укажите title",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        generated_text = generate_advertising_text(title, targeting)
        return Response({"text": generated_text}, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_score(request, *args, **kwargs):
    campaign_id = request.query_params.get("campaign_id")
    if not (campaign := Campaign.objects.filter(pk=campaign_id).first()):
        raise CustomAPIException(
            detail="Кампания не найден.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    client_id = request.query_params.get("client_id")
    if not (client := Client.objects.filter(pk=client_id).first()):
        raise CustomAPIException(
            detail="Клиент не найден.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    current_impressions = Impression.objects.filter(
        advertisement_id=campaign.id
    ).count()
    current_clicks = Click.objects.filter(advertisement_id=campaign.id).count()
    set_local_cache_cur_min_max_score()
    ml_min, ml_max = Score.get_min_and_max()
    ml_score_inctance = Score.objects.filter(
        client=client, advertiser=campaign.advertiser
    ).first()
    ml_score = ml_score_inctance.score if ml_score_inctance else 0

    campaigns = client.get_targered_and_not_impressed_campaigns()
    max_P = get_max_P(client, campaigns)

    score = compute_ad_score(
        campaign=campaign,
        client=client,
        current_impressions=current_impressions,
        current_clicks=current_clicks,
        ml_min=ml_min if ml_min else ml_score,
        ml_max=ml_max if ml_max else ml_score,
        ml_score=ml_score,
        client_max_P=max_P,
    )

    return Response({"score": score}, status=status.HTTP_200_OK)


@api_view(["POST"])
def delete_grafana_users(request, *args, **kwargs):
    advertisers = Advertiser.objects.all()
    for advertiser in advertisers:
        delete_advertiser_from_grafana(advertiser)

    return Response({"status": "ok"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def register_advertiser_to_grafana(request, *args, **kwargs):
    advertiser_id = kwargs.get("advertiser_id")
    if not (advertiser := Advertiser.objects.filter(pk=advertiser_id).first()):
        raise CustomAPIException(
            detail="Рекламодатель не найден.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    password = process_grafana_user(advertiser)
    return Response({"login": advertiser.id, "password": password})
