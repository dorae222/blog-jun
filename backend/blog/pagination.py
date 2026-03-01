from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'  # ?page_size=500 허용
    max_page_size = 1000
