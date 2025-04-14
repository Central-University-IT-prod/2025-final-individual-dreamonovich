from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Row, Cancel, Next, Button, Start, Back
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from .callback import (
    impressions_limit_handler,
    clicks_limit_handler,
    click_cost_handler,
    ad_title_handler,
    ad_text_handler,
    start_date_handler,
    end_date_handler,
    image_handler,
    gender_callback,
    max_age_handler,
    min_age_handler,
    location_handler,
    impression_cost_handler,
    create_campaign_handler,
    first_page,
    previous_page,
    next_page,
    last_page,
    campaign_delete,
    erid_handler,
    update_campaign_handler,
    update_campaign_callback,
    update_location_handler, update_ad_text_handler, update_generated_text_handler,
)
from .getters import (
    campaign_getter,
    campaign_check_getter,
    daily_statistics_getter,
    all_statistics_getter, generate_text_getter,
)
from .states import (
    CampaignSG,
    CreateCampaignSG,
    UpdateCampaignSG,
)
from ..menu.states import MenuSG

campaign_data = [
    DynamicMedia("image", when=F["has_image"]),
    Format("""
**{title}**
{text}

Настройки
Цена показа: {cost_per_impression}
Цена перехода: {cost_per_click}
{dates}
Таргет:
- Возраст: {targeted_age}
- Пол: {targeted_gender}
- Локация: {targeted_location}

Erid: {erid} 
                """),
]

statistics_data = Format("""
Показы: {statistics[impressions_count]}
Переходы: {statistics[clicks_count]}
Конверсия: {statistics[conversion]}%
Траты на показы: {statistics[spent_impressions]}
Траты на переходы: {statistics[spent_clicks]}
Общие траты: {statistics[spent_total]}
""")

campaign_dialog = Dialog(
    Window(
        *campaign_data,
        Row(
            SwitchTo(
                Const("Статистика по дням"),
                state=CampaignSG.daily_statistics,
                id="daily_statistics",
            ),
            SwitchTo(
                Const("Статистика за все время"),
                state=CampaignSG.all_statistics,
                id="all_statistics",
            ),
        ),
        SwitchTo(Const("Изменить"), state=CampaignSG.edit_campaign, id="edit_campaign"),
        Start(Const("Назад"), state=MenuSG.main, id="back"),
        parse_mode=ParseMode.MARKDOWN,
        state=CampaignSG.main,
        getter=campaign_getter,
    ),
    Window(
        Const("Статистика по дням"),
        statistics_data,
        Row(
            Button(Const("<<-1"), id="first_page", on_click=first_page),
            Button(
                Format("<-{previous_page}"), id="previous_page", on_click=previous_page
            ),
            Button(Format("{next_page}->"), id="next_page", on_click=next_page),
            Button(Format("{max_stat_page}->>"), id="last_page", on_click=last_page),
        ),
        SwitchTo(Const("Назад"), id="cancel", state=CampaignSG.main),
        getter=daily_statistics_getter,
        state=CampaignSG.daily_statistics,
    ),
    Window(
        Const("Статистика за все время"),
        statistics_data,
        SwitchTo(Const("Назад"), id="cancel", state=CampaignSG.main),
        getter=all_statistics_getter,
        state=CampaignSG.all_statistics,
    ),
    Window(
        Const("Изменить кампанию"),
        Row(
            SwitchTo(
                Const("Удалить"), state=CampaignSG.delete_campaign, id="delete_campaign"
            ),
            Button(
                Const("Обновить"),
                on_click=update_campaign_callback,
                id="update_campaign",
            ),
        ),
        SwitchTo(Const("Назад"), id="cancel", state=CampaignSG.main),
        state=CampaignSG.edit_campaign,
    ),
    Window(
        Const("Вы точно хотите удалить кампанию?"),
        Row(
            Back(Const("Нет")),
            Button(Const("Да"), id="confirm", on_click=campaign_delete),
        ),
        state=CampaignSG.delete_campaign,
    ),
)


