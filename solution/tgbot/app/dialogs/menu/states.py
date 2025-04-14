from aiogram.fsm.state import State, StatesGroup


class MenuSG(StatesGroup):
    main = State()
    not_registered = State()
    register = State()
    profile = State()
    exit = State()


class ProfileSG(StatesGroup):
    profile = State()
    exit = State()
    daily_statistics = State()
    all_statistics = State()
