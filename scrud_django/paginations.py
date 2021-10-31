import math

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data, *args, **kwargs):

        return {
            'count': self.page.paginator.count,
            'page_count': math.ceil(self.page.paginator.count / self.page_size),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'content': data,
        }
