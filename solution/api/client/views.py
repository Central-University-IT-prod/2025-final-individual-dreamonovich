from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from app.exceptions import CustomAPIException
from app.utils import get_current_day
from business.models import Campaign
from .models import Client, Click, Impression
from .serializers import ClientSerializer


class BulkCreateClientsView(APIView):
    def post(self, request, *args, **kwargs):
        client_data = request.data

        clients = []
        processed_ids = []
        for client_data in client_data:
            serializer = ClientSerializer(data=client_data)
            serializer.is_valid(raise_exception=True)

            if (client_id := serializer.validated_data["id"]) in processed_ids:
                raise CustomAPIException(
                    detail=f"{client_id} встречается несколько раз.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            processed_ids.append(client_id)

            client = Client(**serializer.validated_data)
            clients.append(client)
        Client.objects.bulk_create(
            clients,
            update_conflicts=True,
            unique_fields=["id"],
            update_fields=["login", "age", "location", "gender"],
        )

        return Response(
            ClientSerializer(clients, many=True).data, status=status.HTTP_201_CREATED
        )


class GetClientView(RetrieveAPIView):
    serializer_class = ClientSerializer
    queryset = Client.objects.all()
    lookup_field = "id"


@require_GET
def get_advertisement_view(request):
    client_id = request.GET.get("client_id")
    if not client_id:
        return JsonResponse({"detail": "client_id not provided"}, status=400)

    try:
        client = Client.objects.get(pk=client_id)
    except Client.DoesNotExist:
        return JsonResponse({"detail": "client not found"}, status=404)

    current_day = get_current_day()
    max_retries = 50

    sorted_advertisements = client.get_relevant_advertisement(current_day)
    if not sorted_advertisements:
        return JsonResponse({"message": "not relevant ads"}, status=404)

    for tries in range(min(max_retries, len(sorted_advertisements))):
        try:
            advertisement = sorted_advertisements[tries]
            with transaction.atomic():
                impression, created = Impression.objects.get_or_create(
                    client_id=client_id,
                    advertiser_id=advertisement.advertiser_id,
                    advertisement=advertisement,
                    day=current_day,
                    defaults={"cost": advertisement.cost_per_impression},
                )
                if created:
                    Campaign.objects.filter(id=advertisement.id).update(impressions_count=F('impressions_count') + 1)

                    response_data = {
                        "ad_id": str(advertisement.id),
                        "ad_title": advertisement.ad_title,
                        "ad_text": advertisement.ad_text,
                        "advertiser_id": advertisement.advertiser_id,
                    }
                    return JsonResponse({k: v for k, v in response_data.items() if v is not None})
        except IntegrityError:
            continue

    return JsonResponse({"message": "No new advertisements available"}, status=404)


class ClickAdvertisementView(APIView):
    def post(self, request, *args, **kwargs):
        client_id = request.data.get("client_id")
        if not Client.objects.filter(pk=client_id).exists():
            raise CustomAPIException(
                detail="Клиент не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        campaign_id = kwargs.get("campaign_id")
        if not (campaign := Campaign.objects.filter(pk=campaign_id).first()):
            raise CustomAPIException(
                detail="Кампания не найден.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if not Impression.objects.filter(
            advertisement_id=campaign_id, client_id=client_id
        ).exists():
            raise CustomAPIException(
                detail="Вы не можете перейти по рекламе без показа.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        current_day = get_current_day()
        with transaction.atomic():
            Click.objects.get_or_create(
                client_id=client_id,
                advertisement_id=campaign_id,
                advertiser_id=campaign.advertiser_id,
                day=current_day,
                cost=campaign.cost_per_click,
            )
            Campaign.objects.filter(id=campaign_id).update(clicks_count=F('clicks_count') + 1)

        return Response(status=status.HTTP_204_NO_CONTENT)
