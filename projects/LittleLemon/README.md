# LittleLemon Restaurant API

A Django REST Framework API for managing Little Lemon restaurant operations. This is a student project demonstrating REST API design, authentication, permissions, and comprehensive testing.

## Quick Reference for Developers

### Key Commands
```bash
# Development
pipenv run python manage.py runserver

# Testing
pipenv run pytest                    # Run all tests
pipenv run pytest -v                 # Verbose output
pipenv run pytest tests/test_cart.py # Run specific test file
pipenv run pytest -s --lf -v         # Re-run last failures with output

# Database
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
```

### Core Models & Relationships
- **Category** → **MenuItem** (PROTECT relationship)
- **User** → **Cart** → **MenuItem** (user's shopping cart)
- **User** → **Order** → **OrderItem** → **MenuItem** (completed orders)

### API Endpoints Structure
- `/api/menu-items/` - MenuItemsViewSet (IsStaffOrReadOnly)
- `/api/categories/` - CategoriesViewSet (IsStaffOrReadOnly, DELETE blocked)
- `/api/cart/` - CartViewSet (IsAuthenticated, user-specific)
- `/api/orders/` - OrderViewSet (IsAuthenticated, user-specific)
- `/api/groups/manager/users/` - ManagerViewSet (IsAdminUser)
- `/api/groups/delivery-crew/users/` - DeliveryCrewViewSet (IsAdminUser)

### Testing Patterns
- **Base Class:** `BaseAPITestCase` in `tests/base_test.py`
- **Helper Methods:** `get_auth_token()`, `authenticate_client()`, `add_user_to_manager_group()`
- **Test Strategy:** Each test class gets fresh database, comprehensive coverage

### Key Implementation Notes
- Uses `IsStaffOrReadOnly` custom permission
- Cart logic: auto-increments quantity for duplicate items
- Order creation: atomically creates order + items + clears cart
- Bleach sanitization on Category/MenuItem titles
- Comprehensive logging via 'LittleLemonAPI' logger
- Pagination: default 2 items per page, max 100

See `.cursorrules` for complete documentation.