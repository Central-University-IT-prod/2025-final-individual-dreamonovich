from aiogram.types import User
from aiogram_dialog import DialogManager

from db.db import (
    get_advertiser_campaigns,
    get_advertiser_id,
    get_advertiser_statistics,
    get_advertiser_daily_statistics,
)
from db.models import Advertiser


async def main_menu_getter(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
):
    data = {}
    advertiser_id = await get_advertiser_id(
        str(event_from_user.id), dialog_data=dialog_manager.dialog_data
    )
    advertiser = await Advertiser.filter(id=str(advertiser_id)).first()
    data["advertiser_name"] = advertiser.name

    if not (page := dialog_manager.dialog_data.get("campaign_page")):
        page = 1
        dialog_manager.dialog_data["campaign_page"] = page
    advertiser_campaigns, max_page = await get_advertiser_campaigns(
        advertiser, page=page
    )

    if not (next_page := dialog_manager.dialog_data.get("next_page")):
        next_page = page + 1 if page != max_page else 1
    if not (previous_page := dialog_manager.dialog_data.get("previous_page")):
        previous_page = page - 1 if page != 1 else max_page

    dialog_manager.dialog_data["max_campaign_page"] = max_page
    data["previous_page"] = previous_page
    data["next_page"] = next_page
    data["max_campaign_page"] = max_page
    data["campaign_page"] = page
    data["campaigns"] = [
        {"title": campaign.ad_title, "id": str(campaign.id)}
        for i, campaign in enumerate(advertiser_campaigns)
    ]

    return data


async def get_advertiser_info(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
):
    advertiser_id = await get_advertiser_id(
        str(event_from_user.id), dialog_data=dialog_manager.dialog_data
    )
    advertiser = await Advertiser.filter(id=str(advertiser_id)).first()
    dialog_manager.dialog_data.pop("daily_statistics", None)

    data = {
        "name": advertiser.name,
        "id": advertiser.id,
    }
    return data


async def advertiser_statistics_getter(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
):
    advertiser_id = await get_advertiser_id(
        str(event_from_user.id), dialog_data=dialog_manager.dialog_data
    )
    statistics = await get_advertiser_statistics(advertiser_id)
    data = {"statistics": statistics}
    return data


async def advertiser_daily_statistics_getter(
    dialog_manager: DialogManager, event_from_user: User, **kwargs
):
    advertiser_id = await get_advertiser_id(
        str(event_from_user.id), dialog_data=dialog_manager.dialog_data
    )
    if not dialog_manager.dialog_data.get("daily_statistics"):
        statistics_data = await get_advertiser_daily_statistics(advertiser_id)
        dialog_manager.dialog_data["daily_statistics"] = statistics_data

    statistics_data = dialog_manager.dialog_data["daily_statistics"]
    if not (page := dialog_manager.dialog_data.get("stat_page")):
        page = 1
        dialog_manager.dialog_data["stat_page"] = page
    max_page = len(statistics_data)

    if not (next_page := dialog_manager.dialog_data.get("next_page")):
        next_page = page + 1 if page != max_page else 1
    if not (previous_page := dialog_manager.dialog_data.get("previous_page")):
        previous_page = page - 1 if page != 1 else max_page
    data = {"statistics": statistics_data[page - 1]}
    dialog_manager.dialog_data["max_stat_page"] = max_page
    data["previous_page"] = previous_page
    data["next_page"] = next_page
    data["max_stat_page"] = max_page
    data["stat_page"] = page
    return data
