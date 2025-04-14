from rest_framework import status
from rest_framework.exceptions import APIException


class CustomAPIException(APIException):
    def __init__(
        self, detail=None, status_code=status.HTTP_400_BAD_REQUEST, extra_data=None
    ):
        self.status_code = status_code
        self.detail = {
            "message": detail or "An error occurred.",
        }
