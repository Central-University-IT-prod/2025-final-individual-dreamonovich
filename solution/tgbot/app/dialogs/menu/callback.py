import uuid

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from db.db import advertiser_exists, register_user
from dialogs.campaign.states import CampaignSG
from .states import MenuSG, ProfileSG
from db.models import TelegramUser


async def get_next_page(diaglog_data):
    next_page = (
        diaglog_data["campaign_page"] + 1
        if diaglog_data["campaign_page"] != diaglog_data["max_campaign_page"]
        else 1
    )
    return next_page


async def get_previous_page(diaglog_data):
    previous_page = (
        diaglog_data["campaign_page"] - 1
        if diaglog_data["campaign_page"] != 1
        else diaglog_data["max_campaign_page"]
    )
    return previous_page


async def previous_page(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    if manager.dialog_data["campaign_page"] > 1:
        manager.dialog_data["campaign_page"] -= 1
    else:
        manager.dialog_data["campaign_page"] = manager.dialog_data["max_campaign_page"]
        manager.dialog_data["next_page"] = (
            manager.dialog_data["campaign_page"] + 1
            if manager.dialog_data["campaign_page"]
            != manager.dialog_data["max_campaign_page"]
            else 1
        )
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(MenuSG.main, show_mode=ShowMode.EDIT)


async def next_page(callback: CallbackQuery, button: Button, manager: DialogManager):
    if manager.dialog_data["campaign_page"] < manager.dialog_data["max_campaign_page"]:
        manager.dialog_data["campaign_page"] += 1
    else:
        manager.dialog_data["campaign_page"] = 1
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(MenuSG.main, show_mode=ShowMode.EDIT)


async def campaign_click(
    callback: CallbackQuery, button: Button, manager: DialogManager, item_id: str
):
    manager.dialog_data["campaign_id"] = item_id
    await manager.start(CampaignSG.main, data=manager.dialog_data)


async def first_page(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["campaign_page"] = 1
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(MenuSG.main, show_mode=ShowMode.EDIT)


async def last_page(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["campaign_page"] = manager.dialog_data["max_campaign_page"]
    manager.dialog_data["previous_page"] = await get_previous_page(manager.dialog_data)
    manager.dialog_data["next_page"] = await get_next_page(manager.dialog_data)
    await manager.switch_to(MenuSG.main, show_mode=ShowMode.EDIT)


async def advertiser_id_entered(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    try:
        advertiser_id = uuid.UUID(message.text).hex
        if await advertiser_exists(advertiser_id):
            await register_user(str(message.from_user.id), advertiser_id)
            manager.dialog_data["advertiser_id"] = advertiser_id
            await manager.switch_to(MenuSG.main)
        else:
            await message.answer("Такого рекламодателя не существует!")
            await manager.switch_to(MenuSG.register)
    except ValueError:
        await message.answer("Некорректный UUID!")


async def profile_exit(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    await TelegramUser.filter(telegram_id=message.from_user.id).delete()
    await manager.start(state=MenuSG.register, mode=StartMode.RESET_STACK)


async def get_next_stat_page(diaglog_data):
    next_page = (
        diaglog_data["stat_page"] + 1
        if diaglog_data["stat_page"] != diaglog_data["max_stat_page"]
        else 1
    )
    return next_page


async def get_previous_stat_page(diaglog_data):
    previous_page = (
        diaglog_data["stat_page"] - 1
        if diaglog_data["stat_page"] != 1
        else diaglog_data["max_stat_page"]
    )
    return previous_page


async def previous_stat_page(
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
    manager.dialog_data["previous_page"] = await get_previous_stat_page(
        manager.dialog_data
    )
    manager.dialog_data["next_page"] = await get_next_stat_page(manager.dialog_data)
    await manager.switch_to(ProfileSG.daily_statistics, show_mode=ShowMode.EDIT)


async def next_stat_page(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    if manager.dialog_data["stat_page"] < manager.dialog_data["max_stat_page"]:
        manager.dialog_data["stat_page"] += 1
    else:
        manager.dialog_data["stat_page"] = 1
    manager.dialog_data["previous_page"] = await get_previous_stat_page(
        manager.dialog_data
    )
    manager.dialog_data["next_page"] = await get_next_stat_page(manager.dialog_data)
    await manager.switch_to(ProfileSG.daily_statistics, show_mode=ShowMode.EDIT)


async def first_stat_page(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["stat_page"] = 1
    manager.dialog_data["previous_page"] = await get_previous_stat_page(
        manager.dialog_data
    )
    manager.dialog_data["next_page"] = await get_next_stat_page(manager.dialog_data)
    await manager.switch_to(ProfileSG.daily_statistics, show_mode=ShowMode.EDIT)


async def last_stat_page(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["stat_page"] = manager.dialog_data["max_stat_page"]
    manager.dialog_data["previous_page"] = await get_previous_stat_page(
        manager.dialog_data
    )
    manager.dialog_data["next_page"] = await get_next_stat_page(manager.dialog_data)
    await manager.switch_to(ProfileSG.daily_statistics, show_mode=ShowMode.EDIT)
