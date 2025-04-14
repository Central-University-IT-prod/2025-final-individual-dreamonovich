import os
from math import ceil
from pathlib import Path
from typing import List

from aiogram.client.session import aiohttp
from tortoise import Tortoise

from .models import TelegramUser, Advertiser, Campaign


async def user_is_registered(telegram_id: str) -> bool:
    return await TelegramUser.filter(telegram_id=telegram_id).exists()


async def advertiser_exists(advertiser_id: str) -> bool:
    return await Advertiser.filter(id=advertiser_id).exists()


async def register_user(telegram_id: str, advertiser_id: str) -> None:
    await TelegramUser.create(telegram_id=telegram_id, advertiser_id=advertiser_id)


async def get_advertiser_id(telegram_id: str, dialog_data=None) -> str:
    if dialog_data is None:
        dialog_data = {}
    if not (advertiser_id := dialog_data.get("advertiser_id")):
        user = await TelegramUser.filter(telegram_id=telegram_id).first()
        advertiser_id = str(user.advertiser_id)
        dialog_data["advertiser_id"] = advertiser_id
    return advertiser_id


async def get_advertiser_campaigns(advertiser: Advertiser, page_size=6, page=0):
    campaigns = (
        await Campaign.filter(advertiser_id=advertiser.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    max_page = ceil(
        await Campaign.filter(advertiser_id=advertiser.id).count() / page_size
    )
    return campaigns, max_page


async def get_campaign(campaign_id: str) -> Campaign:
    return await Campaign.get(id=campaign_id)


async def get_image_path(url: str, save_dir: str = "images") -> Path:
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    filename = url.split("/")[-1]  # Extract filename from URL
    file_path = save_path / filename

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await response.read())
                return file_path.resolve()
            else:
                raise Exception(
                    f"Failed to download {url}, status code: {response.status}"
                )


async def send_create_campaign(campaign_data: dict, advertiser_id: str = None):
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/advertisers/{advertiser_id}/campaigns"

    # Remove image data from campaign_data so it doesn't get JSON serialized
    image_data = campaign_data.pop("image", None)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=campaign_data) as response:
            response_data = await response.json()
    campaign_id = response_data["campaign_id"]

    if image_data:
        image_upload_url = (
            f"{api_url}/advertisers/{advertiser_id}/campaigns/{campaign_id}/image"
        )
        form = aiohttp.FormData()
        form.add_field(
            "image",
            image_data,  # This is your BytesIO object
            filename="image.jpg",  # Provide a filename
            content_type="image/jpeg",  # Set the correct content type
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(image_upload_url, data=form) as response:
                image_data = await response.json()  # Return response
        response_data["image"] = image_data["image"]
    return response_data


async def get_advertiser_info(advertiser_id: str) -> Advertiser:
    return await Advertiser.get(id=advertiser_id)


async def get_gaily_statistics(campaign_id: str) -> List:
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/stats/campaigns/{campaign_id}/daily"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_data = await response.json()
    return response_data


async def get_all_statistics(campaign_id: str) -> List:
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/stats/campaigns/{campaign_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_data = await response.json()
    return response_data


async def init():
    await Tortoise.init(
        db_url=os.environ.get(
            "DB_URL", "postgres://postgres:postgres@localhost:5435/advertising"
        ),
        modules={"models": ["db.models"]},
    )

    await Tortoise.generate_schemas()


async def send_update_campaign(
    campaign_data: dict, advertiser_id: str = None, campaign_id: str = None
):
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/advertisers/{advertiser_id}/campaigns/{campaign_id}"

    # Remove image data from campaign_data so it doesn't get JSON serialized
    image_data = campaign_data.pop("image", None)
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=campaign_data) as response:
            response_data = await response.json()
    campaign_id = response_data["campaign_id"]

    if image_data:
        image_upload_url = (
            f"{api_url}/advertisers/{advertiser_id}/campaigns/{campaign_id}/image"
        )
        form = aiohttp.FormData()
        form.add_field(
            "image",
            image_data,  # This is your BytesIO object
            filename="image.jpg",  # Provide a filename
            content_type="image/jpeg",  # Set the correct content type
        )
        async with aiohttp.ClientSession() as session:
            async with session.put(image_upload_url, data=form) as response:
                image_data = await response.json()  # Return response
        response_data["image"] = image_data["image"]
    return response_data


async def get_current_day():
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/time/current"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_data = await response.json()  # Return response
    return response_data["current_date"]


async def get_advertiser_statistics(advertiser_id: str):
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/stats/advertisers/{advertiser_id}/campaigns"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_data = await response.json()
    return response_data


async def get_advertiser_daily_statistics(advertiser_id: str):
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/stats/advertisers/{advertiser_id}/campaigns/daily"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_data = await response.json()
    return response_data

async def generate_text(title, targeting=None):
    api_url = os.getenv("API_URL", "http://localhost:8080")
    url = f"{api_url}/generate-text"

    params = {
        "title": title,
        "targeting": targeting,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response_data = await response.json()
    return response_data["text"]