from django.urls import path
from business.views import (
    BulkCreateAdvertisersView,
    GetAdvertiserView,
    CreateScoreView,
    CreateCampaignView,
    RetrieveUpdateDestroyCampaignView,
    AdvertiserStatisticsView,
    CampaignStatisticsView,
    AdvertiserDailyStatisticsView,
    CampaignDailyStatisticsView,
    update_add_campaign_image_view,
    GenerateAdTextView,
    get_score,
    delete_grafana_users,
    register_advertiser_to_grafana,
)

urlpatterns = [
    path("advertisers/bulk", BulkCreateAdvertisersView.as_view()),
    path("advertisers/<uuid:id>", GetAdvertiserView.as_view()),
    path("ml-scores", CreateScoreView.as_view()),
    path("advertisers/<uuid:advertiser_id>/campaigns", CreateCampaignView.as_view()),
    path(
        "advertisers/<uuid:advertiser_id>/campaigns/<uuid:campaign_id>",
        RetrieveUpdateDestroyCampaignView.as_view(),
    ),
    path(
        "advertisers/<uuid:advertiser_id>/campaigns/<uuid:campaign_id>/image",
        update_add_campaign_image_view,
    ),
    path("stats/campaigns/<uuid:campaign_id>", CampaignStatisticsView.as_view()),
    path(
        "stats/campaigns/<uuid:campaign_id>/daily",
        CampaignDailyStatisticsView.as_view(),
    ),
    path(
        "stats/advertisers/<uuid:advertiser_id>/campaigns",
        AdvertiserStatisticsView.as_view(),
    ),
    path(
        "stats/advertisers/<uuid:advertiser_id>/campaigns/daily",
        AdvertiserDailyStatisticsView.as_view(),
    ),
    path(
        "generate-text",
        GenerateAdTextView.as_view(),
    ),
    path(
        "score",
        get_score,
    ),
    path("delete-grafana-users", delete_grafana_users),
    path("advertisers/<uuid:advertiser_id>/grafana", register_advertiser_to_grafana),
]
