from django.urls import path
from . import views

urlpatterns = [
    # Dashboard views
    path("", views.dashboard, name="dashboard"),
    # Seller views
    path("sellers/", views.seller_dashboard, name="seller_dashboard"),
    path("sellers/<int:seller_id>/", views.seller_detail, name="seller_detail"),
    path("sellers/create/", views.seller_create, name="seller_create"),
    path("sellers/<int:seller_id>/edit/", views.seller_edit, name="seller_edit"),
    path("sellers/<int:seller_id>/delete/", views.seller_delete, name="seller_delete"),
    # Warehouse views
    path("warehouses/", views.warehouse_dashboard, name="warehouse_dashboard"),
    path(
        "warehouses/<int:warehouse_id>/",
        views.warehouse_detail,
        name="warehouse_detail",
    ),
    path(
        "warehouses/<int:warehouse_id>/create-shipment/",
        views.create_shipment_from_warehouse,
        name="create_shipment_from_warehouse",
    ),
    path(
        "warehouses/<int:warehouse_id>/receive-items/",
        views.receive_items_at_warehouse,
        name="receive_items_at_warehouse",
    ),
    # Pickup point views
    path("pickup/", views.pickup_dashboard, name="pickup_dashboard"),
    path("pickup/<int:pickup_id>/", views.pickup_detail, name="pickup_detail"),
    path(
        "items/<int:item_id>/deliver-to-customer/",
        views.deliver_item_to_customer,
        name="deliver_item_to_customer",
    ),
    # Location views (general)
    path("locations/create/", views.location_create, name="location_create"),
    path(
        "locations/<int:location_id>/edit/", views.location_edit, name="location_edit"
    ),
    path(
        "locations/<int:location_id>/delete/",
        views.location_delete,
        name="location_delete",
    ),
    # Order views
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orders/create/", views.order_create, name="order_create"),
    path("orders/<int:order_id>/edit/", views.order_edit, name="order_edit"),
    path("orders/<int:order_id>/delete/", views.order_delete, name="order_delete"),
    path(
        "orders/<int:order_id>/create-shipments/",
        views.create_shipments_for_order,
        name="create_shipments_for_order",
    ),
    path("orders/<int:order_id>/add-item/", views.item_add, name="item_add"),
    path("items/<int:item_id>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:item_id>/delete/", views.item_delete, name="item_delete"),
    path(
        "items/<int:item_id>/update-status/<str:new_status>/",
        views.update_item_status,
        name="update_item_status",
    ),
    # Shipment views
    path("shipments/", views.shipment_list, name="shipment_list"),
    path("shipments/<int:shipment_id>/", views.shipment_detail, name="shipment_detail"),
    path(
        "shipments/create/", views.create_shipment_manual, name="create_shipment_manual"
    ),
    path(
        "shipments/<int:shipment_id>/delete/",
        views.shipment_delete,
        name="shipment_delete",
    ),
    # Shipment workflow views - new process stages
    path(
        "shipments/<int:shipment_id>/loading/",
        views.shipment_loading,
        name="shipment_loading",
    ),
    path(
        "shipments/<int:shipment_id>/start-transit/",
        views.shipment_start_transit,
        name="shipment_start_transit",
    ),
    path(
        "shipments/<int:shipment_id>/mark-arrived/",
        views.shipment_mark_arrived,
        name="shipment_mark_arrived",
    ),
    path(
        "shipments/<int:shipment_id>/unload/",
        views.shipment_unload,
        name="shipment_unload",
    ),
    path(
        "shipments/<int:shipment_id>/finish-unloading/",
        views.shipment_finish_unloading,
        name="shipment_finish_unloading",
    ),
    path(
        "shipments/<int:shipment_id>/complete/",
        views.shipment_complete,
        name="shipment_complete",
    ),
    path(
        "shipments/<int:shipment_id>/cancel/",
        views.shipment_cancel,
        name="shipment_cancel",
    ),
    path(
        "shipments/<int:shipment_id>/add-items/",
        views.add_items_to_shipment,
        name="add_items_to_shipment",
    ),
    path(
        "shipments/<int:shipment_id>/add-items/enhanced/",
        views.add_items_to_shipment_enhanced,
        name="add_items_to_shipment_enhanced",
    ),
    # Route views
    path("routes/", views.route_list, name="route_list"),
    path("routes/<int:route_id>/", views.route_detail, name="route_detail"),
    path("routes/create/", views.route_create, name="route_create"),
    path("routes/<int:route_id>/edit/", views.route_edit, name="route_edit"),
    path(
        "routes/<int:route_id>/toggle-status/",
        views.route_toggle_status,
        name="route_toggle_status",
    ),
    path("routes/<int:route_id>/delete/", views.route_delete, name="route_delete"),
]
