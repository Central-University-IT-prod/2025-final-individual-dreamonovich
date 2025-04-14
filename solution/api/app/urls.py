from django.urls import path, include
from app.views import (
    set_day_view,
    get_day_view,
    BanlistView,
    change_banlist_status,
    ping,
)

urlpatterns = [
    path("", include("client.urls")),
    path("", include("business.urls")),
    path("time/advance", set_day_view),
    path("time/current", get_day_view),
    path("banlist/", BanlistView.as_view()),
    path("banlist/status", change_banlist_status),
    path("ping", ping),
]
