from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 2               # default items per page
    page_size_query_param = 'page_size'  # allows client to override page size
    max_page_size = 100         # max items per page