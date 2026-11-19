from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Meal(models.Model):

    DIET_CHOICES = [
        ("veg", "Vegetarian"),
        ("non_veg", "Non-Vegetarian"),
        ("high_protein", "High Protein"),
    ]

    CATEGORY_CHOICES = [
        ("breakfast", "Breakfast"),
        ("lunch", "Lunch"),
        ("evening_snacks", "Evening Snacks"),
        ("beverages", "Shakes & Beverages"),
        ("dinner", "Dinner"),
    ]

    name = models.CharField(max_length=120)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="lunch"
    )

    diet_type = models.CharField(
        max_length=20,
        choices=DIET_CHOICES
    )

    # Nutrition information
    calories = models.IntegerField(
        null=True,
        blank=True
    )

    protein = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    carbohydrates = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    fats = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    fiber = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    sugar = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )

    serving_size = models.CharField(
        max_length=50,
        blank=True
    )

    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="meals/",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.get_diet_type_display()})"

class WeeklyMenu(models.Model):

    week_start = models.DateField(
        help_text="Enter the Monday date for this menu"
    )

    def __str__(self):
        return f"Weekly Menu starting {self.week_start}"

class MenuItem(models.Model):

    DAY_CHOICES = [
        (0, "Mon"),
        (1, "Tue"),
        (2, "Wed"),
        (3, "Thu"),
        (4, "Fri"),
        (5, "Sat"),
        (6, "Sun"),
    ]

    menu = models.ForeignKey(
        WeeklyMenu,
        on_delete=models.CASCADE,
        related_name="items"
    )

    meal = models.ForeignKey(
        Meal,
        on_delete=models.CASCADE
    )

    day_of_week = models.IntegerField(
        choices=DAY_CHOICES
    )

    class Meta:
        unique_together = ("menu", "day_of_week", "meal")

    def __str__(self):
        return (
            f"{self.menu.week_start} - "
            f"{self.get_day_of_week_display()} : {self.meal.name}"
        )

class Subscription(models.Model):

    SUBSCRIPTION_DIET_CHOICES = [
        ("veg", "Vegetarian"),
        ("non_veg", "Non-Vegetarian"),
        ("high_protein", "High Protein"),
        ("mixed", "Mixed Diet"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    diet_preference = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_DIET_CHOICES
    )

    selected_days = models.CharField(
        max_length=50,
        help_text="Comma-separated days as 0=Mon..6=Sun"
    )

    active = models.BooleanField(default=True)
    paused = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    cancelled_at = models.DateTimeField(null=True,blank=True)

    def selected_days_list(self):

        if not self.selected_days:
            return []

        return [
            int(x)
            for x in self.selected_days.split(",")
            if x.strip().isdigit()
        ]

    def __str__(self):
        return (
            f"Subscription({self.user.username}) - "
            f"{self.get_diet_preference_display()}"
        )

class Order(models.Model):

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    meal = models.ForeignKey(
        Meal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    meal_name = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    date = models.DateField()

    STATUS = [
        ("pending", "Pending"),
        ("delivered", "Delivered"),
        ("cancelled", "Skipped"),
        ("paused", "Paused"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.meal:
            self.meal_name = self.meal.name

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.date} - {self.meal_name}"