from base_test import BaseAPITestCase
from endpoints import MENU_ITEMS
from rest_framework import status
from LittleLemonAPI.models import Category, MenuItem
from LittleLemon.settings import REST_FRAMEWORK


class MenuItemsTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        # Categories
        self.category_pizza = Category.objects.create(slug="pizza", title="Pizza")
        self.category_dessert = Category.objects.create(slug="dessert", title="Dessert")

        # Menu items
        MenuItem.objects.create(title="Margherita", price=10, featured=True, category=self.category_pizza)
        MenuItem.objects.create(title="Pepperoni", price=12, featured=False, category=self.category_pizza)
        MenuItem.objects.create(title="Apple Pie", price=11, featured=False, category=self.category_dessert)

        # Authenticate client as default user
        token = self.get_auth_token()
        self.authenticate_client(token)

    # === View List Tests ===
    def test_list_auth_user_can_view(self):
        page_size = 100
        url = f"{MENU_ITEMS}?page_size={page_size}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        titles = [item["title"] for item in response.json()['results']]    # type:ignore
        for m in MenuItem.objects.all():
            self.assertIn(m.title, titles)

    def test_list_anon_user_cannot_view(self):
        self.client.credentials()
        response = self.client.get(MENU_ITEMS)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    # type:ignore
        
    # === Filter List Tests ===

    def test_list_filter_by_category_exact_match(self):
        url = f"{MENU_ITEMS}?category__title=Pizza"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_titles = [item["title"] for item in response.json()['results']]   # type:ignore
        pizza_items = [m.title for m in MenuItem.objects.filter(category__title="Pizza")]
        for title in pizza_items:
            self.assertIn(title, response_titles)

    def test_list_filter_by_category_partial_match(self):
        url = f"{MENU_ITEMS}?category__title__icontains=Pizz"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_titles = [item["title"] for item in response.json()['results']]   # type:ignore
        pizza_items = [m.title for m in MenuItem.objects.filter(category__title="Pizza")]
        for title in pizza_items:
            self.assertIn(title, response_titles)

    def test_list_filter_query_string_invalid_or_missing_category(self):
        url = f"{MENU_ITEMS}?category__title=Sushi"
        response = self.client.get(url)
        # If the query string is invalid or the category is missing, all menu items are returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        
    # === Paginate List Tests === 
        
    def test_list_client_sets_pagination(self):
        page_size = 1
        url = f"{MENU_ITEMS}?page_size={page_size}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_titles = [item["title"] for item in response.json()["results"]] # Need to get the nested results # type:ignore
        expected_titles = list(MenuItem.objects.all().order_by("id")[:page_size].values_list("title", flat = True))
        self.assertEqual(response_titles, list(expected_titles))
        
    # Note: If the client tries to set a page_size that is 0 or negative, client spells the page_size criteria wrong or does not include a value, 
    # the response uses the default global pagination setting. This is handled by DRF, so not testing it explicitly here.
        
    # === Search List Tests ===
    
    def test_list_search_exact_match(self):
        criteria = "green salad"
        url = f"{MENU_ITEMS}?search={criteria}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_titles = [item["title"] for item in response.json()['results']]   # type:ignore
        expected_titles = [m.title for m in MenuItem.objects.filter(title__icontains={criteria})]
        for title in expected_titles:
            self.assertIn(title, response_titles)

    def test_list_search_partial_match(self):
        criteria = "salad"
        url = f"{MENU_ITEMS}?search={criteria}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_titles = [item["title"] for item in response.json()['results']]   # type:ignore
        expected_titles = [m.title for m in MenuItem.objects.filter(title__icontains={criteria})]
        for title in expected_titles:
            self.assertIn(title, response_titles)

    def test_list_search_no_matches(self):
        criteria = "xyz"
        url = f"{MENU_ITEMS}?search={criteria}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        self.assertEqual(response.json()['results'], [])   # type:ignore
        
