# Generated by Django 5.2 on 2025-04-08 13:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logistics", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="item",
            options={"verbose_name": "Товар", "verbose_name_plural": "Товары"},
        ),
        migrations.AlterModelOptions(
            name="location",
            options={"verbose_name": "Локация", "verbose_name_plural": "Локации"},
        ),
        migrations.AlterModelOptions(
            name="order",
            options={"verbose_name": "Заказ", "verbose_name_plural": "Заказы"},
        ),
        migrations.AlterModelOptions(
            name="route",
            options={"verbose_name": "Маршрут", "verbose_name_plural": "Маршруты"},
        ),
        migrations.AlterModelOptions(
            name="seller",
            options={"verbose_name": "Продавец", "verbose_name_plural": "Продавцы"},
        ),
        migrations.AlterModelOptions(
            name="shipment",
            options={"verbose_name": "Перевозка", "verbose_name_plural": "Перевозки"},
        ),
        migrations.AlterField(
            model_name="item",
            name="current_location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="items",
                to="logistics.location",
                verbose_name="Текущая локация",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="description",
            field=models.CharField(max_length=200, verbose_name="Описание"),
        ),
        migrations.AlterField(
            model_name="item",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="logistics.order",
                verbose_name="Заказ",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="quantity",
            field=models.PositiveIntegerField(default=1, verbose_name="Количество"),
        ),
        migrations.AlterField(
            model_name="item",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Создан"),
                    ("at_warehouse", "На складе"),
                    ("in_transit", "В перевозке"),
                    ("delivered", "Доставлен"),
                    ("returned", "Возвращен"),
                ],
                default="created",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="address",
            field=models.CharField(max_length=200, verbose_name="Адрес"),
        ),
        migrations.AlterField(
            model_name="location",
            name="latitude",
            field=models.FloatField(blank=True, null=True, verbose_name="Широта"),
        ),
        migrations.AlterField(
            model_name="location",
            name="location_type",
            field=models.CharField(
                choices=[("warehouse", "Склад"), ("pickup", "ПВЗ")],
                max_length=20,
                verbose_name="Тип локации",
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="longitude",
            field=models.FloatField(blank=True, null=True, verbose_name="Долгота"),
        ),
        migrations.AlterField(
            model_name="location",
            name="name",
            field=models.CharField(max_length=100, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="order",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Дата создания"),
        ),
        migrations.AlterField(
            model_name="order",
            name="destination",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="destination_orders",
                to="logistics.location",
                verbose_name="Пункт назначения",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="seller",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="logistics.seller",
                verbose_name="Продавец",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Ожидает отправки"),
                    ("in_transit", "В пути"),
                    ("delivered", "Доставлен"),
                    ("returned", "Возврат"),
                ],
                default="pending",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
        migrations.AlterField(
            model_name="route",
            name="active",
            field=models.BooleanField(default=True, verbose_name="Активен"),
        ),
        migrations.AlterField(
            model_name="route",
            name="cost",
            field=models.DecimalField(
                decimal_places=2, max_digits=10, verbose_name="Стоимость"
            ),
        ),
        migrations.AlterField(
            model_name="route",
            name="from_location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="routes_from",
                to="logistics.location",
                verbose_name="Откуда",
            ),
        ),
        migrations.AlterField(
            model_name="route",
            name="to_location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="routes_to",
                to="logistics.location",
                verbose_name="Куда",
            ),
        ),
        migrations.AlterField(
            model_name="route",
            name="travel_time",
            field=models.DurationField(verbose_name="Время в пути"),
        ),
        migrations.AlterField(
            model_name="seller",
            name="contact",
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name="Контактная информация",
            ),
        ),
        migrations.AlterField(
            model_name="seller",
            name="name",
            field=models.CharField(max_length=100, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="arrival_time",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Время прибытия"
            ),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="departure_time",
            field=models.DateTimeField(verbose_name="Время отправления"),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="from_location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="departing_shipments",
                to="logistics.location",
                verbose_name="Откуда",
            ),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="items",
            field=models.ManyToManyField(
                related_name="shipments", to="logistics.item", verbose_name="Товары"
            ),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="shipment_number",
            field=models.CharField(
                max_length=50, unique=True, verbose_name="Номер перевозки"
            ),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="to_location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="arriving_shipments",
                to="logistics.location",
                verbose_name="Куда",
            ),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="vehicle_info",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Информация о транспорте",
            ),
        ),
    ]
