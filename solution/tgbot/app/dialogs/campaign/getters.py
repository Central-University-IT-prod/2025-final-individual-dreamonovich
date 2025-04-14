from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db.db import (
    get_campaign,
    get_image_path,
    get_gaily_statistics,
    get_all_statistics,
)

from db.db import generate_text


async def campaign_getter(dialog_manager: DialogManager, **kwargs):
    campaign = await get_campaign(campaign_id=dialog_manager.start_data["campaign_id"])
    dialog_manager.dialog_data.pop("daily_statisticss", None)
    targeted_age = ""
    if campaign.targeted_age_from is not None:
        targeted_age = f"с {campaign.targeted_age_from} "
    if campaign.targeted_age_to is not None:
        targeted_age += f"до {campaign.targeted_age_to}"
    if not targeted_age:
        targeted_age = "Все"
    match campaign.targeted_gender:
        case "MALE":
            targeted_gender = "Мужской"
        case "FEMALE":
            targeted_gender = "Женский"
        case _:
            targeted_gender = "Все"

    image = None
    if campaign.image.url:
        image_path = await get_image_path(campaign.image.url)
        image = MediaAttachment(path=image_path, type=ContentType.PHOTO)
    return {
        "cost_per_impression": campaign.cost_per_impression,
        "cost_per_click": campaign.cost_per_click,
        "title": campaign.ad_title,
        "text": campaign.ad_text,
        "dates": f"Действительна с {campaign.start_date} по {campaign.end_date}",
        "targeted_gender": targeted_gender,
        "targeted_age": targeted_age,
        "targeted_location": campaign.targeted_location
        if campaign.targeted_location
        else "Все",
        "image": image,
        "has_image": True if image else False,
        "erid": campaign.erid if campaign.erid else "Не обозначен",
    }


async def campaign_check_getter(dialog_manager: DialogManager, **kwargs):
    campaign_data = dialog_manager.dialog_data
    targeted_age = ""
    if campaign_data["targeting"].get("age_from") is not None:
        targeted_age = f"с {campaign_data['targeting'].get('age_from')} "
    if campaign_data["targeting"].get("age_to") is not None:
        targeted_age += f"до {campaign_data['targeting'].get('age_to')}"
    if not targeted_age:
        targeted_age = "Все"
    match campaign_data["targeting"].get("gender"):
        case "MALE":
            targeted_gender = "Мужской"
        case "FEMALE":
            targeted_gender = "Женский"
        case _:
            targeted_gender = "Все"

    image = None
    if campaign_data.get("image_file_id"):
        media_id = MediaId(campaign_data.get("image_file_id"))
        image = MediaAttachment(
            file_id=media_id, type=ContentType.PHOTO
        )

    dates = "Действительна"
    if campaign_data.get("start_date") is not None:
        dates += f" с {campaign_data['start_date']} "
    if campaign_data.get("end_date") is not None:
        dates += f"по {campaign_data['end_date']}"

    return {
        "cost_per_impression": campaign_data["cost_per_impression"],
        "cost_per_click": campaign_data["cost_per_click"],
        "title": campaign_data["ad_title"],
        "text": campaign_data["ad_text"],
        "dates": dates,
        "targeted_gender": targeted_gender,
        "targeted_age": targeted_age,
        "targeted_location": campaign_data["targeting"].get("location")
        if campaign_data["targeting"].get("location")
        else "Все",
        "image": image,
        "has_image": True if image else False,
        "erid": campaign_data.get("erid")
        if campaign_data.get("erid")
        else "Не обозначен",
    }


async def daily_statistics_getter(dialog_manager: DialogManager, **kwargs):
    campaign_id = dialog_manager.start_data["campaign_id"]
    if not dialog_manager.dialog_data.get("daily_statisticss"):
        statistics_data = await get_gaily_statistics(campaign_id)
        dialog_manager.dialog_data["daily_statisticss"] = statistics_data

    statistics_data = dialog_manager.dialog_data["daily_statisticss"]
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


async def all_statistics_getter(dialog_manager: DialogManager, **kwargs):
    campaign_id = dialog_manager.start_data["campaign_id"]
    statistics_data = await get_all_statistics(campaign_id)

    data = {"statistics": statistics_data}
    return data

async def generate_text_getter(dialog_manager: DialogManager, **kwargs):
    title = dialog_manager.dialog_data["ad_title"]
    targeted_age = ""
    if dialog_manager.dialog_data["targeting"].get("age_from") is not None:
        targeted_age = f"с {dialog_manager.dialog_data['targeting'].get('age_from')} "
    if dialog_manager.dialog_data["targeting"].get("age_to") is not None:
        targeted_age += f"до {dialog_manager.dialog_data['targeting'].get('age_to')}"
    match dialog_manager.dialog_data["targeting"].get("gender"):
        case "MALE":
            targeted_gender = "Мужской"
        case "FEMALE":
            targeted_gender = "Женский"
        case _:
            targeted_gender = ''

    generated_text = await generate_text(title, f"{targeted_age} {targeted_gender}")
    dialog_manager.dialog_data["ad_text"] = generated_text

    return {
        "generated_text": generated_text,
    }