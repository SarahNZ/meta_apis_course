from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from .models import Cart, Category, MenuItem
import bleach

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
        
    title = serializers.CharField(
        max_length = 255,
        validators = [UniqueValidator(queryset = Category.objects.all())]
    )
    
    slug = serializers.CharField(
        max_length = 255,
        validators = [UniqueValidator(queryset = Category.objects.all())]
    )
        
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
        
# Converts the Cart object into JSON
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
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  
        fields = ["id", "username", "email"]