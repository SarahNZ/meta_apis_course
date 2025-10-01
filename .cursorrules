# LittleLemon Restaurant API

A Django REST Framework API for managing Little Lemon restaurant operations.

## Project Structure
- **LittleLemonAPI/** - Main API app (models, views, serializers, permissions)
- **tests/** - Pytest test suite with comprehensive coverage
- **LittleLemon/** - Django project settings and configuration
- **Database:** SQLite (db.sqlite3)
- **Dependency Management:** Pipenv

## Quick Start Commands

### Development Server
```bash
pipenv run python manage.py runserver
```

### Run Tests
```bash
pipenv run pytest
```
Run with verbose output:
```bash
pipenv run pytest -v
```

### Database Migrations
```bash
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
```

## API Features

### Core Models
- **Category** - Menu item categories (Appetizers, Desserts, Drinks, Mains, Sides)
- **MenuItem** - Restaurant menu items with pricing and categorization
- **Cart** - User shopping cart for ordering
- **Order** - Customer orders with order items
- **OrderItem** - Individual items within an order

### User Groups & Roles
- **Manager** - Full access, gets staff status
- **Delivery Crew** - Can be assigned to orders
- **Customer** - Regular authenticated users

### Authentication
- **Type:** Token-based authentication (via Djoser)
- **Create user:** POST `/auth/users/` (username, password)
- **Get token:** POST `/auth/token/login/` (username, password)
- **Use token:** Include header `Authorization: Token <your-token>`

### Key API Endpoints
- `/api/menu-items/` - Browse/search menu (staff can add/remove)
- `/api/categories/` - View categories (staff can add, deletion disabled)
- `/api/cart/` - Manage shopping cart
- `/api/orders/` - View/create orders
- `/api/groups/manager/users/` - Manage manager group (admin only)
- `/api/groups/delivery-crew/users/` - Manage delivery crew (admin only)
- `/api/users/` - View all users (admin only)

### API Features
- Filtering (by category, etc.)
- Searching (menu items by title)
- Ordering/Sorting (by price, title, category)
- Pagination (customizable page size)

## Testing
- **Framework:** pytest with pytest-django
- **Test Coverage:** Authentication, permissions, menu items, categories, cart, orders, managers, delivery crew
- **Helper Methods:** Extensive use of helper methods for test readability
