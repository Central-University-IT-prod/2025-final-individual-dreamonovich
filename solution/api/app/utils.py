from django.core.cache import cache


def get_current_day() -> int:
    return cache.get("current_day", 1)


def set_day(day: int) -> None:
    cache.set("current_day", day)


def get_banlist_status():
    return cache.get("banlist_status", False)


def set_banlist_status(status: bool):
    cache.set("banlist_status", status)
