# Django REST API Course Projects - AI Coding Guidelines

## Project Architecture Overview

This workspace contains multiple Django REST API projects that follow a **course-driven structure**:

- **LittleLemon**: Main production-ready restaurant API with full authentication, role-based permissions, and comprehensive testing
- **BookList**: Basic Django project template for learning exercises
- **DebugExample**: Minimal Django setup for debugging practice

## Core Development Workflow

### Environment Setup
```powershell
cd LittleLemon
pipenv shell                    # Activate virtual environment  
pipenv install                  # Install dependencies from Pipfile
python manage.py migrate        # Run database migrations
python manage.py runserver      # Start development server
```

### Testing Commands (LittleLemon project)
```powershell
# Run all tests with verbose output
pytest tests/ -v --tb=short --maxfail=1 --disable-warnings

# Run specific test file
pytest tests/test_menu_items.py -v

# Run single test method
pytest tests/test_auth.py::UserAPITestCase::test_login -v

# Re-run only failed tests
pytest --lf -v
```

## Authentication & Permission Patterns

### Token-Based Authentication (Djoser + DRF)
- **All API endpoints require authentication** unless explicitly marked otherwise
- Use `Token {auth_token}` in Authorization header
- Login via `POST /auth/token/login/` with username/password
- User management handled by Djoser endpoints (`/auth/users/`, `/auth/users/me/`)

### Role-Based Access Control
```python
# Three user roles with distinct permissions:
# 1. Customer (default) - can browse menu, manage own cart/orders
# 2. Manager (is_staff=True) - full CRUD on menu items, user group management  
# 3. Delivery Crew - can view/update assigned orders only

# Custom permission pattern in views.py:
from .permissions import IsStaffOrReadOnly
permission_classes = [IsStaffOrReadOnly]  # Read for auth users, write for staff
```

## Model & API Design Conventions

### Model Patterns
```python
# All models use bleach.clean() for XSS protection
def clean(self):
    self.title = bleach.clean(self.title)

# Models override save() to call full_clean()
def save(self, *args, **kwargs):
    self.full_clean() 
    super().save(*args, **kwargs)

# Use db_index=True for frequently queried fields
price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
```

### ViewSet Architecture
```python
# Use ModelViewSet for full CRUD operations
class MenuItemsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = MenuItemFilter  # Custom django-filter class

# Use ViewSet for custom logic (see CartViewSet)
class CartViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Cart.objects.filter(user=request.user)  # Always filter by current user
```

### Serializer Patterns
```python
# Separate read/write fields for foreign keys
category = CategorySerializer(read_only=True)
category_id = serializers.IntegerField(write_only=True)

# Use UniqueValidator for business constraints
title = serializers.CharField(
    validators=[UniqueValidator(queryset=MenuItem.objects.all())]
)

# Custom validation methods
def validate_price(self, value):
    if value < 0:
        raise serializers.ValidationError('Price cannot be negative')
    return value
```

## Testing Architecture

### Base Test Classes
- Inherit from `BaseAPITestCase` in `tests/base_test.py`
- Built-in helper methods: `get_auth_token()`, `authenticate_client()`, `add_user_to_manager_group()`
- Automatic test user/group setup in `setUp()`

### Test Organization
```python
# Use descriptive test method names
def test_unauthenticated_user_cannot_view_menu_items(self):
def test_manager_can_add_user_to_delivery_crew_group(self):

# Group endpoints by functionality in separate files:
# test_auth.py, test_menu_items.py, test_permissions.py, etc.
```

## URL & Routing Patterns

### Project-Level URLs (`LittleLemon/urls.py`)
```python
# Djoser authentication endpoints
path('auth/', include('djoser.urls')),
path('auth/', include('djoser.urls.authtoken')),

# API app routes
path('api/', include('LittleLemonAPI.urls')),
```

### App-Level URLs (`LittleLemonAPI/urls.py`)
```python
# Mix ViewSet routes with function-based views
router.register('menu-items', MenuItemsViewSet)  # Full CRUD
path('groups/manager/users/', views.managers),   # Custom group management
```

## Django Settings Configuration

### DRF Settings Block
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter', 
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
}
```

## Common Gotchas & Project-Specific Patterns

1. **Group Management**: Adding users to Manager group automatically grants `is_staff=True`
2. **Category Deletion**: Deliberately blocked in `CategoriesViewSet.destroy()` to prevent FK constraint issues  
3. **Cart Logic**: Always filter by `request.user` - never allow cross-user access
4. **Test Database**: Each test runs in isolated transaction with clean test DB
5. **Pipenv**: Use `pipenv` for dependency management, not pip directly
6. **Windows Development**: Use PowerShell commands, not bash

## Key Files to Understand First

- `LittleLemon/technical_plan.txt` - Complete feature requirements and implementation checklist
- `LittleLemon/requirements_and_test_cases.txt` - Business requirements mapping
- `tests/endpoints.py` - All available API endpoints and Djoser routes  
- `LittleLemonAPI/permissions.py` - Custom permission classes
- `tests/base_test.py` - Test utilities and patterns