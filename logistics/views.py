from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models import Seller, Location, Order, Item, Shipment, Route
from .utils.routing import RoutingEngine
from .forms import RouteForm, SellerForm, LocationForm, OrderForm, ItemForm, ShipmentForm, ItemSelectionForm
import uuid

def dashboard(request):
    """Main dashboard with overall system statistics"""
    context = {
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'in_transit_orders': Order.objects.filter(status='in_transit').count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'total_shipments': Shipment.objects.count(),
        'active_shipments': Shipment.objects.filter(arrival_time__isnull=True).count(),
        'total_locations': Location.objects.count(),
        'total_sellers': Seller.objects.count(),
        'recent_orders': Order.objects.order_by('-created_at')[:5],
        'upcoming_shipments': Shipment.objects.filter(
            departure_time__gt=timezone.now()
        ).order_by('departure_time')[:5],
    }
    return render(request, 'logistics/dashboard/index.html', context)

def seller_dashboard(request):
    """Dashboard for sellers showing their orders"""
    sellers = Seller.objects.annotate(
        total_orders=Count('order'),
        pending_orders=Count('order', filter=Q(order__status='pending'))
    )
    
    context = {
        'sellers': sellers,
    }
    return render(request, 'logistics/seller/dashboard.html', context)

def seller_detail(request, seller_id):
    """Detailed view for a specific seller"""
    seller = get_object_or_404(Seller, pk=seller_id)
    orders = Order.objects.filter(seller=seller).order_by('-created_at')
    
    context = {
        'seller': seller,
        'orders': orders,
        'pending_orders': orders.filter(status='pending'),
        'in_transit_orders': orders.filter(status='in_transit'),
        'delivered_orders': orders.filter(status='delivered'),
    }
    return render(request, 'logistics/seller/detail.html', context)

def warehouse_dashboard(request):
    """Dashboard for warehouses"""
    warehouses = Location.objects.filter(location_type='warehouse')
    
    context = {
        'warehouses': warehouses,
    }
    return render(request, 'logistics/warehouse/dashboard.html', context)

def warehouse_detail(request, warehouse_id):
    """Detailed view for a specific warehouse"""
    warehouse = get_object_or_404(Location, pk=warehouse_id, location_type='warehouse')
    
    # Get incoming and outgoing shipments
    incoming_shipments = Shipment.objects.filter(to_location=warehouse)
    outgoing_shipments = Shipment.objects.filter(from_location=warehouse)
    
    # Get items currently at this warehouse
    warehouse_items = Item.objects.filter(current_location=warehouse)
    
    context = {
        'warehouse': warehouse,
        'incoming_shipments': incoming_shipments,
        'outgoing_shipments': outgoing_shipments,
        'warehouse_items': warehouse_items,
    }
    return render(request, 'logistics/warehouse/detail.html', context)

def pickup_dashboard(request):
    """Dashboard for pickup points"""
    pickup_points = Location.objects.filter(location_type='pickup')
    
    context = {
        'pickup_points': pickup_points,
    }
    return render(request, 'logistics/pickup/dashboard.html', context)

def pickup_detail(request, pickup_id):
    """Detailed view for a specific pickup point"""
    pickup = get_object_or_404(Location, pk=pickup_id, location_type='pickup')
    
    # Get orders for this pickup point
    pickup_orders = Order.objects.filter(destination=pickup)
    
    # Get incoming shipments
    incoming_shipments = Shipment.objects.filter(to_location=pickup)
    
    # Get items ready for pickup
    ready_items = Item.objects.filter(current_location=pickup, status='at_warehouse')
    
    context = {
        'pickup': pickup,
        'pickup_orders': pickup_orders,
        'incoming_shipments': incoming_shipments,
        'ready_items': ready_items,
    }
    return render(request, 'logistics/pickup/detail.html', context)

