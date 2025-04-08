from django.db import models
from django.utils import timezone
from django.db.models import Count, F, ExpressionWrapper, fields
from django.core.exceptions import ValidationError
from datetime import timedelta


class Seller(models.Model):
    """
    Модель продавца, который отправляет товары.
    """

    name = models.CharField("Название", max_length=100)
    contact = models.CharField(
        "Контактная информация", max_length=200, blank=True, null=True
    )

    def __str__(self):
        return self.name

    def get_pending_orders_count(self):
        """Получение количества активных заказов продавца"""
        return self.order_set.filter(status="pending").count()

    def get_total_orders_count(self):
        """Получение общего количества заказов продавца"""
        return self.order_set.count()

    class Meta:
        verbose_name = "Продавец"
        verbose_name_plural = "Продавцы"


class Location(models.Model):
    """
    Модель локации (склада или ПВЗ)
    """

    LOCATION_TYPE = (
        ("warehouse", "Склад"),
        ("pickup", "ПВЗ"),
    )

    name = models.CharField("Название", max_length=100)
    location_type = models.CharField(
        "Тип локации", max_length=20, choices=LOCATION_TYPE
    )
    address = models.CharField("Адрес", max_length=200)

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"

    def get_incoming_shipments(self):
        """Получение всех входящих перевозок"""
        return self.arriving_shipments.filter(arrival_time__isnull=True)

    def get_outgoing_shipments(self):
        """Получение всех исходящих перевозок"""
        return self.departing_shipments.filter(arrival_time__isnull=True)

    def get_items_at_location(self):
        """Получение всех товаров на этой локации"""
        return Item.objects.filter(current_location=self)

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"


