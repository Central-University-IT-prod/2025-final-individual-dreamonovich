import logging

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

logger = logging.getLogger(__name__)


def create_grafana_user(advertiser):
    url = f"{settings.GRAFANA_API_URL}/api/admin/users"
    basic = HTTPBasicAuth("admin", "admin")
    headers = {"Content-Type": "application/json"}
    data = {
        "name": advertiser.name,
        "login": str(advertiser.id),
        "password": settings.GRAFANA_ADVERTISER_DEFAULT_PASSWORD,
    }

    try:
        response = requests.post(url, headers=headers, json=data, auth=basic)
        response.raise_for_status()
        return response.json().get("id")
    except requests.RequestException as e:
        logger.error(f"Failed to create Grafana user for {advertiser.id}: {e}")
        return None


def add_user_to_grafana_team(user_id):
    if not user_id:
        return
    url = f"{settings.GRAFANA_API_URL}/api/teams/{settings.GRAFANA_TEAM_ID}/members"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GRAFANA_API_KEY}",
    }
    data = {"userId": user_id}

    try:
        requests.post(url, headers=headers, json=data)
    except requests.RequestException as e:
        logger.error(f"Failed to add user {user_id} to Grafana team: {e}")


def process_grafana_user(advertiser):
    user_id = create_grafana_user(advertiser)
    if user_id:
        add_user_to_grafana_team(user_id)


def get_grafana_user(user_login):
    url = f"{settings.GRAFANA_API_URL}/api/users/lookup"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GRAFANA_API_KEY}",
    }
    params = {"loginOrEmail": user_login}

    response = requests.get(url, headers=headers, params=params)
    return response.json()


def delete_grafana_user(user_id):
    url = f"{settings.GRAFANA_API_URL}/api/admin/users/{user_id}"

    basic = HTTPBasicAuth("admin", "admin")
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.delete(url, headers=headers, auth=basic)

    return response.json()


def delete_advertiser_from_grafana(advertiser):
    response = get_grafana_user(advertiser.id)
    if grafana_user_id := response.get("id"):
        delete_grafana_user(grafana_user_id)
