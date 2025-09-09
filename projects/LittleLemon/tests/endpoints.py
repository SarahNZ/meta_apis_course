LOGIN = "/auth/token/login/"  # Djoser login endpoint
USERS = "/api/users/"
MANAGERS = "/api/groups/manager/users/"
DELIVERY_CREW = "/api/groups/delivery-crew/users/"

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
/api/menu-items (GET, Role = Customer, delivery crew, lists all menu items, return a 200 ok code)
/api/menu-items (POST, PUT, PATCH, DELETE, Role = customer, delivery crew)

# CART ENDPOINTS
/api/users/{userId}/cart
/api/users/{userId}/cart/menu-items

# ORDER/DELIVERY ENDPOINTS
/api/orders
/api/orders/{orderId}
/api/orders?status=delivered
/api/orders/status=pending
'''