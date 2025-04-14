from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from db.db import send_create_campaign, send_update_campaign, get_current_day
from dialogs.campaign.states import CampaignSG, UpdateCampaignSG
from dialogs.menu.states import MenuSG
from db.models import TelegramUser, Campaign

from .states import CreateCampaignSG


async def impressions_limit_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        manager.dialog_data["impressions_limit"] = int(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def clicks_limit_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        manager.dialog_data["clicks_limit"] = int(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def click_cost_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        manager.dialog_data["cost_per_click"] = float(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def impression_cost_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        manager.dialog_data["cost_per_impression"] = float(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def ad_title_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["ad_title"] = message.text
    await manager.next()


async def erid_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["erid"] = message.text
    await manager.next()


async def ad_text_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["ad_text"] = message.text

    await manager.switch_to(CreateCampaignSG.start_date)

async def update_ad_text_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["ad_text"] = message.text

    campaign_id = manager.start_data["campaign_id"]
    campaign = await Campaign.filter(id=campaign_id).first()
    if campaign.start_date <= await get_current_day():
        await manager.switch_to(UpdateCampaignSG.cost_per_impression)
    else:
        await manager.switch_to(UpdateCampaignSG.start_date)

async def update_generated_text_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    campaign_id = manager.start_data["campaign_id"]
    campaign = await Campaign.filter(id=campaign_id).first()
    if campaign.start_date <= await get_current_day():
        await manager.switch_to(UpdateCampaignSG.cost_per_impression)
    else:
        await manager.next()

async def start_date_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        manager.dialog_data["start_date"] = int(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def end_date_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        manager.dialog_data["end_date"] = int(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def image_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    manager.dialog_data["image_file_id"] = message.photo[-1].file_id
    await manager.next()


async def gender_callback(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    if not manager.dialog_data.get("targeting"):
        manager.dialog_data["targeting"] = {}
    manager.dialog_data["targeting"]["gender"] = callback.data
    await manager.next()


async def update_location_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    if not manager.dialog_data.get("targeting"):
        manager.dialog_data["targeting"] = {}
    manager.dialog_data["targeting"]["location"] = message.text

    campaign_id = manager.start_data["campaign_id"]
    campaign = await Campaign.filter(id=campaign_id).first()
    await manager.next()


async def location_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    if not manager.dialog_data.get("targeting"):
        manager.dialog_data["targeting"] = {}
    manager.dialog_data["targeting"]["location"] = message.text

    await manager.next()


async def max_age_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        if not manager.dialog_data.get("targeting"):
            manager.dialog_data["targeting"] = {}
        manager.dialog_data["targeting"]["age_to"] = int(message.text)
        await manager.next()
    except ValueError:
        await message.reply("Неверный формат")


async def min_age_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        if not manager.dialog_data.get("targeting"):
            manager.dialog_data["targeting"] = {}
        manager.dialog_data["targeting"]["age_from"] = int(message.text)

        await manager.next()
    except ValueError as e:
        await message.reply(str(e))


async def create_campaign_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    data = manager.dialog_data
    if data.get("image_file_id"):
        data["image"] = await message.bot.download(data["image_file_id"])
    advertiser = await TelegramUser.get(telegram_id=str(message.from_user.id))

    response_data = await send_create_campaign(data, advertiser.advertiser_id)

    campaign_id = response_data["campaign_id"]

    await manager.start(state=CampaignSG.main, data={"campaign_id": campaign_id})


async def get_next_page(diaglog_data):
    next_page = (
        diaglog_data["stat_page"] + 1
        if diaglog_data["stat_page"] != diaglog_data["max_stat_page"]
        else 1
    )
    return next_page


async def get_previous_page(diaglog_data):
    previous_page = (
        diaglog_data["stat_page"] - 1
        if diaglog_data["stat_page"] != 1
        else diaglog_data["max_stat_page"]
    )
    return previous_page


async def previous_page(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    if manager.dialog_data["stat_page"] > 1:
        manager.dialog_data["stat_page"] -= 1
    else:
        manager.dialog_data["stat_page"] = manager.dialog_data["max_stat_page"]
        manager.dialog_data["next_page"] = (
            manager.dialog_data["stat_page"] + 1
            if manager.dialog_data["stat_page"] != manager.dialog_data["max_stat_page"]
            else 1
        )
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(CampaignSG.daily_statistics, show_mode=ShowMode.EDIT)


async def next_page(callback: CallbackQuery, button: Button, manager: DialogManager):
    if manager.dialog_data["stat_page"] < manager.dialog_data["max_stat_page"]:
        manager.dialog_data["stat_page"] += 1
    else:
        manager.dialog_data["stat_page"] = 1
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(CampaignSG.daily_statistics, show_mode=ShowMode.EDIT)


async def first_page(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["stat_page"] = 1
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(CampaignSG.daily_statistics, show_mode=ShowMode.EDIT)


async def last_page(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["stat_page"] = manager.dialog_data["max_stat_page"]
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(CampaignSG.daily_statistics, show_mode=ShowMode.EDIT)


async def campaign_delete(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    campaign_id = manager.start_data["campaign_id"]
    await Campaign.filter(id=campaign_id).delete()
    await manager.start(MenuSG.main)


async def update_campaign_callback(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    campaign_id = manager.start_data["campaign_id"]
    await manager.start(UpdateCampaignSG.ad_title, data={"campaign_id": campaign_id})


async def update_campaign_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    data = manager.dialog_data

    if data.get("image_file_id"):
        data["image"] = await message.bot.download(data.get("image_file_id"))
    advertiser = await TelegramUser.get(telegram_id=str(message.from_user.id))

    await send_update_campaign(
        data, advertiser.advertiser_id, manager.start_data["campaign_id"]
    )

    await manager.start(
        state=CampaignSG.main, data={"campaign_id": manager.start_data["campaign_id"]}
    )
