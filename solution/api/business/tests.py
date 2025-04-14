from rest_framework.exceptions import ValidationError

from app.utils import set_day
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from client.models import Client
from unittest.mock import patch
from client.models import (
    Advertiser,
    Campaign,
    Score,
    Impression,
)


class AdvertisersTests(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = APIClient()
        self.sample_advertiser = Advertiser.objects.create(
            id=uuid.uuid4(), name="Test Advertiser"
        )

    def test_get_advertiser_by_id(self):
        url = f"/advertisers/{self.sample_advertiser.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Advertiser")

    def test_upsert_advertisers_bulk(self):
        url = "/advertisers/bulk"
        data = [{"advertiser_id": str(uuid.uuid4()), "name": "New Advertiser"}]
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Advertiser.objects.count(), 2)

    def test_upsert_ml_score(self):
        client = Client.objects.create(
            id=uuid.uuid4(),
            login="mlclient",
            age=28,
            location="ML City",
            gender="FEMALE",
        )
        url = "/ml-scores"
        data = {
            "client_id": str(client.id),
            "advertiser_id": str(self.sample_advertiser.id),
            "score": 95,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Score.objects.filter(
                client=client, advertiser=self.sample_advertiser
            ).exists()
        )


class CampaignsTests(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = APIClient()
        self.advertiser = Advertiser.objects.create(
            id=uuid.uuid4(), name="Campaign Advertiser"
        )
        self.campaign_data = {
            "impressions_limit": 1000,
            "clicks_limit": 100,
            "cost_per_impression": 0.5,
            "cost_per_click": 5.0,
            "ad_title": "Test Campaign",
            "ad_text": "Test Ad Text",
            "start_date": 1,
            "end_date": 30,
            "targeting": {
                "gender": "ALL",
                "age_from": 18,
                "age_to": 65,
                "location": "Test City",
            },
        }

    def test_create_campaign(self):
        url = f"/advertisers/{self.advertiser.id}/campaigns"
        response = self.client.post(url, self.campaign_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Campaign.objects.count(), 1)

    def test_list_campaigns(self):
        self.client.post(
            f"/advertisers/{self.advertiser.id}/campaigns",
            self.campaign_data,
            format="json",
        )
        url = f"/advertisers/{self.advertiser.id}/campaigns?page=1&size=10"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_campaign(self):
        post_url = f"/advertisers/{self.advertiser.id}/campaigns"
        post_response = self.client.post(post_url, self.campaign_data, format="json")
        campaign_id = post_response.data["campaign_id"]
        update_data = {"ad_title": "Updated Title"}
        update_url = f"/advertisers/{self.advertiser.id}/campaigns/{campaign_id}"
        response = self.client.put(update_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campaign = Campaign.objects.get(id=campaign_id)
        self.assertEqual(campaign.ad_title, "Updated Title")

    def test_delete_campaign(self):
        post_url = f"/advertisers/{self.advertiser.id}/campaigns"
        post_response = self.client.post(post_url, self.campaign_data, format="json")
        campaign_id = post_response.data["campaign_id"]
        delete_url = f"/advertisers/{self.advertiser.id}/campaigns/{campaign_id}"
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Campaign.objects.count(), 0)


class AdsTests(TestCase):
    databases = "__all__"
    databases = "__all__"

    def setUp(self):
        self.client = APIClient()
        self.client_obj = Client.objects.create(
            id=uuid.uuid4(), login="adclient", age=25, location="Ad City", gender="MALE"
        )
        self.advertiser = Advertiser.objects.create(id=uuid.uuid4(), name="Advertiser")
        Score.objects.create(
            client=self.client_obj, advertiser=self.advertiser, score=95
        )
        self.campaign = Campaign.objects.create(
            id=uuid.uuid4(),
            advertiser=self.advertiser,
            impressions_limit=1000,
            clicks_limit=100,
            cost_per_impression=0.5,
            cost_per_click=5.0,
            ad_title="Test Ad",
            ad_text="Test Text",
            start_date=1,
            end_date=30,
            targeted_gender="MALE",
            targeted_age_from=20,
            targeted_age_to=30,
            targeted_location="Ad City",
        )
        set_day(5)

    def test_get_ad_for_client(self):
        url = f"/ads?client_id={self.client_obj.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["advertiser_id"], self.advertiser.id)


class TimeTests(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = APIClient()

    def test_advance_day(self):
        url = "/time/advance"
        data = {"current_date": 5}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_date"], 5)
        # Verify subsequent operations use the new date


class ClientModelTests(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client = Client.objects.create(
            id=uuid.uuid4(),
            login="testclient",
            age=25,
            location="Test City",
            gender="MALE",
        )
        self.advertiser = Advertiser.objects.create(
            id=uuid.uuid4(), name="Test Advertiser"
        )

    def test_profanity_validation(self):
        with self.assertRaises(ValidationError):
            Client.objects.create(
                id=uuid.uuid4(),
                login="shithead",
                age=30,
                location="Clean City",
                gender="MALE",
            )

    def test_get_relevant_advertisement_edge_cases(self):
        # Test campaign targeting boundary conditions
        campaign = Campaign.objects.create(
            id=uuid.uuid4(),
            advertiser=self.advertiser,
            impressions_limit=100,
            clicks_limit=10,
            cost_per_impression=0.5,
            cost_per_click=5.0,
            ad_title="Test Ad",
            ad_text="Test Content",
            start_date=1,
            end_date=30,
            targeted_gender="MALE",
            targeted_age_from=25,  # Exact match
            targeted_age_to=25,  # Exact match
            targeted_location="Test City",
        )

        # Should match exactly
        relevant = self.client.get_relevant_advertisement()
        self.assertEqual(relevant.id, campaign.id)

        # Test age boundaries
        self.client.age = 24
        self.client.save()
        self.assertIsNone(self.client.get_relevant_advertisement())

    def test_ml_score_normalization(self):
        # Test when all scores are the same
        Score.objects.create(client=self.client, advertiser=self.advertiser, score=50)
        Score.objects.create(
            client=Client.objects.create(
                id=uuid.uuid4(),
                login="other",
                age=30,
                location="Other",
                gender="FEMALE",
            ),
            advertiser=self.advertiser,
            score=50,
        )

        normalized = self.client.get_normalized_ml_score(self.advertiser)
        self.assertEqual(normalized, 0.5)  # Should handle min=max case


class CampaignModelTests(TestCase):
    databases = "__all__"

    def test_campaign_targeting_null_handling(self):
        advertiser = Advertiser.objects.create(id=uuid.uuid4(), name="Test")
        campaign = Campaign.objects.create(
            id=uuid.uuid4(),
            advertiser=advertiser,
            impressions_limit=100,
            clicks_limit=10,
            cost_per_impression=0.5,
            cost_per_click=5.0,
            ad_title="Test",
            ad_text="Content",
            start_date=1,
            end_date=30,
            # All targeting fields null
        )

        client = Client.objects.create(
            id=uuid.uuid4(), login="any", age=99, location="Nowhere", gender="FEMALE"
        )

        self.assertIn(campaign, client.get_targered_and_not_impressed_campaigns())

    def test_campaign_date_validation(self):
        advertiser = Advertiser.objects.create(id=uuid.uuid4(), name="Test")
        with self.assertRaises(ValidationError):
            Campaign.objects.create(
                id=uuid.uuid4(),
                advertiser=advertiser,
                impressions_limit=100,
                clicks_limit=10,
                cost_per_impression=0.5,
                cost_per_click=5.0,
                ad_title="Test",
                ad_text="Content",
                start_date=30,
                end_date=1,  # Invalid date range
            )


class AdsEndpointTests(TestCase):
    databases = "__all__"

    def setUp(self):
        self.client_user = Client.objects.create(
            id=uuid.uuid4(),
            login="adviewer",
            age=25,
            location="Test City",
            gender="MALE",
        )
        self.advertiser = Advertiser.objects.create(
            id=uuid.uuid4(), name="Test Advertiser"
        )
        self.campaign = Campaign.objects.create(
            id=uuid.uuid4(),
            advertiser=self.advertiser,
            impressions_limit=1,  # Very low limit for testing
            clicks_limit=1,
            cost_per_impression=0.5,
            cost_per_click=5.0,
            ad_title="Test Ad",
            ad_text="Test Content",
            start_date=1,
            end_date=30,
            targeted_gender="MALE",
            targeted_age_from=20,
            targeted_age_to=30,
            targeted_location="Test City",
        )
        Score.objects.create(
            client=self.client_user, advertiser=self.advertiser, score=100
        )
        self.api_client = APIClient()

    @patch("app.utils.get_current_day")
    def test_ad_selection_with_date_boundaries(self, mock_day):
        mock_day.return_value = 0  # Before campaign start
        response = self.api_client.get(f"/ads?client_id={self.client_user.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        mock_day.return_value = 1  # Exact start date
        response = self.api_client.get(f"/ads?client_id={self.client_user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_day.return_value = 30  # Exact end date
        response = self.api_client.get(f"/ads?client_id={self.client_user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_day.return_value = 31  # After campaign end
        response = self.api_client.get(f"/ads?client_id={self.client_user.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_impression_limit_enforcement(self):
        # First request should succeed
        response = self.api_client.get(f"/ads?client_id={self.client_user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Second request should return no content
        response = self.api_client.get(f"/ads?client_id={self.client_user.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class StatisticsTests(TestCase):
    databases = "__all__"

    def setUp(self):
        self.api_client = APIClient()
        self.advertiser = Advertiser.objects.create(id=uuid.uuid4(), name="Stats Test")
        self.campaign = Campaign.objects.create(
            id=uuid.uuid4(),
            advertiser=self.advertiser,
            impressions_limit=100,
            clicks_limit=10,
            cost_per_impression=1.0,
            cost_per_click=5.0,
            ad_title="Stats Ad",
            ad_text="Content",
            start_date=1,
            end_date=30,
        )
        self.client_user = Client.objects.create(
            id=uuid.uuid4(),
            login="statsuser",
            age=25,
            location="Stats City",
            gender="MALE",
        )

    def test_click_cost_calculation(self):
        # Record impression first
        Impression.objects.create(
            client_id=self.client_user.id,
            cost=self.campaign.cost_per_impression,
            advertiser_id=self.advertiser.id,
            advertisement_id=self.campaign.id,
            day=1,
        )

        # Record click
        click_url = f"/ads/{self.campaign.id}/click"
        response = self.api_client.post(
            click_url, {"client_id": str(self.client_user.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify statistics
        stats_url = f"/stats/campaigns/{self.campaign.id}"
        response = self.api_client.get(stats_url)
        self.assertEqual(
            response.data["spent_total"],
            self.campaign.cost_per_impression + self.campaign.cost_per_click,
        )

    def test_daily_stats_aggregation(self):
        # Test ClickHouse-specific aggregation
        with patch("app.models.get_current_day", return_value=5):
            for _ in range(3):
                Impression.objects.create(
                    client_id=self.client_user.id,
                    cost=self.campaign.cost_per_impression,
                    advertiser_id=self.advertiser.id,
                    advertisement_id=self.campaign.id,
                    day=5,
                )

        daily_url = f"/stats/campaigns/{self.campaign.id}/daily"
        response = self.api_client.get(daily_url)
        day5_stats = next(d for d in response.data if d["date"] == 5)
        self.assertEqual(day5_stats["impressions_count"], 3)
