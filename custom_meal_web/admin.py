
from django.contrib import admin
from django.utils.html import format_html

from .models import Meal, WeeklyMenu, MenuItem, Subscription, Order


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
        "diet_type",
        "calories",
        "protein",
        "carbohydrates",
        "fats",
        "image_preview",
    )

    list_filter = (
        "category",
        "diet_type",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "image_preview",
    )

    fields = (
        "name",
        "category",
        "diet_type",
        "description",
        "image",
        "image_preview",
        "serving_size",
        "calories",
        "protein",
        "carbohydrates",
        "fats",
        "fiber",
        "sugar",
    )

    ordering = ("category", "name")

    list_per_page = 25

    def image_preview(self, obj):

        if obj and obj.image:
            return format_html(
                '<img src="{}" width="100" height="70" '
                'style="object-fit:cover; border-radius:8px;" />',
                obj.image.url
            )

        return "No Image"

    image_preview.short_description = "Dish Preview"


class MenuItemInline(admin.TabularInline):

    model = MenuItem
    extra = 1

    autocomplete_fields = ["meal"]

    fields = (
        "day_of_week",
        "meal",
        "meal_category",
    )

    readonly_fields = (
        "meal_category",
    )

    def meal_category(self, obj):

        if obj and obj.meal:
            return obj.meal.get_category_display()

        return "-"

    meal_category.short_description = "Meal Category"


@admin.register(WeeklyMenu)
class WeeklyMenuAdmin(admin.ModelAdmin):

    list_display = (
        "week_start",
    )

    ordering = (
        "-week_start",
    )

    inlines = [
        MenuItemInline,
    ]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "diet_preference",
        "active",
        "paused",
        "paid",
        "created_at",
        "cancelled_at",
    )
    
    list_filter = (
        "diet_preference",
        "active",
        "paused",
        "paid",
    )

    search_fields = (
        "user__username",
        "user__email",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "subscription",
        "meal",
        "date",
        "status",
    )

    list_filter = (
        "status",
        "date",
    )

    search_fields = (
        "subscription__user__username",
        "meal__name",
    )

    ordering = (
        "-date",
    )
