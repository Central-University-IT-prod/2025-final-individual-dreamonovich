from better_profanity import profanity
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from . import settings
from .exceptions import CustomAPIException
from .utils import set_day as cache_set_day, get_current_day, set_banlist_status


@api_view(["POST"])
def set_day_view(request):
    if (day := request.data.get("current_date")) is None:
        raise CustomAPIException(
            detail="current_date обязателен.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_day = get_current_day()
    if not isinstance(day, int):
        raise CustomAPIException(
            detail="Неверный формат даты.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if day < current_day:
        raise CustomAPIException(
            detail="Дата меньше текущей.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    cache_set_day(day)
    return Response({"current_date": day})


@api_view(["GET"])
def get_day_view(request):
    current_day = get_current_day()
    return Response({"current_date": current_day})


class BanlistView(APIView):
    def put(self, request):
        words = self.get_words()
        profanity.load_censor_words(words)

        with open(settings.BANLIST_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(words))

        return Response({"message": "banlist установлен."})

    def post(self, request):
        words = self.get_words()
        profanity.add_censor_words(words)
        with open(settings.BANLIST_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(words) + "\n")

        return Response({"message": "banlist обновлен."})

    def get_words(self):
        wordlist_file = self.request.FILES.get("banlist")
        if not wordlist_file:
            raise CustomAPIException(
                "banlist не передан.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content = wordlist_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return CustomAPIException(
                "Ошибка декодирования файла. Кодировка должны быть UTF-8"
            )

        words = content.splitlines()
        return words


@api_view(["POST"])
def change_banlist_status(request):
    if (banlist_status := request.data.get("status")) is None:
        raise CustomAPIException(
            "status обязателен",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(banlist_status, bool):
        raise CustomAPIException(
            "status должен быть bool",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    set_banlist_status(banlist_status)
    return Response(
        {
            "status": banlist_status,
        }
    )


@api_view(["GET"])
def ping(request):
    return Response({"message": "prod."})