class Order(models.Model):
    """
    Модель заказа
    """

    STATUS_CHOICES = (
        ("pending", "Ожидает отправки"),
        ("in_transit", "В пути"),
        ("delivered", "Доставлен"),
        ("returned", "Возврат"),
    )

    seller = models.ForeignKey(
        Seller, on_delete=models.CASCADE, verbose_name="Продавец"
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    destination = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="destination_orders",
        verbose_name="Пункт назначения",
    )

    def __str__(self):
        return f"Заказ #{self.id} от {self.seller.name}"

    def update_status(self):
        """
        Обновляет статус заказа на основе статусов товаров
        """
        items = self.items.all()

        if not items:
            self.status = "pending"
            self.save()
            return

        # Если все товары доставлены
        if all(item.status == "delivered" for item in items):
            self.status = "delivered"
        # Если все товары возвращены
        elif all(item.status == "returned" for item in items):
            self.status = "returned"
        # Если хотя бы один товар в пути
        elif any(item.status == "in_transit" for item in items):
            self.status = "in_transit"
        # Иначе заказ ожидает отправки
        else:
            self.status = "pending"

        self.save()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class Item(models.Model):
    """
    Модель товара в заказе
    """

    STATUS_CHOICES = (
        ("created", "Создан"),
        ("at_warehouse", "На складе"),
        ("in_transit", "В перевозке"),
        ("delivered", "Доставлен"),
        ("returned", "Возвращен"),
        ("lost", "Утерян"),
    )

    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE, verbose_name="Заказ"
    )
    description = models.CharField("Описание", max_length=200)
    quantity = models.PositiveIntegerField("Количество", default=1)
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="created"
    )
    current_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="Текущая локация",
    )

    def __str__(self):
        return f"{self.description} (x{self.quantity}) - {self.get_status_display()}"

    def update_status(self, new_status, location=None):
        """
        Обновляет статус товара и его местоположение
        """
        self.status = new_status

        if location:
            self.current_location = location
        elif new_status == 'in_transit':
            pass
        elif new_status == 'lost':
            pass

        self.save()

        # Обновить статус заказа
        self.order.update_status()

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Shipment(models.Model):
    """
    Модель перевозки товаров между локациями
    """

    STATUS_CHOICES = (
        ("created", "Создана"),
        ("loading", "Загрузка"),
        ("in_transit", "В пути"),
        ("arrived", "Прибыла"),
        ("unloading", "Разгрузка"),
        ("unloaded", "Разгружена"),
        ("completed", "Завершена"),
        ("cancelled", "Отменена"),
    )

    shipment_number = models.CharField("Номер перевозки", max_length=50, unique=True)
    vehicle_info = models.CharField(
        "Информация о транспорте", max_length=100, blank=True, null=True
    )
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="created"
    )
    departure_time = models.DateTimeField("Время отправления", blank=True, null=True)
    estimated_arrival_time = models.DateTimeField(
        "Расчетное время прибытия", blank=True, null=True
    )
    arrival_time = models.DateTimeField(
        "Фактическое время прибытия", blank=True, null=True
    )
    from_location = models.ForeignKey(
        Location,
        related_name="departing_shipments",
        on_delete=models.CASCADE,
        verbose_name="Откуда",
    )
    to_location = models.ForeignKey(
        Location,
        related_name="arriving_shipments",
        on_delete=models.CASCADE,
        verbose_name="Куда",
    )
    items = models.ManyToManyField(
        Item, related_name="shipments", verbose_name="Товары", blank=True
    )

    def __str__(self):
        return f"Перевозка #{self.shipment_number}: {self.from_location.name} → {self.to_location.name}"

    def mark_as_in_transit(self):
        """
        Отмечает перевозку как отправленную в путь, устанавливает время отправления
        и рассчитывает ожидаемое время прибытия на основе активного маршрута.
        """
        if self.status in ["loading", "created"]: # Allow starting transit from created or loading
            self.status = "in_transit"
            self.departure_time = timezone.now()

            # Calculate estimated arrival time based on route
            try:
                route = Route.objects.get(
                    from_location=self.from_location,
                    to_location=self.to_location,
                    active=True,
                )
                if route.travel_time:
                    self.estimated_arrival_time = self.departure_time + route.travel_time
                else:
                    self.estimated_arrival_time = None # No travel time defined
            except Route.DoesNotExist:
                self.estimated_arrival_time = None # No active route found

            self.save()

            # Update item statuses
            for item in self.items.all():
                item.update_status("in_transit", location=item.current_location) # Keep current location until arrival
            return True
        return False

    def mark_as_arrived(self):
        """
        Отмечает перевозку как прибывшую, устанавливает фактическое время прибытия.
        """
        if self.status == "in_transit":
            self.status = "arrived"
            self.arrival_time = timezone.now()
            self.save()
            return True
        return False

    def start_unloading(self):
        """Marks the shipment as being unloaded."""
        if self.status == "arrived":
            self.status = "unloading"
            self.save()
            return True
        return False

    def process_unloaded_item(self, item, status):
        """
        Processes a single item during unloading.
        Updates item status and location.
        """
        if self.status == "unloading" and item in self.items.all():
            if status == "at_warehouse":
                item.update_status("at_warehouse", location=self.to_location)
            elif status == "lost":
                item.update_status("lost", location=self.to_location)
            else:
                return False
            return True
        return False

    def check_and_finish_unloading(self):
        """Checks if all items are processed (at_warehouse or lost) and marks shipment as unloaded."""
        if self.status == "unloading":
            processed_items_count = self.items.filter(
                Q(status='at_warehouse', current_location=self.to_location) | Q(status='lost')
            ).count()

            if processed_items_count == self.items.count():
                self.status = "unloaded"
                self.save()
                return True
        return False


    def complete_shipment(self):
        """
        Завершает перевозку после подтверждения разгрузки всех товаров.
        """
        if self.status == "unloaded":
            self.status = "completed"
            self.save()
            return True
        return False

    def cancel_shipment(self):
        """Cancels the shipment and attempts to return items."""
        if self.status not in ['completed', 'cancelled']:
            previous_status = self.status
            self.status = 'cancelled'
            self.save()
            for item in self.items.all():
                if item.status == 'in_transit' or previous_status in ['loading', 'created']:
                    item.update_status('at_warehouse', location=self.from_location)
            return True
        return False


    class Meta:
        verbose_name = "Перевозка"
        verbose_name_plural = "Перевозки"


class Route(models.Model):
    """
    Модель маршрута между двумя локациями
    """

    from_location = models.ForeignKey(
        Location,
        related_name="routes_from",
        on_delete=models.CASCADE,
        verbose_name="Откуда",
    )
    to_location = models.ForeignKey(
        Location,
        related_name="routes_to",
        on_delete=models.CASCADE,
        verbose_name="Куда",
    )
    travel_time = models.DurationField("Время в пути", help_text="Пример: 1 02:30:00 = 1 день, 2 часа, 30 минут")
    active = models.BooleanField("Активен", default=True)

    def __str__(self):
        return f"Маршрут: {self.from_location.name} → {self.to_location.name}"

    def clean(self):
        """Валидация маршрута"""
        if self.from_location == self.to_location:
            raise ValidationError(
                "Начальная и конечная локации не могут быть одинаковыми"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"
        unique_together = ["from_location", "to_location"]
