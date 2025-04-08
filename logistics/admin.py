from django.contrib import admin
from .models import Seller, Location, Order, Item, Shipment, Route


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ("name", "contact")
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "location_type", "address")
    list_filter = ("location_type",)
    search_fields = ("name", "address")


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "seller", "created_at", "status", "destination")
    list_filter = ("status", "seller")
    search_fields = ("id",)
    date_hierarchy = "created_at"
    inlines = [ItemInline]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("description", "quantity", "status", "order", "current_location")
    list_filter = ("status", "current_location")
    search_fields = ("description",)


class ShipmentItemInline(admin.TabularInline):
    model = Shipment.items.through
    extra = 1


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "shipment_number",
        "from_location",
        "to_location",
        "departure_time",
        "arrival_time",
    )
    list_filter = ("from_location", "to_location")
    search_fields = ("shipment_number",)
    date_hierarchy = "departure_time"
    inlines = [ShipmentItemInline]
    exclude = ("items",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("from_location", "to_location", "cost", "travel_time", "active")
    list_filter = ("active", "from_location", "to_location")
