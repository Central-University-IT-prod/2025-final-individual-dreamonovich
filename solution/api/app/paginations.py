from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PurePageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(data)
