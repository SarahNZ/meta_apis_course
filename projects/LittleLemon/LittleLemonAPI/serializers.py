from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Cart, Category, MenuItem, Order, OrderItem
import bleach
from decimal import Decimal, InvalidOperation

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
        
    title = serializers.CharField(
        max_length = 255,
        validators = [UniqueValidator(queryset = Category.objects.all())]
    )
    
    slug = serializers.SlugField(
        max_length = 50,  # SlugField default max_length
        validators = [UniqueValidator(queryset = Category.objects.all())]
    )
    
    def validate_slug(self, value):
        """Additional slug validation to match Django's SlugField."""
        import re
        if not re.match(r'^[-a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'
            )
        return value
        
class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only = True)
    category_id = serializers.IntegerField(write_only = True)
    
    title = serializers.CharField(
        max_length = 255,
        validators = [UniqueValidator(queryset = MenuItem.objects.all())]
    )
        
    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category", "category_id"]
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Price cannot be negative')
        return value
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id')
        category = Category.objects.get(id = category_id)
        return MenuItem.objects.create(category = category, **validated_data)
    
    def update(self, instance, validated_data):
        if 'category_id' in validated_data:
            category_id = validated_data.pop('category_id')
            try:
                instance.category = Category.objects.get(id = category_id)
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category_id": "Invalid category id"})
        return super().update(instance, validated_data)
        
        
class CartSerializer(serializers.ModelSerializer):
    # The menuitem id is the primary key of the MenuItem model, not the Category model
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset = MenuItem.objects.all()
    )
    
    # Adding a field to the serializer that doesn't exist in the Cart model. It is in the MenuItem model.
    menuitem_title = serializers.ReadOnlyField(source = "menuitem.title")
    
    class Meta:
        model = Cart  
        fields = [
            "id",
            "menuitem", # expects a MenuItem.id in POST body
            "menuitem_title",   # shows MenuItem title in response
            "quantity", # expects quantity to be provided in POST body
            "unit_price",   # gets from MenuItem.price
            "price",
        ]
        
        read_only_fields = ["unit_price", "price"]
        
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Quantity must be at least 1')
        
        # SmallIntegerField has range -32768 to 32767
        if value > 32767:
            raise serializers.ValidationError('Quantity cannot exceed 32,767')
        
        return value
    
    def validate(self, data):
        """
        Cross-field validation to prevent decimal overflow when calculating price.
        """
        if 'quantity' in data and 'menuitem' in data:
            quantity = data['quantity']
            menuitem = data['menuitem']
            unit_price = menuitem.price
            
            # Check if quantity × unit_price would cause decimal overflow
            # DecimalField(max_digits=6, decimal_places=2) has max value 9999.99
            try:
                calculated_price = Decimal(str(quantity)) * unit_price
                if calculated_price > Decimal('9999.99'):
                    raise serializers.ValidationError({
                        'quantity': f'Quantity too large. Total price ({calculated_price}) would exceed maximum allowed value (9999.99)'
                    })
            except (InvalidOperation, ValueError) as e:
                raise serializers.ValidationError({
                    'quantity': 'Invalid quantity - calculation would cause overflow'
                })
        
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  
        fields = ["id", "username", "email"]
        
        
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem_title = serializers.ReadOnlyField(source="menuitem.title")
    menuitem_category = serializers.ReadOnlyField(source="menuitem.category.title")
    
    class Meta:
        model = OrderItem
        fields = ["id", "menuitem", "menuitem_title", "menuitem_category", "quantity", "unit_price", "price"]
        read_only_fields = ["menuitem_title", "menuitem_category"]


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.ReadOnlyField(source="user.username")
    delivery_crew_name = serializers.ReadOnlyField(source="delivery_crew.username")
    
    # Add formatted date fields for better readability
    date_formatted = serializers.SerializerMethodField()
    time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Order  
        fields = ["id", "user", "user_name", "delivery_crew", "delivery_crew_name", "status", "total", "date", "date_formatted", "time_formatted", "order_items"]
        
        read_only_fields = ["user", "user_name", "total", "date", "order_items"]
    
    def get_date_formatted(self, obj):
        """Return date in readable format: 'September 30, 2025'"""
        # Convert UTC datetime to the active timezone (from settings.TIME_ZONE)
        local_date = timezone.localtime(obj.date)
        return local_date.strftime('%B %d, %Y')
    
    def get_time_formatted(self, obj):
        """Return time in readable format: '2:31 PM'"""
        # Convert UTC datetime to the active timezone (from settings.TIME_ZONE)
        local_date = timezone.localtime(obj.date)
        return local_date.strftime('%I:%M %p')


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for general order updates (PATCH).
    Allows updating both delivery_crew and status fields.
    """
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    status = serializers.IntegerField(required=False)
    
    class Meta:
        model = Order
        fields = ["delivery_crew", "status"]
    
    def validate_delivery_crew(self, value):
        """
        Validate that the delivery_crew user exists and is in the Delivery Crew group.
        """
        if value is not None:
            # Check if user is in Delivery Crew group
            if not value.groups.filter(name='Delivery Crew').exists():
                raise serializers.ValidationError(
                    f"User '{value.username}' is not in the Delivery Crew group"
                )
        return value
    
    def validate_status(self, value):
        """
        Validate that the status can only be set to 1 (delivered).
        """
        if value is not None and value != 1:
            raise serializers.ValidationError(
                "Status can only be set to 1 (delivered)"
            )
        return value