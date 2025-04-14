from aiogram.fsm.state import State, StatesGroup


class CampaignSG(StatesGroup):
    main = State()
    new = State()
    daily_statistics = State()
    all_statistics = State()
    edit_campaign = State()
    update_campaign = State()
    delete_campaign = State()


class CreateCampaignSG(StatesGroup):
    impressions_limit = State()
    clicks_limit = State()
    cost_per_impression = State()
    cost_per_click = State()
    ad_title = State()
    ad_text = State()
    start_date = State()
    end_date = State()
    image = State()
    targeted_gender = State()
    targeted_age_to = State()
    targeted_age_from = State()
    targeted_location = State()
    erid = State()
    create_campaign = State()
    generate_text = State()


class UpdateCampaignSG(StatesGroup):
    impressions_limit = State()
    clicks_limit = State()
    cost_per_impression = State()
    cost_per_click = State()
    ad_title = State()
    ad_text = State()
    start_date = State()
    end_date = State()
    image = State()
    targeted_gender = State()
    targeted_age_to = State()
    targeted_age_from = State()
    targeted_location = State()
    erid = State()
    update_campaign = State()
    generate_text = State()
