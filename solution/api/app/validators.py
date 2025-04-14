from rest_framework import status

from app.exceptions import CustomAPIException
from app.profanity_filter import check_profanity
from app.utils import get_banlist_status


def profanity_validator(value):
    is_banlist_enabled = get_banlist_status()
    if is_banlist_enabled and check_profanity(value):
        raise CustomAPIException(
            detail="Нецензурная лексика в тексте.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
