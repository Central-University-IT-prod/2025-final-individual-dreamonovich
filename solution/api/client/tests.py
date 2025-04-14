from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from .models import Client


class ClientsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sample_client = Client.objects.create(
            id=uuid.uuid4(),
            login="testuser",
            age=30,
            location="Test City",
            gender="MALE",
        )

    def test_get_client_by_id(self):
        url = f"/clients/{self.sample_client.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["client_id"], str(self.sample_client.id))
        self.assertEqual(response.data["login"], "testuser")

    def test_upsert_clients_bulk_create(self):
        url = "/clients/bulk"
        data = [
            {
                "client_id": str(uuid.uuid4()),
                "login": "newuser",
                "age": 25,
                "location": "New City",
                "gender": "FEMALE",
            }
        ]
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 2)

    def test_upsert_clients_bulk_update(self):
        url = "/clients/bulk"
        data = [
            {
                "client_id": str(self.sample_client.id),
                "login": "updateduser",
                "age": 35,
                "location": "Updated City",
                "gender": "FEMALE",
            }
        ]
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.sample_client.refresh_from_db()
        self.assertEqual(self.sample_client.login, "updateduser")
