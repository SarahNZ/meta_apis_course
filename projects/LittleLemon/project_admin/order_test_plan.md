## Order Test Plan

### Manager can assign an order to a delivery crew member
# Manager assigns order to delivery crew
PATCH /api/orders/1/
{
  "delivery_crew": 5
}

# Manager updates status of assigned order
PATCH /api/orders/1/
{
  "status": 1
}

# Manager cannot update status of unassigned orders

# Delivery crew member updates status of their assigned order
PATCH /api/orders/1/
{
  "status": 1
}

# Delivery crew members CANNOT update the delivery_crew field (assignment)

# Manager can assign an order to a delivery crew member and update the status to delivered
PATCH /api/orders/1/
{
  "delivery_crew": 5,
  "status": 1
}

# Authenticated user who is not in the Manager or Delivery Crew group can't update the status or delivery_crew user of an order, even if they placed that order

# Anon users can't update orders

# Invalid or non-existent status values are rejected

# Invalid or non-existent delivery crew id's are rejected

test_delivery_crew_cannot_update_multiple_fields - Ensures delivery crew can't update both fields
test_delivery_crew_cannot_update_status_of_order_assigned_to_other - Ensures delivery crew can only update their own orders
test_delivery_crew_cannot_update_status_of_unassigned_order - Ensures delivery crew can't update unassigned orders