def order_list(request):
    """List of all orders with filtering options"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Handle filters
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    seller_filter = request.GET.get('seller')
    if seller_filter:
        orders = orders.filter(seller_id=seller_filter)
    
    context = {
        'orders': orders,
        'sellers': Seller.objects.all(),
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'logistics/orders/list.html', context)

def order_detail(request, order_id):
    """Detailed view for a specific order"""
    order = get_object_or_404(Order, pk=order_id)
    items = Item.objects.filter(order=order)
    
    # Получаем перевозки, связанные с этим заказом
    # Используем distinct() для удаления дубликатов
    related_shipments = Shipment.objects.filter(
        items__order=order
    ).distinct().order_by('-departure_time')
    
    context = {
        'order': order,
        'items': items,
        'related_shipments': related_shipments,
        'now': timezone.now(),
    }
    return render(request, 'logistics/orders/detail.html', context)

def shipment_list(request):
    """List of all shipments with filtering options"""
    shipments = Shipment.objects.all().order_by('-departure_time')
    
    from_location = request.GET.get('from_location')
    if from_location:
        shipments = shipments.filter(from_location_id=from_location)
        
    to_location = request.GET.get('to_location')
    if to_location:
        shipments = shipments.filter(to_location_id=to_location)
    
    context = {
        'shipments': shipments,
        'locations': Location.objects.all(),
    }
    return render(request, 'logistics/shipments/list.html', context)

def shipment_detail(request, shipment_id):
    """Detailed view for a specific shipment"""
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    items = shipment.items.all()
    
    context = {
        'shipment': shipment,
        'items': items,
    }
    return render(request, 'logistics/shipments/detail.html', context)

def route_list(request):
    """List of all routes with filtering options"""
    routes = Route.objects.all()
    
    from_location = request.GET.get('from_location')
    if from_location:
        routes = routes.filter(from_location_id=from_location)
        
    to_location = request.GET.get('to_location')
    if to_location:
        routes = routes.filter(to_location_id=to_location)
    
    context = {
        'routes': routes,
        'locations': Location.objects.all(),
    }
    return render(request, 'logistics/routes/list.html', context)

def create_shipments_for_order(request, order_id):
    """Create shipments for all items in an order"""
    order = get_object_or_404(Order, pk=order_id)
    
    if order.status != 'pending':
        messages.error(request, 'Можно создавать перевозки только для заказов в статусе "Ожидает отправки"')
        return redirect('order_detail', order_id=order.id)
    
    # Get all items that need shipping
    items_to_ship = Item.objects.filter(order=order, status__in=['created', 'at_warehouse'])
    
    if not items_to_ship:
        messages.warning(request, 'Нет товаров, требующих отправки')
        return redirect('order_detail', order_id=order.id)
    
    if not order.destination:
        messages.error(request, 'У заказа не указан пункт назначения')
        return redirect('order_detail', order_id=order.id)
    
    # Use the routing engine to create optimal shipments
    created_shipments = RoutingEngine.create_shipments_for_items(
        items_to_ship, 
        order.destination.id
    )
    
    if created_shipments:
        messages.success(
            request, 
            f'Успешно создано {len(created_shipments)} перевозок для заказа #{order.id}'
        )
    else:
        messages.warning(request, 'Не удалось создать перевозки. Проверьте наличие маршрутов.')
    
    return redirect('order_detail', order_id=order.id)

def mark_shipment_arrived(request, shipment_id):
    """Mark a shipment as arrived at its destination"""
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    
    if shipment.arrival_time:
        messages.warning(request, 'Перевозка уже отмечена как прибывшая')
    else:
        shipment.mark_as_arrived()
        messages.success(request, f'Перевозка {shipment.shipment_number} отмечена как прибывшая')
    
    return redirect('shipment_detail', shipment_id=shipment.id)

def route_detail(request, route_id):
    """Detailed view for a specific route"""
    route = get_object_or_404(Route, pk=route_id)
    
    # Get recent shipments using this route
    recent_shipments = Shipment.objects.filter(
        from_location=route.from_location,
        to_location=route.to_location
    ).order_by('-departure_time')[:5]
    
    shipment_count = Shipment.objects.filter(
        from_location=route.from_location,
        to_location=route.to_location
    ).count()
    
    context = {
        'route': route,
        'recent_shipments': recent_shipments,
        'shipment_count': shipment_count,
    }
    return render(request, 'logistics/routes/detail.html', context)

def route_create(request):
    """Create a new route"""
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f'Маршрут успешно создан')
            return redirect('route_detail', route_id=route.id)
    else:
        form = RouteForm()
    
    context = {
        'form': form,
    }
    return render(request, 'logistics/routes/form.html', context)

def route_edit(request, route_id):
    """Edit an existing route"""
    route = get_object_or_404(Route, pk=route_id)
    
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f'Маршрут успешно обновлен')
            return redirect('route_detail', route_id=route.id)
    else:
        form = RouteForm(instance=route)
    
    context = {
        'form': form,
        'route': route,
    }
    return render(request, 'logistics/routes/form.html', context)

def route_toggle_status(request, route_id):
    """Toggle active status of a route"""
    route = get_object_or_404(Route, pk=route_id)
    
    if request.method == 'POST':
        route.active = not route.active
        route.save()
        
        status_text = "активирован" if route.active else "деактивирован"
        messages.success(request, f'Маршрут успешно {status_text}')
        
    return redirect('route_detail', route_id=route.id)

def route_delete(request, route_id):
    """Delete a route"""
    route = get_object_or_404(Route, pk=route_id)
    
    # Check if there are any active shipments using this route
    active_shipments = Shipment.objects.filter(
        from_location=route.from_location,
        to_location=route.to_location,
        arrival_time__isnull=True
    ).exists()
    
    if active_shipments:
        messages.error(request, 'Невозможно удалить маршрут, так как по нему есть активные перевозки')
        return redirect('route_detail', route_id=route.id)
    
    # Get route information for success message
    route_info = str(route)
    
    # Delete the route
    route.delete()
    
    messages.success(request, f'Маршрут {route_info} успешно удален')
    return redirect('route_list')

def seller_create(request):
    """Create a new seller"""
    if request.method == 'POST':
        form = SellerForm(request.POST)
        if form.is_valid():
            seller = form.save()
            messages.success(request, f'Продавец "{seller.name}" успешно создан')
            return redirect('seller_detail', seller_id=seller.id)
    else:
        form = SellerForm()
    
    context = {
        'form': form,
    }
    return render(request, 'logistics/seller/form.html', context)

def seller_edit(request, seller_id):
    """Edit an existing seller"""
    seller = get_object_or_404(Seller, pk=seller_id)
    
    if request.method == 'POST':
        form = SellerForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, f'Информация о продавце успешно обновлена')
            return redirect('seller_detail', seller_id=seller.id)
    else:
        form = SellerForm(instance=seller)
    
    context = {
        'form': form,
        'seller': seller,
    }
    return render(request, 'logistics/seller/form.html', context)

def seller_delete(request, seller_id):
    """Delete a seller"""
    seller = get_object_or_404(Seller, pk=seller_id)
    
    # Проверяем, есть ли у продавца активные заказы
    has_active_orders = Order.objects.filter(
        seller=seller, 
        status__in=['pending', 'in_transit']
    ).exists()
    
    if has_active_orders:
        messages.error(request, f'Невозможно удалить продавца "{seller.name}", так как у него есть активные заказы')
    else:
        seller_name = seller.name
        seller.delete()
        messages.success(request, f'Продавец "{seller_name}" успешно удален')
    
    return redirect('seller_dashboard')

def location_create(request):
    """Create a new location"""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Локация "{location.name}" успешно создана')
            
            if location.location_type == 'warehouse':
                return redirect('warehouse_detail', warehouse_id=location.id)
            else:
                return redirect('pickup_detail', pickup_id=location.id)
    else:
        form = LocationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'logistics/locations/form.html', context)

def location_edit(request, location_id):
    """Edit an existing location"""
    location = get_object_or_404(Location, pk=location_id)
    
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Информация о локации успешно обновлена')
            
            if location.location_type == 'warehouse':
                return redirect('warehouse_detail', warehouse_id=location.id)
            else:
                return redirect('pickup_detail', pickup_id=location.id)
    else:
        form = LocationForm(instance=location)
    
    context = {
        'form': form,
        'location': location,
    }
    return render(request, 'logistics/locations/form.html', context)

def location_delete(request, location_id):
    """Delete a location (warehouse or pickup point)"""
    location = get_object_or_404(Location, pk=location_id)
    
    # Проверяем, можно ли удалить локацию
    has_items = Item.objects.filter(current_location=location).exists()
    has_incoming = Shipment.objects.filter(to_location=location, arrival_time__isnull=True).exists()
    has_outgoing = Shipment.objects.filter(from_location=location, arrival_time__isnull=True).exists()
    
    if has_items or has_incoming or has_outgoing:
        messages.error(request, 
            f'Невозможно удалить локацию "{location.name}", так как она содержит товары '
            'или имеет активные перевозки'
        )
    else:
        location_type = location.location_type
        location_name = location.name
        location.delete()
        messages.success(request, f'Локация "{location_name}" успешно удалена')
    
    # Перенаправляем на соответствующую страницу в зависимости от типа локации
    if location.location_type == 'warehouse':
        return redirect('warehouse_dashboard')
    else:
        return redirect('pickup_dashboard')

def order_create(request):
    """Create a new order"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f'Заказ #{order.id} успешно создан')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm()
    
    context = {
        'form': form,
    }
    return render(request, 'logistics/orders/form.html', context)

