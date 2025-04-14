from tortoise import fields, Model
from typing import Optional
import os


class TelegramUser(Model):
    telegram_id = fields.CharField(pk=True, max_length=64, unique=True)
    advertiser_id = fields.UUIDField()

    class Meta:
        table = "telegram_users"


class Advertiser(Model):
    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=100)

    class Meta:
        table = "business_advertiser"


# You can either import your settings or use environment variables
MINIO_STORAGE_MEDIA_URL = os.environ.get(
    "MINIO_STORAGE_MEDIA_URL", "http://REDACTED/local-media"
)


class MediaFile:
    """
    A simple wrapper that provides a .url attribute.
    """

    def __init__(self, file_path: Optional[str]):
        self.file_path = file_path

    @property
    def url(self) -> Optional[str]:
        if self.file_path:
            # Construct the full URL; adjust as needed.
            return f"{MINIO_STORAGE_MEDIA_URL}/{self.file_path}"
        return None


class Campaign(Model):
    TARGET_GENDER_CHOICES = {"MALE": "Male", "FEMALE": "Female", "ALL": "All"}

    id = fields.UUIDField(pk=True)
    impressions_limit = fields.IntField()
    clicks_limit = fields.IntField()
    cost_per_impression = fields.FloatField()
    cost_per_click = fields.FloatField()
    ad_title = fields.CharField(max_length=100)
    ad_text = fields.CharField(max_length=500)
    start_date = fields.IntField()
    end_date = fields.IntField()

    # Rename the stored field to something like "image_path"
    image_path = fields.CharField(
        null=True, blank=True, max_length=500, source_field="image"
    )

    targeted_gender = fields.CharField(
        max_length=6, choices=TARGET_GENDER_CHOICES, null=True, blank=True
    )
    targeted_age_from = fields.IntField(null=True, blank=True)
    targeted_age_to = fields.IntField(null=True, blank=True)
    targeted_location = fields.CharField(max_length=500, null=True, blank=True)
    erid = fields.CharField(max_length=20, null=True, blank=True)

    advertiser = fields.OneToOneField(
        "models.Advertiser", on_delete=fields.CASCADE, related_name="campaigns"
    )

    class Meta:
        table = "business_campaign"

    @property
    def image(self) -> MediaFile:
        """
        Returns a MediaFile wrapper so you can do campaign.image.url.
        """
        return MediaFile(self.image_path)
