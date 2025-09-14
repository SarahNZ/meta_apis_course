import django_filters
from .models import MenuItem

class MenuItemFilter(django_filters.FilterSet):
    category_title = django_filters.CharFilter(field_name='category__title', lookup_expr='icontains')
    
    class Meta:
        model = MenuItem
        fields = ['category_title', 'title']