def order_edit(request, order_id):
    """Edit an existing order"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Информация о заказе успешно обновлена')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'logistics/orders/form.html', context)

def item_add(request, order_id):
    """Add a new item to an order"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.save()
            
            # Update order status
            order.update_status()
            
            messages.success(request, f'Товар успешно добавлен в заказ #{order.id}')
            return redirect('order_detail', order_id=order.id)
    else:
        form = ItemForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'logistics/orders/item_form.html', context)

def item_edit(request, item_id):
    """Edit an existing item"""
    item = get_object_or_404(Item, pk=item_id)
    order = item.order
    
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            
            # Update order status
            order.update_status()
            
            messages.success(request, f'Информация о товаре успешно обновлена')
            return redirect('order_detail', order_id=order.id)
    else:
        form = ItemForm(instance=item)
    
    context = {
        'form': form,
        'item': item,
        'order': order,
    }
    return render(request, 'logistics/orders/item_form.html', context)

def item_delete(request, item_id):
    """Delete an item from an order"""
    item = get_object_or_404(Item, pk=item_id)
    order = item.order
    
    # Check if the item can be deleted (not in transit or delivered)
    if item.status in ['in_transit', 'delivered']:
        messages.error(request, 'Нельзя удалить товар в статусе "В перевозке" или "Доставлен"')
    else:
        # Remove the item from any shipments it might be in
        item.shipments.clear()
        
        # Delete the item
        item.delete()
        messages.success(request, 'Товар успешно удален из заказа')
        
        # Update order status
        order.update_status()
        
    return redirect('order_detail', order_id=order.id)

