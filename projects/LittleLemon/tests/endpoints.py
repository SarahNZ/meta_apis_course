CART = "/api/cart/"
CATEGORIES = "/api/categories/"
DELIVERY_CREW = "/api/groups/delivery-crew/users/"
LOGIN = "/auth/token/login/"  # Djoser login endpoint
MANAGERS = "/api/groups/manager/users/"
MENU_ITEMS = "/api/menu-items/"
USERS = "/api/users/"

'''
### DJOSER (User token-based authentication) ###
http://localhost:8000/auth
/users/
/users/me/
/users/confirm/
/users/resend_activation/
/users/set_password/
/users/reset_password/
/users/reset_password_confirm/
/users/set_username/
/users/reset_username/
users/reset_username_confirm/
/token/login/ (Note: Need to install DRF Simple TokenAuthentication or JWT for this to work)
/token/logout/

# USER/GROUP MANAGEMENT ENDPOINTS
/api/users/{userId}/groups

## MENU-ITEMS ENDPOINTS
Note: All require authentication (IsAuthenticated)
/api/menu-items (GET, Role = Customer, delivery crew, lists all menu items, return a 200 ok code)
/api/menu-items (POST, PUT, PATCH, DELETE, Role = customer, delivery crew)

GET /api/menu-items/ → list menu items
POST /api/menu-items/ → create menu item
GET /api/menu-items/{id}/ → retrieve single item
PUT /api/menu-items/{id}/ → update item
PATCH /api/menu-items/{id}/ → partial update
DELETE /api/menu-items/{id}/ → delete item

# CART ENDPOINTS
/api/users/{userId}/cart
/api/users/{userId}/cart/menu-items

# ORDER/DELIVERY ENDPOINTS
/api/orders
/api/orders/{orderId}
/api/orders?status=delivered
/api/orders/status=pending
'''