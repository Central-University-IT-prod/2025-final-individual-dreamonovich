from aiogram.enums import ContentType, ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Start,
    Back,
    Row,
    Select,
    Group,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format, List
from .callback import (
    campaign_click,
    first_page,
    previous_page,
    next_page,
    last_page,
    advertiser_id_entered,
    profile_exit,
    first_stat_page,
    previous_stat_page,
    next_stat_page,
    last_stat_page,
)
from .getters import (
    main_menu_getter,
    get_advertiser_info,
    advertiser_statistics_getter,
    advertiser_daily_statistics_getter,
)
from .states import MenuSG, ProfileSG
from ..campaign.states import CreateCampaignSG

main_dialog = Dialog(
    Window(
        Const("Кажется, вы ещё не авторизованы!"),
        Start(Const("Авторизоваться"), id="register", state=MenuSG.register),
        state=MenuSG.not_registered,
    ),
    Window(
        Const("Укажите UUID рекламодателя"),
        Back(Const("Отмена")),
        MessageInput(advertiser_id_entered, content_types=[ContentType.TEXT]),
        state=MenuSG.register,
    ),
    Window(
        Format("{advertiser_name}\n"),
        Const("Ваши рекламы:"),
        List(Format("{pos}) {item[title]}"), items="campaigns"),
        Format("{campaign_page}/{max_campaign_page}"),
        Group(
            Select(
                Format("{pos}"),
                on_click=campaign_click,
                item_id_getter=lambda item: item["id"],
                id="campaigns_button",
                items="campaigns",
            ),
            width=3,
        ),
        Row(
            Button(Const("<<-1"), id="first_page", on_click=first_page),
            Button(
                Format("<-{previous_page}"), id="previous_page", on_click=previous_page
            ),
            Button(Format("{next_page}->"), id="next_page", on_click=next_page),
            Button(
                Format("{max_campaign_page}->>"), id="last_page", on_click=last_page
            ),
        ),
        Start(
            Const("Создать кампанию"),
            state=CreateCampaignSG.ad_title,
            id="campaign_new",
        ),
        Start(Const("Профиль"), state=ProfileSG.profile, id="profile"),
        state=MenuSG.main,
        getter=main_menu_getter,
    ),
)

statistics_data = Format("""
Показы: {statistics[impressions_count]}
Переходы: {statistics[clicks_count]}
Конверсия: {statistics[conversion]}%
Траты на показы: {statistics[spent_impressions]}
Траты на переходы: {statistics[spent_clicks]}
Общие траты: {statistics[spent_total]}
""")

profile_dialog = Dialog(
    Window(
        Format("""Название: {name}

ID: _{id}_
"""),
        SwitchTo(
            Const("Статистика по дням"),
            state=ProfileSG.daily_statistics,
            id="daily_statistics",
        ),
        SwitchTo(
            Const("Статистика за все время"),
            state=ProfileSG.all_statistics,
            id="all_statistics",
        ),
        SwitchTo(Const("Выйти из профиля"), state=ProfileSG.exit, id="exit"),
        Start(Const("Назад"), id="cancel", state=MenuSG.main),
        parse_mode=ParseMode.MARKDOWN,
        getter=get_advertiser_info,
        state=ProfileSG.profile,
    ),
    Window(
        Const("Вы точно хотите выйти из профиля?"),
        Row(
            Back(Const("Нет")), Button(Const("Да"), id="confirm", on_click=profile_exit)
        ),
        state=ProfileSG.exit,
    ),
    Window(
        Const("Статистика по дням"),
        statistics_data,
        Row(
            Button(Const("<<-1"), id="first_page", on_click=first_stat_page),
            Button(
                Format("<-{previous_page}"),
                id="previous_page",
                on_click=previous_stat_page,
            ),
            Button(Format("{next_page}->"), id="next_page", on_click=next_stat_page),
            Button(
                Format("{max_stat_page}->>"), id="last_page", on_click=last_stat_page
            ),
        ),
        Format("{stat_page}/{max_stat_page}"),
        SwitchTo(Const("Назад"), state=ProfileSG.profile, id="profile"),
        state=ProfileSG.daily_statistics,
        getter=advertiser_daily_statistics_getter,
    ),
    Window(
        Const("Статистика за все время"),
        statistics_data,
        SwitchTo(Const("Назад"), state=ProfileSG.profile, id="profile"),
        state=ProfileSG.all_statistics,
        getter=advertiser_statistics_getter,
    ),
)
