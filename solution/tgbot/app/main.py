import asyncio
import logging
import os.path

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import Message
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from redis.asyncio.client import Redis

from aiogram_dialog import (
    DialogManager,
    StartMode,
    setup_dialogs,
)
from tortoise import run_async

from db.db import user_is_registered, init
from dialogs.campaign.dialog import (
    campaign_dialog,
    create_campaign_dialog,
    edit_campaign_dialog,
)
from dialogs.menu.dialog import main_dialog, profile_dialog
from dialogs.menu.states import MenuSG

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6380")
REDIS_DB = os.environ.get("REDIS_DB", "1")
BOT_TOKEM = os.environ.get(
    "BOT_TOKEM", "REDACTED"
)


async def start(message: Message, dialog_manager: DialogManager):
    if await user_is_registered(str(dialog_manager.event.from_user.id)):
        await dialog_manager.start(MenuSG.main, mode=StartMode.RESET_STACK)
    else:
        await dialog_manager.start(MenuSG.not_registered, mode=StartMode.RESET_STACK)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEM)
    storage = RedisStorage(
        Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
        ),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp = Dispatcher(storage=storage)
    dp.message.register(start, CommandStart())
    dp.errors.register(
        start,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(
        start,
        ExceptionTypeFilter(UnknownState),
    )
    dp.include_routers(
        main_dialog,
        campaign_dialog,
        create_campaign_dialog,
        profile_dialog,
        edit_campaign_dialog,
    )
    setup_dialogs(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    run_async(init())
    asyncio.run(main())