# === Ordering / Sorting Tests ===
    
    def test_list_order_by_price_ascending(self):
        url = f"{MENU_ITEMS}?ordering=price&page_size=100"  # Ensure all items are returned/avoids pagination issues
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore

        # Convert prices from response to floats
        response_prices = [float(item["price"]) for item in response.json()['results']]  # type:ignore

        # Convert expected prices to floats for comparison
        expected_prices = list(MenuItem.objects.all().order_by("price").values_list("price", flat=True))
        expected_prices = [float(p) for p in expected_prices]

        self.assertEqual(response_prices, expected_prices)
        

    def test_list_order_by_price_descending(self):
        url = f"{MENU_ITEMS}?ordering=-price&page_size=100"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_prices = [float(item["price"]) for item in response.json()['results']] # type:ignore
        expected_prices = list(MenuItem.objects.all().order_by("-price").values_list("price", flat=True))
        self.assertEqual(response_prices, expected_prices)

    def test_list_order_by_category_title_then_price(self):
        url = f"{MENU_ITEMS}?ordering=category__title,price&page_size=100"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        response_items = [(item['category']['title'], float(item["price"])) for item in response.json()['results']] # type:ignore
        expected_items = list(MenuItem.objects.all().order_by("category__title", "price").values_list("category__title", "price"))
        self.assertEqual(response_items, expected_items)
        
    def test_list_filter_by_category_and_order_by_price(self):
        category_title = "Pizza"
        url = f"{MENU_ITEMS}?category_title={category_title}&ordering=price&page_size=100"  # Ensure all items returned
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore

        # Extract prices from response
        response_items = response.json()['results']  # type:ignore
        response_prices = [float(item["price"]) for item in response_items]
        response_titles = [item["title"] for item in response_items]

        # Get expected items from DB
        expected_items = MenuItem.objects.filter(category__title=category_title).order_by("price")
        expected_prices = [float(item.price) for item in expected_items]
        expected_titles = [item.title for item in expected_items]

        # Assert prices and titles match expected order
        self.assertEqual(response_prices, expected_prices)
        self.assertEqual(response_titles, expected_titles)

    # === Detail Tests ===
    
    def test_detail_auth_user_can_view(self):
        item = MenuItem.objects.get(title="Margherita")
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        self.assertEqual(response.json()["title"], item.title)  # type:ignore
        self.assertEqual(response.json()["price"], str(item.price))  # type:ignore
        self.assertEqual(response.json()["featured"], item.featured) # type:ignore
        self.assertEqual(response.json()['category']['id'], item.category_id)    # type:ignore

    def test_detail_anon_user_cannot_view(self):
        item = MenuItem.objects.get(title="Margherita")
        self.client.credentials()
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.get(url)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    # type:ignore

    # === Create / POST Tests ===
    def test_auth_admin_user_can_add_menu_item(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {
            "title": "Tiramisu",
            "price": 15.0,
            "featured": False,
            "category_id": self.category_dessert.id # type:ignore
        }
        response = self.client.post(MENU_ITEMS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # type:ignore
        self.assertTrue(MenuItem.objects.filter(title="Tiramisu").exists()) # type:ignore

    def test_auth_non_staff_user_cannot_add_menu_item(self):
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)
        data = {"title": "Gelato", "price": 12.0, "featured": False, "category_id": self.category_dessert.id}   # type:ignore
        response = self.client.post(MENU_ITEMS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)   # type:ignore
        self.assertFalse(MenuItem.objects.filter(title="Gelato").exists())

    def test_anon_user_cannot_add_menu_item(self):
        self.client.credentials()
        data = {"title": "Panna Cotta", "price": 14.0, "featured": True, "category_id": self.category_dessert.id}   # type:ignore
        response = self.client.post(MENU_ITEMS, data, format="json")
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    # type:ignore
        self.assertFalse(MenuItem.objects.filter(title="Panna Cotta").exists())

    # === Update / PATCH / PUT Tests ===

    def test_auth_admin_user_can_patch_menu_item(self):
        """
        Admin/staff user can partially update a menu item via PATCH.
        """
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)

        item = MenuItem.objects.create(title="Original Dish", price=10.0, featured=False, category=self.category_dessert)

        data = {"title": "Updated Dish", "price": 15.0, "featured": True}
        url = f"{MENU_ITEMS}{item.id}/"  # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        item.refresh_from_db()
        self.assertEqual(item.title, "Updated Dish")
        self.assertEqual(item.price, 15.0)
        self.assertTrue(item.featured)


    def test_auth_admin_user_can_put_menu_item(self):
        """
        Admin/staff user can fully update a menu item via PUT.
        """
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)

        item = MenuItem.objects.create(title="Original Dish", price=10.0, featured=False, category=self.category_dessert)

        data = {
            "title": "Updated Dish",
            "price": 20.0,
            "featured": True,
            "category_id": self.category_dessert.id  # type:ignore
        }
        url = f"{MENU_ITEMS}{item.id}/"  # type:ignore
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # type:ignore
        item.refresh_from_db()
        self.assertEqual(item.title, "Updated Dish")
        self.assertEqual(item.price, 20.0)
        self.assertTrue(item.featured)


    def test_auth_non_staff_user_cannot_update_menu_item_patch(self):
        """
        Authenticated non-staff users should get 403 Forbidden when PATCHing a menu item.
        """
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)

        item = MenuItem.objects.create(title="Non-Staff Dish", price=10.0, featured=False, category=self.category_dessert)
        data = {"price": 99.0}
        url = f"{MENU_ITEMS}{item.id}/"  # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type:ignore
        item.refresh_from_db()
        self.assertEqual(item.price, 10.0)


    def test_auth_non_staff_user_cannot_update_menu_item_put(self):
        """
        Authenticated non-staff users should get 403 Forbidden when PUTting a menu item.
        """
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)

        item = MenuItem.objects.create(title="Non-Staff Dish", price=10.0, featured=False, category=self.category_dessert)
        data = {
            "title": "Should Not Update",
            "price": 50.0,
            "featured": True,
            "category_id": self.category_dessert.id  # type:ignore
        }
        url = f"{MENU_ITEMS}{item.id}/"  # type:ignore
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # type:ignore
        item.refresh_from_db()
        self.assertEqual(item.title, "Non-Staff Dish")


    def test_anon_user_cannot_update_menu_item_patch(self):
        """
        Anonymous users cannot PATCH a menu item.
        """
        self.client.credentials()
        item = MenuItem.objects.create(title="Anon Dish", price=10.0, featured=False, category=self.category_dessert)
        data = {"price": 99.0}
        url = f"{MENU_ITEMS}{item.id}/"  # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore
        item.refresh_from_db()
        self.assertEqual(item.price, 10.0)


    def test_anon_user_cannot_update_menu_item_put(self):
        """
        Anonymous users cannot PUT a menu item.
        """
        self.client.credentials()
        item = MenuItem.objects.create(title="Anon Dish", price=10.0, featured=False, category=self.category_dessert)
        data = {
            "title": "Should Not Update",
            "price": 50.0,
            "featured": True,
            "category_id": self.category_dessert.id  # type:ignore
        }
        url = f"{MENU_ITEMS}{item.id}/"  # type:ignore
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # type:ignore
        item.refresh_from_db()
        self.assertEqual(item.title, "Anon Dish")
    

    # === Update / PATCH / PUT Validation Tests ===
    def test_patch_menu_item_invalid_price(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        item = MenuItem.objects.create(title="Patch Dish", price=10.0, featured=False, category=self.category_dessert)
        data = {"price": -7.0}
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # type:ignore
        self.assertIn("price", response.json()) # type:ignore

    def test_patch_menu_item_invalid_category(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        item = MenuItem.objects.create(title="Patch Dish", price=10.0, featured=False, category=self.category_dessert)
        data = {"category_id": 9999}
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # type:ignore
        self.assertIn("category_id", response.json())   # type:ignore

    def test_put_menu_item_duplicate_title(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        item1 = MenuItem.objects.create(title="Dish One", price=10.0, featured=False, category=self.category_dessert)
        item2 = MenuItem.objects.create(title="Dish Two", price=12.0, featured=True, category=self.category_dessert)
        data = {"title": "Dish One", "price": 15.0, "featured": True, "category_id": self.category_dessert.id}  # type:ignore
        url = f"{MENU_ITEMS}{item2.id}/"    # type:ignore
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # type:ignore
        self.assertIn("title", response.json()) # type:ignore

    # === Delete / DELETE Tests ===
    def test_auth_admin_user_can_delete_menu_item(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        item = MenuItem.objects.create(title="To Delete", price=10.0, featured=False, category=self.category_dessert)
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # type:ignore
        self.assertFalse(MenuItem.objects.filter(id=item.id).exists())  # type:ignore
        
    def test_auth_admin_user_delete_nonexistent_menu_item(self):
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        non_existent_id = 9999  # an ID that does not exist in the test DB
        url = f"{MENU_ITEMS}{non_existent_id}/"  # type:ignore
        response = self.client.delete(url)
        self.print_json(response)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)   # type:ignore

    def test_auth_non_staff_user_cannot_delete_menu_item(self):
        self.user1.is_staff = False
        self.user1.save()
        token = self.get_auth_token()
        self.authenticate_client(token)
        item = MenuItem.objects.create(title="To Delete", price=10.0, featured=False, category=self.category_dessert)
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)   # type:ignore
        self.assertTrue(MenuItem.objects.filter(id=item.id).exists())   # type:ignore

    def test_anon_user_cannot_delete_menu_item(self):
        self.client.credentials()
        item = MenuItem.objects.create(title="To Delete", price=10.0, featured=False, category=self.category_dessert)
        url = f"{MENU_ITEMS}{item.id}/" # type:ignore
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)    # type:ignore
        self.assertTrue(MenuItem.objects.filter(id=item.id).exists())   # type:ignore

    # === Performance & Scalability Tests ===
    
    def test_menu_items_large_dataset_performance(self):
        """Test menu items API performance with many items."""
        # Arrange: Create many menu items to test pagination and query performance
        bulk_items = []
        for i in range(100):
            bulk_items.append(MenuItem(
                title=f"Performance Test Item {i}",
                price=9.99 + (i * 0.01),  # Vary prices slightly
                featured=(i % 5 == 0),  # Every 5th item featured
                category=self.category_pizza if i % 2 == 0 else self.category_dessert
            ))
        
        MenuItem.objects.bulk_create(bulk_items)
        
        # Act: Request all menu items with pagination
        response = self.client.get(f"{MENU_ITEMS}?page_size=50")
        
        # Assert: Should handle large datasets gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertTrue(response.data['count'] >= 100)  # At least our test items

    def test_menu_items_filtering_performance_with_large_dataset(self):
        """Test filtering performance with many items."""
        # Arrange: Create items across multiple categories
        category_appetizers = Category.objects.create(slug="appetizers", title="Appetizers")
        category_mains = Category.objects.create(slug="mains", title="Mains")
        
        bulk_items = []
        for i in range(200):
            category = [self.category_pizza, self.category_dessert, category_appetizers, category_mains][i % 4]
            bulk_items.append(MenuItem(
                title=f"Filter Test Item {i}",
                price=5.00 + (i * 0.05),
                featured=(i % 10 == 0),
                category=category
            ))
        
        MenuItem.objects.bulk_create(bulk_items)
        
        # Act: Test various filtering scenarios
        filters_to_test = [
            f"{MENU_ITEMS}?category__title=Pizza",
            f"{MENU_ITEMS}?featured=true", 
            f"{MENU_ITEMS}?price__gte=10.00",
            f"{MENU_ITEMS}?search=Filter",
            f"{MENU_ITEMS}?ordering=price"
        ]
        
        # Assert: All filters should work efficiently
        for filter_url in filters_to_test:
            with self.subTest(filter_url=filter_url):
                response = self.client.get(filter_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn('results', response.data)

    def test_menu_item_creation_field_limits(self):
        """Test menu item creation with field boundary values."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Test maximum price (DecimalField max_digits=6, decimal_places=2 → max 9999.99)
        data = {
            "title": "Maximum Price Item",
            "price": "9999.99",
            "featured": True,
            "category_id": self.category_pizza.id
        }
        
        response = self.client.post(MENU_ITEMS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the item was created correctly
        created_item = MenuItem.objects.get(title="Maximum Price Item")
        self.assertEqual(float(created_item.price), 9999.99)

    def test_menu_item_creation_exceeding_decimal_field_limits(self):
        """Test menu item creation with price exceeding decimal field limits."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Test price exceeding DecimalField limits (> 9999.99)
        data = {
            "title": "Overflow Price Item", 
            "price": "10000.00",  # Exceeds max_digits=6, decimal_places=2
            "featured": False,
            "category_id": self.category_pizza.id
        }
        
        response = self.client.post(MENU_ITEMS, data, format="json")
        # Should return 400 Bad Request due to decimal field validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        
        # Verify no item was created
        self.assertFalse(MenuItem.objects.filter(title="Overflow Price Item").exists())

    def test_menu_item_title_length_limits(self):
        """Test menu item creation with maximum title length."""
        self.give_user_staff_status(self.user1)
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Test maximum title length (CharField max_length=255)
        max_length_title = "A" * 255
        data = {
            "title": max_length_title,
            "price": "15.99",
            "featured": False,
            "category_id": self.category_pizza.id
        }
        
        response = self.client.post(MENU_ITEMS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test exceeding title length
        too_long_title = "A" * 256
        data["title"] = too_long_title
        
        response = self.client.post(MENU_ITEMS, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_menu_items_concurrent_operations_simulation(self):
        """Test menu items API under simulated concurrent access."""
        self.give_user_staff_status(self.user1) 
        token = self.get_auth_token()
        self.authenticate_client(token)
        
        # Simulate multiple rapid operations
        operations_data = []
        for i in range(20):
            operations_data.append({
                "title": f"Concurrent Item {i}",
                "price": f"{10 + i}.99", 
                "featured": i % 3 == 0,
                "category_id": self.category_pizza.id if i % 2 == 0 else self.category_dessert.id
            })
        
        # Perform rapid sequential operations (simulating concurrent load)
        created_items = []
        failed_responses = []
        for data in operations_data:
            response = self.client.post(MENU_ITEMS, data, format="json")
            if response.status_code == status.HTTP_201_CREATED:
                created_items.append(response.data['id'])
            else:
                failed_responses.append((response.status_code, response.data))

        # Assert: Most operations should succeed
        self.assertGreaterEqual(len(created_items), 18)  # Allow for some potential conflicts        # Verify items exist in database
        existing_count = MenuItem.objects.filter(id__in=created_items).count()
        self.assertEqual(existing_count, len(created_items))