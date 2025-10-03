import django_filters
from .models import MenuItem, Order

class MenuItemFilter(django_filters.FilterSet):
    category_title = django_filters.CharFilter(field_name='category__title', lookup_expr='exact')
    
    class Meta:
        model = MenuItem
        fields = ['category_title', 'title']

class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=[
            ('pending', 'Pending'),
            ('delivered', 'Delivered'),
        ],
        method='filter_by_status'
    )
    
    def filter_by_status(self, queryset, name, value):
        """
        Filter orders by status.
        Maps 'pending' to status=0 and 'delivered' to status=1.
        """
        if value == 'pending':
            return queryset.filter(status=0)
        elif value == 'delivered':
            return queryset.filter(status=1)
        return queryset
    
    class Meta:
        model = Order
        fields = ['status']