def create_shipment_manual(request):
    """Create a shipment manually"""
    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            
            # Calculate expected arrival time
            from_loc = form.cleaned_data['from_location']
            to_loc = form.cleaned_data['to_location']
            
            try:
                route = Route.objects.get(from_location=from_loc, to_location=to_loc, active=True)
                travel_time = route.travel_time
            except Route.DoesNotExist:
                travel_time = timezone.timedelta(hours=1)  # Default 1 hour if no route
            
            shipment.arrival_time = shipment.departure_time + travel_time
            shipment.save()
            
            messages.success(request, f'Перевозка #{shipment.shipment_number} успешно создана')
            return redirect('add_items_to_shipment', shipment_id=shipment.id)
    else:
        # Generate a unique shipment number
        shipment_number = f"SH-{uuid.uuid4().hex[:8].upper()}"
        form = ShipmentForm(initial={'shipment_number': shipment_number, 'departure_time': timezone.now()})
    
    context = {
        'form': form,
    }
    return render(request, 'logistics/shipments/form.html', context)

def add_items_to_shipment(request, shipment_id):
    """Add items to a shipment"""
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    
    if shipment.arrival_time and shipment.arrival_time < timezone.now():
        messages.error(request, 'Нельзя добавлять товары в уже прибывшую перевозку')
        return redirect('shipment_detail', shipment_id=shipment.id)
    
    if request.method == 'POST':
        form = ItemSelectionForm(request.POST, location=shipment.from_location)
        if form.is_valid():
            items = form.cleaned_data['items']
            
            for item in items:
                shipment.items.add(item)
                item.update_status('in_transit', shipment.from_location)
            
            messages.success(request, f'Товары успешно добавлены в перевозку #{shipment.shipment_number}')
            return redirect('shipment_detail', shipment_id=shipment.id)
    else:
        form = ItemSelectionForm(location=shipment.from_location)
    
    context = {
        'form': form,
        'shipment': shipment,
    }
    return render(request, 'logistics/shipments/add_items.html', context)

def create_shipment_from_warehouse(request, warehouse_id):
    """
    Создать перевозку от имени конкретного склада.
    Предварительно заполняет форму с указанием склада как точки отправления.
    """
    warehouse = get_object_or_404(Location, pk=warehouse_id, location_type='warehouse')
    
    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            
            # Расчет ожидаемого времени прибытия
            from_loc = form.cleaned_data['from_location']
            to_loc = form.cleaned_data['to_location']
            
            try:
                route = Route.objects.get(from_location=from_loc, to_location=to_loc, active=True)
                travel_time = route.travel_time
            except Route.DoesNotExist:
                travel_time = timezone.timedelta(hours=1)  # По умолчанию 1 час если нет маршрута
            
            # Устанавливаем время прибытия
            shipment.arrival_time = shipment.departure_time + travel_time
            shipment.save()
            
            messages.success(request, f'Перевозка #{shipment.shipment_number} успешно создана')
            return redirect('add_items_to_shipment_enhanced', shipment_id=shipment.id)
    else:
        # Генерация уникального номера перевозки
        shipment_number = f"SH-{uuid.uuid4().hex[:8].upper()}"
        form = ShipmentForm(initial={
            'shipment_number': shipment_number, 
            'from_location': warehouse,
            'departure_time': timezone.now()
        })
    
    context = {
        'form': form,
        'warehouse': warehouse,
        'page_title': f'Создание перевозки из {warehouse.name}'
    }
    return render(request, 'logistics/shipments/form.html', context)

