from django.urls import path

from .views import (
    BulkCreateClientsView,
    GetClientView,
    ClickAdvertisementView, get_advertisement_view,
)

urlpatterns = [
    path("clients/bulk", BulkCreateClientsView.as_view(), name="bulk_create_clients"),
    path("clients/<uuid:id>", GetClientView.as_view(), name="get_client"),
    path("ads", get_advertisement_view, name="get_ad"),
    path(
        "ads/<uuid:campaign_id>/click",
        ClickAdvertisementView.as_view(),
        name="click_ad",
    ),
]
