from django.urls import path
from . import views

urlpatterns = [
    # Dashboard views
    path('', views.dashboard, name='dashboard'),
    
    # Seller views
    path('sellers/', views.seller_dashboard, name='seller_dashboard'),
    path('sellers/<int:seller_id>/', views.seller_detail, name='seller_detail'),
    path('sellers/create/', views.seller_create, name='seller_create'),
    path('sellers/<int:seller_id>/edit/', views.seller_edit, name='seller_edit'),
    path('sellers/<int:seller_id>/delete/', views.seller_delete, name='seller_delete'),
    
    # Warehouse views
    path('warehouses/', views.warehouse_dashboard, name='warehouse_dashboard'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<int:warehouse_id>/create-shipment/', views.create_shipment_from_warehouse, name='create_shipment_from_warehouse'),
    
    # Pickup point views
    path('pickup/', views.pickup_dashboard, name='pickup_dashboard'),
    path('pickup/<int:pickup_id>/', views.pickup_detail, name='pickup_detail'),
    
    # Location views (general)
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:location_id>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:location_id>/delete/', views.location_delete, name='location_delete'),
    
    # Order views
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:order_id>/create-shipments/', views.create_shipments_for_order, name='create_shipments_for_order'),
    path('orders/<int:order_id>/add-item/', views.item_add, name='item_add'),
    path('items/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:item_id>/delete/', views.item_delete, name='item_delete'),
    
    # Shipment views
    path('shipments/', views.shipment_list, name='shipment_list'),
    path('shipments/<int:shipment_id>/', views.shipment_detail, name='shipment_detail'),
    path('shipments/create/', views.create_shipment_manual, name='create_shipment_manual'),
    path('shipments/<int:shipment_id>/mark-arrived/', views.mark_shipment_arrived, name='mark_shipment_arrived'),
    path('shipments/<int:shipment_id>/add-items/', views.add_items_to_shipment, name='add_items_to_shipment'),
    path('shipments/<int:shipment_id>/add-items/enhanced/', views.add_items_to_shipment_enhanced, name='add_items_to_shipment_enhanced'),
    
    # Route views
    path('routes/', views.route_list, name='route_list'),
    path('routes/<int:route_id>/', views.route_detail, name='route_detail'),
    path('routes/create/', views.route_create, name='route_create'),
    path('routes/<int:route_id>/edit/', views.route_edit, name='route_edit'),
    path('routes/<int:route_id>/toggle-status/', views.route_toggle_status, name='route_toggle_status'),
    path('routes/<int:route_id>/delete/', views.route_delete, name='route_delete'),
]