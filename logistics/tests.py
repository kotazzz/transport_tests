from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Seller, Location, Order, Item, Shipment, Route
from .forms import (
    RouteForm,
    SellerForm,
    LocationForm,
    OrderForm,
    ItemForm,
    ShipmentForm,
)
from datetime import timedelta
import shortuuid
from django.db.models import Q


class LogisticsTests(TestCase):
    def setUp(self):
        # Create a client for making requests
        self.client = Client()

        # Create a seller
        self.seller = Seller.objects.create(name="Test Seller", contact="test@example.com")

        # Create a warehouse location
        self.warehouse = Location.objects.create(
            name="Test Warehouse", location_type="warehouse", address="Test Address 1"
        )

        # Create a pickup location
        self.pickup = Location.objects.create(
            name="Test Pickup", location_type="pickup", address="Test Address 2"
        )

        # Create a route
        self.route = Route.objects.create(
            from_location=self.warehouse,
            to_location=self.pickup,
            travel_time=timedelta(hours=2),
            active=True,
        )

        # Create an order
        self.order = Order.objects.create(seller=self.seller, destination=self.pickup)

        # Create an item
        self.item = Item.objects.create(
            order=self.order,
            description="Test Item",
            quantity=1,
            current_location=self.warehouse,
        )

        # Create a shipment
        self.shipment = Shipment.objects.create(
            shipment_number=f"SHP-{shortuuid.ShortUUID().random(length=8).upper()}",
            from_location=self.warehouse,
            to_location=self.pickup,
        )
        self.shipment.items.add(self.item)

    def test_dashboard_view(self):
        """Test the dashboard view"""
        url = reverse("dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/dashboard/index.html")

    def test_seller_dashboard_view(self):
        """Test the seller dashboard view"""
        url = reverse("seller_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/seller/dashboard.html")

    def test_seller_detail_view(self):
        """Test the seller detail view"""
        url = reverse("seller_detail", args=[self.seller.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/seller/detail.html")

    def test_warehouse_dashboard_view(self):
        """Test the warehouse dashboard view"""
        url = reverse("warehouse_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/warehouse/dashboard.html")

    def test_warehouse_detail_view(self):
        """Test the warehouse detail view"""
        url = reverse("warehouse_detail", args=[self.warehouse.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/warehouse/detail.html")

    def test_pickup_dashboard_view(self):
        """Test the pickup dashboard view"""
        url = reverse("pickup_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/pickup/dashboard.html")

    def test_pickup_detail_view(self):
        """Test the pickup detail view"""
        url = reverse("pickup_detail", args=[self.pickup.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/pickup/detail.html")

    def test_order_list_view(self):
        """Test the order list view"""
        url = reverse("order_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/orders/list.html")

    def test_order_detail_view(self):
        """Test the order detail view"""
        url = reverse("order_detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/orders/detail.html")

    def test_shipment_list_view(self):
        """Test the shipment list view"""
        url = reverse("shipment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/shipments/list.html")

    def test_shipment_detail_view(self):
        """Test the shipment detail view"""
        url = reverse("shipment_detail", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/shipments/detail.html")

    def test_route_list_view(self):
        """Test the route list view"""
        url = reverse("route_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/routes/list.html")

    def test_route_detail_view(self):
        """Test the route detail view"""
        url = reverse("route_detail", args=[self.route.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/routes/detail.html")

    def test_seller_create_view(self):
        """Test the seller create view"""
        url = reverse("seller_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/seller/form.html")

        # Test form submission
        data = {"name": "New Seller", "contact": "new@example.com"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Seller.objects.count(), 2)  # Check if a new seller is created

    def test_seller_edit_view(self):
        """Test the seller edit view"""
        url = reverse("seller_edit", args=[self.seller.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/seller/form.html")

        # Test form submission
        data = {"name": "Updated Seller", "contact": "updated@example.com"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.seller.refresh_from_db()  # Refresh the object from the database
        self.assertEqual(self.seller.name, "Updated Seller")  # Check if the seller is updated

    def test_seller_delete_view(self):
        """Test the seller delete view"""
        url = reverse("seller_delete", args=[self.seller.id])

        # Test delete
        self.order.status = "delivered"  # Change order status to allow deletion
        self.order.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Seller.objects.count(), 0)  # Check if the seller is deleted

    def test_location_create_view(self):
        """Test the location create view"""
        url = reverse("location_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/locations/form.html")

        # Test form submission
        data = {
            "name": "New Location",
            "location_type": "warehouse",
            "address": "New Address",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Location.objects.count(), 3)  # Check if a new location is created

    def test_location_edit_view(self):
        """Test the location edit view"""
        url = reverse("location_edit", args=[self.warehouse.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/locations/form.html")

        # Test form submission
        data = {"name": "Updated Location", "location_type": "warehouse", "address": "Updated Address"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.warehouse.refresh_from_db()  # Refresh the object from the database
        self.assertEqual(self.warehouse.name, "Updated Location")  # Check if the location is updated

    def test_location_delete_view(self):
        """Test the location delete view"""
        url = reverse("location_delete", args=[self.warehouse.id])

        # Test delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Location.objects.count(), 2)  # Check if the location is deleted

    def test_order_create_view(self):
        """Test the order create view"""
        url = reverse("order_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/orders/form.html")

        # Test form submission
        data = {"seller": self.seller.id, "status": "pending", "destination": self.pickup.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Order.objects.count(), 2)  # Check if a new order is created

    def test_order_edit_view(self):
        """Test the order edit view"""
        url = reverse("order_edit", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/orders/form.html")

        # Test form submission
        data = {"seller": self.seller.id, "status": "delivered", "destination": self.pickup.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.order.refresh_from_db()  # Refresh the object from the database
        self.assertEqual(self.order.status, "delivered")  # Check if the order is updated

    def test_order_delete_view(self):
        """Test the order delete view"""
        url = reverse("order_delete", args=[self.order.id])

        # Test delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Order.objects.count(), 0)  # Check if the order is deleted

    def test_item_add_view(self):
        """Test the item add view"""
        url = reverse("item_add", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/orders/item_form.html")

        # Test form submission
        data = {
            "description": "New Item",
            "quantity": 2,
            "status": "created",
            "current_location": self.warehouse.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Item.objects.count(), 2)  # Check if a new item is created

    def test_item_edit_view(self):
        """Test the item edit view"""
        url = reverse("item_edit", args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/orders/item_form.html")

        # Test form submission
        data = {
            "description": "Updated Item",
            "quantity": 3,
            "status": "at_warehouse",
            "current_location": self.warehouse.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.item.refresh_from_db()  # Refresh the object from the database
        self.assertEqual(self.item.description, "Updated Item")  # Check if the item is updated

    def test_item_delete_view(self):
        """Test the item delete view"""
        url = reverse("item_delete", args=[self.item.id])

        # Test delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Item.objects.count(), 0)  # Check if the item is deleted

    def test_create_shipment_manual_view(self):
        """Test the create shipment manual view"""
        url = reverse("create_shipment_manual")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/shipments/form.html")

        # Test form submission
        data = {
            "shipment_number": f"SHP-{shortuuid.ShortUUID().random(length=8).upper()}",
            "vehicle_info": "Test Vehicle",
            "from_location": self.warehouse.id,
            "to_location": self.pickup.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Shipment.objects.count(), 2)  # Check if a new shipment is created

    def test_shipment_delete_view(self):
        """Test the shipment delete view"""
        url = reverse("shipment_delete", args=[self.shipment.id])

        # Test delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Shipment.objects.count(), 0)  # Check if the shipment is deleted

    def test_route_create_view(self):
        """Test the route create view"""
        url = reverse("route_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/routes/form.html")

        # Create a new unique location for the test
        new_destination = Location.objects.create(
            name="New Test Destination", location_type="pickup", address="New Test Address 3"
        )

        # Test form submission with unique locations
        data = {
            "from_location": self.warehouse.id,
            "to_location": new_destination.id, # Use the new location
            "travel_time": "1 02:30:00",
            "active": True,
        }
        response = self.client.post(url, data)
        # Expect redirect on successful creation of a unique route
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Route.objects.count(), 2)  # Check if a new route is created

    def test_route_edit_view(self):
        """Test the route edit view"""
        url = reverse("route_edit", args=[self.route.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/routes/form.html")

        # Test form submission
        data = {
            "from_location": self.warehouse.id,
            "to_location": self.pickup.id,
            "travel_time": "1 02:30:00",
            "active": False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.route.refresh_from_db()  # Refresh the object from the database
        self.assertEqual(self.route.active, False)  # Check if the route is updated

    def test_route_toggle_status_view(self):
        """Test the route toggle status view"""
        url = reverse("route_toggle_status", args=[self.route.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Test toggle status
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful toggle
        self.route.refresh_from_db()  # Refresh the object from the database
        self.assertEqual(self.route.active, False)  # Check if the route is toggled

    def test_route_delete_view(self):
        """Test the route delete view"""
        url = reverse("route_delete", args=[self.route.id])
        self.route.active = False
        self.route.save()

        # Test delete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect after successful delete
        self.assertEqual(Route.objects.count(), 1)  # Check if the route is deleted

    def test_create_shipments_for_order_view(self):
        """Test the create shipments for order view"""
        url = reverse("create_shipments_for_order", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_update_item_status_view(self):
        """Test the update item status view"""
        url = reverse("update_item_status", args=[self.item.id, "at_warehouse"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_receive_items_at_warehouse_view(self):
        """Test the receive items at warehouse view"""
        url = reverse("receive_items_at_warehouse", args=[self.warehouse.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/warehouse/receive_items.html")

    def test_deliver_item_to_customer_view(self):
        """Test the deliver item to customer view"""
        self.item.current_location = self.pickup
        self.item.status = "at_warehouse"
        self.item.save()
        url = reverse("deliver_item_to_customer", args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_create_shipment_from_warehouse_view(self):
        """Test the create shipment from warehouse view"""
        url = reverse("create_shipment_from_warehouse", args=[self.warehouse.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/shipments/form.html")

    def test_shipment_loading_view(self):
        """Test the shipment loading view"""
        url = reverse("shipment_loading", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_shipment_start_transit_view(self):
        """Test the shipment start transit view"""
        url = reverse("shipment_start_transit", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_shipment_mark_arrived_view(self):
        """Test the shipment mark arrived view"""
        self.shipment.status = "in_transit"
        self.shipment.departure_time = timezone.now() - timedelta(hours=1)
        self.shipment.mark_as_in_transit()
        self.shipment.save()
        url = reverse("shipment_mark_arrived", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_shipment_unload_view(self):
        """Test the shipment unload view"""
        self.shipment.status = "arrived"
        self.shipment.arrival_time = timezone.now()
        self.shipment.save()
        url = reverse("shipment_unload", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/shipments/unload.html")

    def test_shipment_complete_view(self):
        """Test the shipment complete view"""
        self.shipment.status = "unloaded"
        self.shipment.save()
        url = reverse("shipment_complete", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_shipment_cancel_view(self):
        """Test the shipment cancel view"""
        url = reverse("shipment_cancel", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_add_items_to_shipment_enhanced_view(self):
        """Test the add items to shipment enhanced view"""
        url = reverse("add_items_to_shipment_enhanced", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logistics/shipments/add_items_enhanced.html")

    def test_route_form_validation(self):
        """Test the route form validation"""
        form = RouteForm(
            {
                "from_location": self.warehouse.id,
                "to_location": self.warehouse.id,
                "travel_time": "1 02:30:00",
                "active": True,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Начальный и конечный пункты маршрута должны быть разными",
            form.errors["__all__"],
        )

    def test_shipment_form_validation(self):
        """Test the shipment form validation"""
        form = ShipmentForm(
            {
                "shipment_number": f"SHP-{shortuuid.ShortUUID().random(length=8).upper()}",
                "vehicle_info": "Test Vehicle",
                "from_location": self.warehouse.id,
                "to_location": self.warehouse.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Начальный и конечный пункты доставки должны быть разными",
            form.errors["__all__"],
        )

    def test_shipment_form_route_validation(self):
        """Test the shipment form route validation"""
        # Deactivate the existing route
        self.route.active = False
        self.route.save()

        form = ShipmentForm(
            {
                "shipment_number": f"SHP-{shortuuid.ShortUUID().random(length=8).upper()}",
                "vehicle_info": "Test Vehicle",
                "from_location": self.warehouse.id,
                "to_location": self.pickup.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Между указанными точками нет активного маршрута", form.errors["__all__"]
        )

    def test_item_update_status(self):
        """Test the item update status method"""
        self.item.update_status("at_warehouse", self.warehouse)
        self.assertEqual(self.item.status, "at_warehouse")
        self.assertEqual(self.item.current_location, self.warehouse)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_order_update_status(self):
        """Test the order update status method"""
        self.item.status = "delivered"
        self.item.save()
        self.order.update_status()
        self.assertEqual(self.order.status, "delivered")

    def test_shipment_mark_as_in_transit(self):
        """Test the shipment mark as in transit method"""
        self.shipment.mark_as_in_transit()
        self.assertEqual(self.shipment.status, "in_transit")
        self.assertIsNotNone(self.shipment.departure_time)
        self.assertIsNotNone(self.shipment.estimated_arrival_time)

    def test_shipment_mark_as_arrived(self):
        """Test the shipment mark as arrived method"""
        self.shipment.status = "in_transit"
        self.shipment.departure_time = timezone.now() - timedelta(hours=1)
        self.shipment.mark_as_in_transit()
        self.shipment.save()
        self.shipment.mark_as_arrived()
        self.assertEqual(self.shipment.status, "arrived")
        self.assertIsNotNone(self.shipment.arrival_time)

    def test_shipment_complete_shipment(self):
        """Test the shipment complete shipment method"""
        self.shipment.status = "unloaded"
        self.shipment.save()
        self.shipment.complete_shipment()
        self.assertEqual(self.shipment.status, "completed")

    def test_shipment_cancel_shipment(self):
        """Test the shipment cancel shipment method"""
        # Ensure item is initially at the warehouse
        self.item.status = 'at_warehouse'
        self.item.current_location = self.warehouse
        self.item.save()
        self.shipment.items.set([self.item]) # Ensure item is in shipment

        # Mark the shipment as in transit (this updates item status to 'in_transit')
        self.assertTrue(self.shipment.mark_as_in_transit())
        self.shipment.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.shipment.status, "in_transit")
        self.assertEqual(self.item.status, "in_transit") # Verify item status changed

        # Now, cancel the shipment
        self.assertTrue(self.shipment.cancel_shipment()) # Call the cancel method

        # Refresh objects from DB
        self.shipment.refresh_from_db()
        self.item.refresh_from_db()

        # Assert final states
        self.assertEqual(self.shipment.status, "cancelled")
        # Item status should revert to 'at_warehouse' at the origin location
        self.assertEqual(self.item.status, "at_warehouse")
        self.assertEqual(self.item.current_location, self.warehouse)

    def test_route_clean(self):
        """Test the route clean method"""
        route = Route(from_location=self.warehouse, to_location=self.warehouse)
        with self.assertRaises(ValidationError):
            route.clean()

    def test_route_save(self):
        """Test the route save method"""
        # Ensure the new route is unique
        new_pickup = Location.objects.create(
            name="Another Test Pickup", location_type="pickup", address="Another Test Address"
        )
        route = Route(from_location=self.warehouse, to_location=new_pickup, travel_time=timedelta(hours=1))
        route.save()
        self.assertEqual(Route.objects.count(), 2)

    def test_shipment_start_unloading(self):
        """Test the shipment start unloading method"""
        self.shipment.status = "arrived"
        self.shipment.arrival_time = timezone.now()
        self.shipment.save()
        self.assertTrue(self.shipment.start_unloading())
        self.assertEqual(self.shipment.status, "unloading")

    def test_shipment_process_unloaded_item(self):
        """Test the shipment process unloaded item method"""
        self.shipment.status = "unloading"
        self.shipment.save()
        self.assertTrue(self.shipment.process_unloaded_item(self.item, "at_warehouse"))
        self.assertEqual(self.item.status, "at_warehouse")
        self.assertEqual(self.item.current_location, self.pickup)

    def test_shipment_check_and_finish_unloading(self):
        """Test the shipment check and finish unloading method"""
        self.shipment.status = "unloading"
        self.shipment.save()
        self.shipment.process_unloaded_item(self.item, "at_warehouse")
        self.item.save()
        self.assertTrue(self.shipment.check_and_finish_unloading())
        self.assertEqual(self.shipment.status, "unloaded")

    def test_order_delete_with_items_in_transit(self):
        """Test that an order cannot be deleted if items are in transit"""
        self.item.status = "in_transit"
        self.item.save()
        url = reverse("order_delete", args=[self.order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "Невозможно удалить заказ, содержащий товары в пути.",
            [m.message for m in response.wsgi_request._messages],
        )

    def test_shipment_finish_unloading_view(self):
        """Test the shipment_finish_unloading view"""
        self.shipment.status = "unloading"
        self.shipment.save()
        url = reverse("shipment_finish_unloading", args=[self.shipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
