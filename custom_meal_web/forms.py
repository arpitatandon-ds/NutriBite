
from datetime import timedelta

from django import forms

from .models import (
    Subscription,
    WeeklyMenu,
    MenuItem,
    Meal,
)


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
        fields = ["diet_preference"]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.menu = WeeklyMenu.objects.order_by(
            "-week_start"
        ).first()

        # Restore selected delivery days
        if self.instance and self.instance.pk:
            self.fields["days"].initial = [
                str(day)
                for day in self.instance.selected_days_list()
            ]

        # Get selected meals from existing subscription
        selected_by_day = {}

        if self.instance and self.instance.pk and self.menu:

            week_end = self.menu.week_start + timedelta(days=6)

            existing_orders = self.instance.orders.filter(
                status__in=["pending", "paused"],
                date__gte=self.menu.week_start,
                date__lte=week_end
            ).select_related("meal")

            for order in existing_orders:

                if not order.meal_id:
                    continue

                day = (
                    order.date - self.menu.week_start
                ).days

                if 0 <= day <= 6:

                    selected_by_day.setdefault(
                        day, []
                    ).append(str(order.meal_id))

        # Prepare meal options for template
        self.meal_options = []

        if self.menu:

            items = MenuItem.objects.filter(
                menu=self.menu
            ).select_related(
                "meal"
            ).order_by(
                "day_of_week",
                "meal__category",
                "meal__name"
            )

            for item in items:

                day = item.day_of_week

                self.meal_options.append({
                    "id": item.meal_id,
                    "name": item.meal.name,
                    "day": day,
                    "day_name": dict(self.DAY_CHOICES).get(
                        str(day), ""
                    ),
                    "category": item.meal.get_category_display(),
                    "diet": item.meal.diet_type,
                    "image": item.meal.image,
                    "selected": str(item.meal_id) in
                        selected_by_day.get(day, []),
                })

        # Keep selected meals available to the template
        self.selected_meals_initial = [
            {
                "day": day,
                "meal_id": meal_id
            }
            for day, meal_ids in selected_by_day.items()
            for meal_id in meal_ids
        ]
    def clean(self):

        cleaned_data = super().clean()

        selected_days = cleaned_data.get("days", [])

        selected_meals = {}
        selected_diets = set()

        if not self.menu:

            self.add_error(
                "days",
                "No weekly menu is available. Please contact the administrator."
            )

            return cleaned_data

        for day in selected_days:

            day_name = dict(self.DAY_CHOICES).get(day, day)
            day_number = int(day)

            meal_ids = self.data.getlist(
                f"meal_{day}"
            )

            if not meal_ids:

                self.add_error(
                    "days",
                    f"Please select at least one meal for {day_name}."
                )

                continue

            selected_meals[day_number] = []

            for meal_id in meal_ids:

                try:
                    meal_id = int(meal_id)

                except (TypeError, ValueError):

                    self.add_error(
                        "days",
                        "Invalid meal selection."
                    )

                    continue

                valid_item = MenuItem.objects.filter(
                    menu=self.menu,
                    day_of_week=day_number,
                    meal_id=meal_id
                ).select_related("meal").first()

                if not valid_item:

                    self.add_error(
                        "days",
                        f"Invalid meal selected for {day_name}."
                    )

                    continue

                if meal_id not in selected_meals[day_number]:

                    selected_meals[day_number].append(
                        meal_id
                    )

                selected_diets.add(
                    valid_item.meal.diet_type
                )

            if not selected_meals[day_number]:
                del selected_meals[day_number]

        # Automatically determine diet preference
        if len(selected_diets) == 1:

            final_diet = next(iter(selected_diets))

        elif len(selected_diets) > 1:

            final_diet = "mixed"

        else:

            final_diet = cleaned_data.get(
                "diet_preference"
            )

        cleaned_data["diet_preference"] = final_diet
        cleaned_data["selected_meals"] = selected_meals

        return cleaned_data

    def save(self, user=None, commit=True):

        instance = super().save(commit=False)

        instance.selected_days = ",".join(
            self.cleaned_data.get("days", [])
        )

        instance.diet_preference = self.cleaned_data.get(
            "diet_preference"
        )

        if user:
            instance.user = user

        if commit:
            instance.save()

        return instance
