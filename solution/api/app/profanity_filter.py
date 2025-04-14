from better_profanity import profanity
from app import settings

try:
    profanity.load_censor_words_from_file(settings.BANLIST_PATH)
except FileNotFoundError:
    pass


def check_profanity(text: str) -> bool:
    return profanity.contains_profanity(text)