create_campaign_dialog = Dialog(
    Window(
        Const("Укажите название кампании"),
        MessageInput(ad_title_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.ad_title,
    ),
    Window(
        Const("Прикрепите картинку"),
        MessageInput(image_handler, content_types=ContentType.PHOTO),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.image,
    ),
    Window(
        Const("Укажите таргет на минимальный возраст"),
        MessageInput(min_age_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.targeted_age_from,
    ),
    Window(
        Const("Укажите таргет на максимальный возраст"),
        MessageInput(max_age_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.targeted_age_to,
    ),
    Window(
        Const("Укажите таргет на пол"),
        Row(
            Button(Const("Мужской"), on_click=gender_callback, id="MALE"),
            Button(Const("Женский"), on_click=gender_callback, id="FEMALE"),
        ),
        Button(Const("Все"), on_click=gender_callback, id="ALL"),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.targeted_gender,
    ),
    Window(
        Const("Укажите таргет на локацию"),
        MessageInput(location_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.targeted_location,
    ),
    Window(
        Const("Напишите текст рекламы"),
        MessageInput(ad_text_handler, content_types=ContentType.TEXT),
        SwitchTo(Const("Сгенерировать текст"), state=CreateCampaignSG.generate_text, id="generate_text"),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.ad_text,
    ),
    Window(
        Format("{generated_text}"),
        Next(Const("Отлично!")),
        Back(Const("Напишу текст сам")),
        parse_mode=ParseMode.MARKDOWN,
        getter=generate_text_getter,
        state=CreateCampaignSG.generate_text,
    ),
    Window(
        Const("Укажите дату начала кампании"),
        MessageInput(start_date_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.start_date,
    ),
    Window(
        Const("Укажите дату окончания кампании"),
        MessageInput(end_date_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.end_date,
    ),
    Window(
        Const("Укажите цену показа"),
        MessageInput(impression_cost_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.cost_per_impression,
    ),
    Window(
        Const("Укажите цену перехода"),
        MessageInput(click_cost_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.cost_per_click,
    ),
    Window(
        Const("Укажите лимит показов"),
        MessageInput(impressions_limit_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.impressions_limit,
    ),
    Window(
        Const("Укажите лимит переходов"),
        MessageInput(clicks_limit_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.clicks_limit,
    ),
    Window(
        Const("Укажите erid"),
        MessageInput(erid_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=CreateCampaignSG.erid,
    ),
    Window(
        Const("Превью:\n"),
        *campaign_data,
        Button(
            Const("Создать"),
            on_click=create_campaign_handler,
            id="create_campaign",
        ),
        Cancel(Const("Отмена"), id="cancel"),
        parse_mode=ParseMode.MARKDOWN,
        getter=campaign_check_getter,
        state=CreateCampaignSG.create_campaign,
    ),
)

edit_campaign_dialog = Dialog(
    Window(
        Const("Укажите название кампании"),
        MessageInput(ad_title_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.ad_title,
    ),
    Window(
        Const("Прикрепите картинку"),
        MessageInput(image_handler, content_types=ContentType.PHOTO),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.image,
    ),
    Window(
        Const("Укажите таргет на минимальный возраст"),
        MessageInput(min_age_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.targeted_age_from,
    ),
    Window(
        Const("Укажите таргет на максимальный возраст"),
        MessageInput(max_age_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.targeted_age_to,
    ),
    Window(
        Const("Укажите таргет на пол"),
        Row(
            Button(Const("Мужской"), on_click=gender_callback, id="MALE"),
            Button(Const("Женский"), on_click=gender_callback, id="FEMALE"),
        ),
        Button(Const("Все"), on_click=gender_callback, id="ALL"),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.targeted_gender,
    ),
    Window(
        Const("Укажите таргет на локацию"),
        MessageInput(update_location_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.targeted_location,
    ),
    Window(
        Const("Напишите текст рекламы"),
        MessageInput(update_ad_text_handler, content_types=ContentType.TEXT),
        SwitchTo(Const("Сгенерировать текст"), state=UpdateCampaignSG.generate_text, id="generate_text"),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.ad_text,
    ),
    Window(
        Format("{generated_text}"),
        Button(Const("Отлично!"), id="submit", on_click=update_generated_text_handler),
        Cancel(Const("Напишу текст сам")),
        parse_mode=ParseMode.MARKDOWN,
        getter=generate_text_getter,
        state=UpdateCampaignSG.generate_text,
    ),
    Window(
        Const("Укажите дату начала кампании"),
        MessageInput(start_date_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.start_date,
    ),
    Window(
        Const("Укажите дату окончания кампании"),
        MessageInput(end_date_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.end_date,
    ),
    Window(
        Const("Укажите цену показа"),
        MessageInput(click_cost_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.cost_per_impression,
    ),
    Window(
        Const("Укажите цену перехода"),
        MessageInput(impression_cost_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.cost_per_click,
    ),
    Window(
        Const("Укажите лимит показов"),
        MessageInput(impressions_limit_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.impressions_limit,
    ),
    Window(
        Const("Укажите лимит переходов"),
        MessageInput(clicks_limit_handler, content_types=ContentType.TEXT),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.clicks_limit,
    ),
    Window(
        Const("Укажите erid"),
        MessageInput(erid_handler, content_types=ContentType.TEXT),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена"), id="cancel"),
        state=UpdateCampaignSG.erid,
    ),
    Window(
        Const("Превью:"),
        *campaign_data,
        Button(
            Const("Обновить"),
            on_click=update_campaign_handler,
            id="update_campaign",
        ),
        Cancel(Const("Отмена"), id="cancel"),
        parse_mode=ParseMode.MARKDOWN,
        getter=campaign_check_getter,
        state=UpdateCampaignSG.update_campaign,
    ),
)