def add_items_to_shipment_enhanced(request, shipment_id):
    """
    Улучшенный интерфейс для добавления товаров в перевозку.
    Обеспечивает более удобную фильтрацию и выбор товаров, как в системах Озона.
    """
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    warehouse = shipment.from_location
    
    if shipment.arrival_time and shipment.arrival_time < timezone.now():
        messages.error(request, 'Нельзя добавлять товары в уже прибывшую перевозку')
        return redirect('shipment_detail', shipment_id=shipment.id)
    
    # Товары, доступные для перевозки (находящиеся на складе отправления)
    # Расширяем диапазон статусов товаров, которые можно добавлять в перевозку
    available_items = Item.objects.filter(
        current_location=warehouse
    ).exclude(
        status__in=['in_transit', 'delivered']
    ).select_related('order')
    
    # Если нет доступных товаров, показываем предупреждение с диагностической информацией
    if not available_items.exists():
        # Проверяем сколько товаров вообще есть в системе
        total_items = Item.objects.count()
        # Проверяем сколько товаров есть на этом складе (независимо от статуса)
        all_items_in_warehouse = Item.objects.filter(current_location=warehouse).count()
        
        diagnostic_msg = (
            f"Нет доступных товаров для отправки. "
            f"Всего товаров в системе: {total_items}, "
            f"товаров на складе '{warehouse.name}': {all_items_in_warehouse}. "
            f"Возможно, все товары уже в пути или имеют статус 'доставлен'."
        )
        messages.warning(request, diagnostic_msg)
    
    # Фильтрация по номеру заказа, если указан
    order_filter = request.GET.get('order_id')
    if order_filter:
        available_items = available_items.filter(order_id=order_filter)
    
    # Фильтрация по описанию товара
    description_filter = request.GET.get('description')
    if description_filter:
        available_items = available_items.filter(description__icontains=description_filter)
    
    # Статус товара
    status_filter = request.GET.get('status')
    if status_filter:
        available_items = available_items.filter(status=status_filter)
    
    # Товары, уже добавленные в перевозку
    selected_items = shipment.items.all()
    selected_item_ids = [item.id for item in selected_items]
    
    # Обработка добавления/удаления товаров
    if request.method == 'POST':
        action = request.POST.get('action')
        item_ids = request.POST.getlist('item_ids')
        
        if action == 'add' and item_ids:
            # Добавляем выбранные товары в перевозку
            added_count = 0
            for item_id in item_ids:
                if int(item_id) not in selected_item_ids:
                    item = Item.objects.get(pk=item_id)
                    shipment.items.add(item)
                    item.update_status('in_transit', warehouse)
                    added_count += 1
            
            if added_count > 0:
                messages.success(request, f'Успешно добавлено {added_count} товаров в перевозку #{shipment.shipment_number}')
            else:
                messages.info(request, 'Товары уже были добавлены в перевозку ранее')
        
        elif action == 'remove' and item_ids:
            # Удаляем выбранные товары из перевозки
            removed_count = 0
            for item_id in item_ids:
                item = Item.objects.get(pk=item_id)
                if item in selected_items:
                    shipment.items.remove(item)
                    item.update_status('at_warehouse', warehouse)
                    removed_count += 1
            
            if removed_count > 0:
                messages.success(request, f'Успешно удалено {removed_count} товаров из перевозки #{shipment.shipment_number}')
            else:
                messages.info(request, 'Нет товаров для удаления из перевозки')
        
        return redirect('add_items_to_shipment_enhanced', shipment_id=shipment.id)
    
    # Заказы, связанные с доступными товарами
    available_orders = Order.objects.filter(
        items__in=available_items
    ).distinct()
    
    # Список возможных статусов товаров для фильтрации
    status_choices = [('created', 'Создан'), ('at_warehouse', 'На складе')]
    
    context = {
        'shipment': shipment,
        'available_items': available_items,
        'selected_items': selected_items,
        'selected_item_ids': selected_item_ids,
        'available_orders': available_orders,
        'order_filter': order_filter,
        'description_filter': description_filter,
        'status_filter': status_filter,
        'status_choices': status_choices,
        'warehouse': warehouse
    }
    return render(request, 'logistics/shipments/add_items_enhanced.html', context)
