from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Subscription, Meal


class SubscriptionForm(forms.ModelForm):

    DAY_CHOICES = [
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    ]

    diet_preference = forms.ChoiceField(
        choices=Subscription.SUBSCRIPTION_DIET_CHOICES,
        widget=forms.RadioSelect(
            attrs={"class": "diet-radio"}
        )
    )

    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
        error_messages={
            "required": "Please select a subscription start date."
        }
    )

    duration_weeks = forms.TypedChoiceField(
        choices=Subscription.DURATION_CHOICES,
        coerce=int,
        widget=forms.Select(
            attrs={"class": "form-control"}
        )
    )

    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "day-checkbox"}
        ),
        error_messages={
            "required": "Please select at least one delivery day."
        }
    )

    class Meta:
        model = Subscription
        fields = [
            "diet_preference",
            "start_date",
            "duration_weeks",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.is_edit = bool(
            self.instance and self.instance.pk
        )

        today = timezone.localdate()

        # Prevent new subscriptions from starting in the past.
        # Existing subscriptions can retain their original start date.
        if (
            not self.is_edit
            or not self.instance.start_date
            or self.instance.start_date >= today
        ):
            self.fields["start_date"].widget.attrs["min"] = (
                today.isoformat()
            )

        # Load existing subscription details.
        if self.is_edit:

            self.fields["days"].initial = (
                self.instance.selected_days_list()
            )

            self.fields["start_date"].initial = (
                self.instance.start_date
            )

            self.fields["duration_weeks"].initial = (
                self.instance.duration_weeks
            )

        # Load all available meals.
        self.meal_options = []

        meals = Meal.objects.all().order_by(
            "category",
            "name"
        )

        for meal in meals:

            self.meal_options.append({
                "id": meal.id,
                "name": meal.name,

                # Category information
                "category": meal.get_category_display(),
                "category_value": meal.category,

                # Diet information
                "diet": meal.diet_type,
                "diet_display": meal.get_diet_type_display(),

                # Nutrition and image information
                "image": meal.image,
                "calories": meal.calories,
                "protein": meal.protein,
            })

        # Load existing future meal selections while editing.
        self.selected_meals_initial = []

        if self.is_edit:

            existing_orders = self.instance.orders.filter(
                status__in=["pending", "paused"],
                date__gte=today
            ).select_related("meal")

            for order in existing_orders:

                if order.meal_id:

                    self.selected_meals_initial.append({
                        "date": order.date.isoformat(),
                        "meal_id": order.meal_id,
                    })

    def clean(self):

        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        duration = cleaned_data.get("duration_weeks")
        selected_days = cleaned_data.get("days", [])
        diet_preference = cleaned_data.get("diet_preference")

        selected_meals = {}

        if not start_date or not duration:
            return cleaned_data

        today = timezone.localdate()

        # New subscriptions cannot start in the past.
        # Existing subscriptions can retain their original start date.
        if start_date < today:

            original_start_date = (
                self.instance.start_date
                if self.is_edit
                else None
            )

            if start_date != original_start_date:

                self.add_error(
                    "start_date",
                    "Subscription start date cannot be in the past."
                )

        if not selected_days:
            cleaned_data["selected_meals"] = selected_meals
            return cleaned_data

        try:
            selected_weekdays = {
                int(day) for day in selected_days
            }

        except (TypeError, ValueError):

            self.add_error(
                "days",
                "Invalid delivery day selected."
            )

            cleaned_data["selected_meals"] = selected_meals
            return cleaned_data

        # Calculate subscription date range.
        end_date = (
            start_date
            + timedelta(weeks=duration)
            - timedelta(days=1)
        )

        current_date = start_date

        while current_date <= end_date:

            if current_date.weekday() in selected_weekdays:

                # Past dates cannot be modified.
                if current_date < today:
                    current_date += timedelta(days=1)
                    continue

                date_key = current_date.isoformat()

                meal_ids = self.data.getlist(
                    f"meal_{date_key}"
                )

                if not meal_ids:

                    self.add_error(
                        "days",
                        f"Please select at least one meal for "
                        f"{current_date.strftime('%d %b %Y')}."
                    )

                    current_date += timedelta(days=1)
                    continue

                selected_meals[date_key] = []

                for meal_id in meal_ids:

                    try:
                        meal_id = int(meal_id)

                    except (TypeError, ValueError):

                        self.add_error(
                            "days",
                            "Invalid meal selection."
                        )

                        continue

                    meal = Meal.objects.filter(
                        id=meal_id
                    ).first()

                    if not meal:

                        self.add_error(
                            "days",
                            "Selected meal does not exist."
                        )

                        continue

                    # Backend diet validation.
                    if (
                        diet_preference != "mixed"
                        and meal.diet_type != diet_preference
                    ):

                        self.add_error(
                            "diet_preference",
                            f"{meal.name} does not match your "
                            f"selected diet preference."
                        )

                        continue

                    # Avoid duplicate meal IDs for the same date.
                    if meal_id not in selected_meals[date_key]:

                        selected_meals[date_key].append(
                            meal_id
                        )

            current_date += timedelta(days=1)

        cleaned_data["selected_meals"] = selected_meals

        return cleaned_data

    def save(self, user=None, commit=True):

        instance = super().save(commit=False)

        instance.selected_days = ",".join(
            self.cleaned_data.get("days", [])
        )

        if user:
            instance.user = user

        if commit:
            instance.save()

        return instance
