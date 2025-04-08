from django import forms
from django.core.exceptions import ValidationError
from .models import Route, Seller, Location, Order, Item, Shipment
from datetime import timedelta
import shortuuid


class RouteForm(forms.ModelForm):
    """Форма для создания и редактирования маршрутов"""

    class Meta:
        model = Route
        fields = ["from_location", "to_location", "travel_time", "active"]
        widgets = {
            "from_location": forms.Select(attrs={"class": "form-select"}),
            "to_location": forms.Select(attrs={"class": "form-select"}),
            "travel_time": forms.TextInput(attrs={"class": "form-control", "placeholder": "ДД ЧЧ:ММ:СС"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_location = cleaned_data.get("from_location")
        to_location = cleaned_data.get("to_location")

        if from_location and to_location and from_location == to_location:
            raise ValidationError(
                "Начальный и конечный пункты маршрута должны быть разными"
            )

        return cleaned_data


class SellerForm(forms.ModelForm):
    """Форма для создания и редактирования продавцов"""

    class Meta:
        model = Seller
        fields = ["name", "contact"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "contact": forms.TextInput(attrs={"class": "form-control"}),
        }


class LocationForm(forms.ModelForm):
    """Форма для создания и редактирования локаций"""

    class Meta:
        model = Location
        fields = ["name", "location_type", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "location_type": forms.Select(attrs={"class": "form-select"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }


class OrderForm(forms.ModelForm):
    """Форма для создания заказов"""

    class Meta:
        model = Order
        fields = ["seller", "status", "destination"]
        widgets = {
            "seller": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "destination": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination"].queryset = Location.objects.filter(
            location_type="pickup"
        )


class ItemForm(forms.ModelForm):
    """Форма для создания товаров в заказе"""

    class Meta:
        model = Item
        fields = ["description", "quantity", "status", "current_location"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "current_location": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["current_location"].queryset = Location.objects.filter(
            location_type="warehouse"
        )


class ShipmentForm(forms.ModelForm):
    """Форма для создания отправления вручную"""

    # Generate a default shipment number
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('shipment_number'):
            self.initial['shipment_number'] = f"SHP-{shortuuid.ShortUUID().random(length=8).upper()}"

    class Meta:
        model = Shipment
        fields = [
            "shipment_number",
            "vehicle_info",
            "from_location",
            "to_location",
        ]
        widgets = {
            "shipment_number": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "vehicle_info": forms.TextInput(attrs={"class": "form-control"}),
            "from_location": forms.Select(attrs={"class": "form-select"}),
            "to_location": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_location = cleaned_data.get("from_location")
        to_location = cleaned_data.get("to_location")

        if from_location and to_location and from_location == to_location:
            raise ValidationError(
                "Начальный и конечный пункты доставки должны быть разными"
            )

        # Проверка существования маршрута
        if from_location and to_location:
            if not Route.objects.filter(
                from_location=from_location, to_location=to_location, active=True
            ).exists():
                raise ValidationError("Между указанными точками нет активного маршрута")

        return cleaned_data


class ItemSelectionForm(forms.Form):
    """Форма для выбора товаров, которые нужно добавить в отправление"""

    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.filter(status__in=["created", "at_warehouse"]),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=True,
    )

    def __init__(self, *args, location=None, **kwargs):
        super().__init__(*args, **kwargs)
        if location:
            self.fields["items"].queryset = Item.objects.filter(
                current_location=location, status__in=["created", "at_warehouse"]
            )
