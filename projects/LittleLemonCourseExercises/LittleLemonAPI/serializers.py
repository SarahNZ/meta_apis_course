from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.validators import UniqueTogetherValidator
from .models import MenuItem
from .models import Category
from decimal import Decimal, ROUND_HALF_UP
import bleach

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
        
class MenuItemSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source = 'inventory')
    price_after_tax = serializers.SerializerMethodField(method_name = 'calculate_tax')
    category = CategorySerializer(read_only = True)
    category_id = serializers.IntegerField(write_only = True)
    title = serializers.CharField(
        max_length = 255,
        validators = [UniqueValidator(queryset = MenuItem.objects.all())]
    )
    # price = serializers.DecimalField(max_digits = 6, decimal_places = 2, min_value = 2)
    
    def validate_title(self, value):
        return bleach.clean(value)
    
    def validate_price(self, value):
        if value < 2:
            raise serializers.ValidationError('Price should not be less than 2.0')
        return value # Return value if it passes validation
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('Stock cannot be negative')
        return value # Return value if it passes valication
    
    # def validate(self, attrs):
    #     if(attrs['price'] < 2):
    #         raise serializers.ValidationError('Price should not be less than 2.0')
    #     if(attrs['inventory'] < 0):
    #         raise serializers.ValidationError('Stock cannot be negative')
    #     return super().validate(attrs)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'price_after_tax', 'stock', 'category', 'category_id']
        extra_kwargs = {
            'price': {'min_value': 2},
            # 'title': {
            #     'validators': [
            #         UniqueValidator(queryset = MenuItem.objects.all())
            #     ]
            # }
        }
        
    def calculate_tax(self, product:MenuItem):
        price_with_tax = product.price * Decimal("1.1")
        return price_with_tax.quantize(Decimal("0.01"), rounding = ROUND_HALF_UP)

# class MenuItemSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     title = serializers.CharField(max_length = 255)
#     price = serializers.DecimalField(max_digits = 6, decimal_places = 2)
#     inventory = serializers.IntegerField()
