
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import Http404, JsonResponse

from .models import WeeklyMenu, Meal, Subscription, MenuItem, Order
from .forms import SubscriptionForm


# ==========================================
# CURRENT SUBSCRIPTION HELPER
# ==========================================

def get_current_subscription(user):

    subscription = Subscription.objects.filter(
        user=user,
        active=True
    ).order_by("-created_at").first()

    if not subscription:
        raise Http404("No active subscription found.")

    return subscription


# ==========================================
# HOME
# ==========================================

def home(request):
    return render(request, "main/home.html")


# ==========================================
# MENU
# ==========================================

def menu_view(request):

    all_menus = WeeklyMenu.objects.order_by("-week_start")

    selected_week = request.GET.get("week")

    menu = all_menus.first()

    if selected_week:
        menu = all_menus.filter(id=selected_week).first() or menu

    menu_items = MenuItem.objects.none()

    if menu:
        menu_items = menu.items.select_related(
            "meal"
        ).order_by(
            "day_of_week",
            "meal__category",
            "meal__name"
        )

    diet = request.GET.get("diet")

    if diet:
        menu_items = menu_items.filter(
            meal__diet_type=diet
        )

    return render(request, "main/menu.html", {
        "menu": menu,
        "menus": all_menus,
        "menu_items": menu_items,
        "diet": diet,
    })


# ==========================================
# REGISTER
# ==========================================

def register(request):

    if request.method == "POST":

        form = UserCreationForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Account created — please log in."
            )

            return redirect("login")

    else:

        form = UserCreationForm()

    return render(
        request,
        "main/register.html",
        {"form": form}
    )


# ==========================================
# CREATE SUBSCRIPTION
# ==========================================

@login_required
def subscribe(request):

    if Subscription.objects.filter(
        user=request.user,
        active=True
    ).exists():

        messages.info(
            request,
            "You already have a subscription. Edit it from My Subscription."
        )

        return redirect("edit_subscription")

    if request.method == "POST":

        form = SubscriptionForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                subscription = form.save(
                    user=request.user
                )

                menu = form.menu

                selected_meals = form.cleaned_data.get(
                    "selected_meals", {}
                )

                for day, meal_ids in selected_meals.items():

                    day = int(day)

                    order_date = (
                        menu.week_start + timedelta(days=day)
                    )

                    for meal_id in meal_ids:

                        item = MenuItem.objects.filter(
                            menu=menu,
                            day_of_week=day,
                            meal_id=meal_id
                        ).select_related(
                            "meal"
                        ).first()

                        if item:

                            Order.objects.create(
                                subscription=subscription,
                                meal=item.meal,
                                date=order_date
                            )

            messages.success(
                request,
                "Subscription created successfully!"
            )

            return redirect("my_subscription")

    else:

        form = SubscriptionForm()

    meals = Meal.objects.all().order_by(
        "diet_type",
        "name"
    )

    return render(
        request,
        "main/subscribe.html",
        {
            "form": form,
            "meals": meals
        }
    )


# ==========================================
# EDIT SUBSCRIPTION
# ==========================================

@login_required
def edit_subscription(request):

    try:

        subscription = get_current_subscription(
            request.user
        )

    except Http404:

        messages.error(
            request,
            "No active subscription found."
        )

        return redirect("my_subscription")

    if request.method == "POST":

        form = SubscriptionForm(
            request.POST,
            instance=subscription
        )

        if form.is_valid():

            with transaction.atomic():

                updated_subscription = form.save()

                menu = form.menu

                if menu:

                    today = timezone.localdate()

                    selected_meals = form.cleaned_data.get(
                        "selected_meals", {}
                    )

                    # Selected day + meal combinations
                    selected_pairs = set()

                    for day, meal_ids in selected_meals.items():

                        day = int(day)

                        for meal_id in meal_ids:

                            selected_pairs.add(
                                (day, int(meal_id))
                            )

                    week_end = (
                        menu.week_start + timedelta(days=6)
                    )

                    # Cancel removed pending/paused orders
                    existing_orders = updated_subscription.orders.filter(
                        date__gte=max(today, menu.week_start),
                        date__lte=week_end,
                        status__in=["pending", "paused"]
                    ).select_related(
                        "meal"
                    )

                    for order in existing_orders:

                        day = (
                            order.date - menu.week_start
                        ).days

                        if order.meal_id and (
                            day,
                            order.meal_id
                        ) not in selected_pairs:

                            order.status = "cancelled"

                            order.save(
                                update_fields=["status"]
                            )

                    # Add or reactivate selected meals
                    if updated_subscription.active:

                        desired_status = (
                            "paused"
                            if updated_subscription.paused
                            else "pending"
                        )

                        for day, meal_id in selected_pairs:

                            order_date = (
                                menu.week_start + timedelta(days=day)
                            )

                            if order_date < today:
                                continue

                            item = MenuItem.objects.filter(
                                menu=menu,
                                day_of_week=day,
                                meal_id=meal_id
                            ).select_related(
                                "meal"
                            ).first()

                            if not item:
                                continue

                            existing_order = (
                                updated_subscription.orders.filter(
                                    date=order_date,
                                    meal_id=meal_id
                                ).order_by("-created_at").first()
                            )

                            if existing_order:

                                if existing_order.status in [
                                    "cancelled",
                                    "pending",
                                    "paused"
                                ]:

                                    if existing_order.status != desired_status:

                                        existing_order.status = desired_status

                                        existing_order.save(
                                            update_fields=["status"]
                                        )

                            else:

                                Order.objects.create(
                                    subscription=updated_subscription,
                                    meal=item.meal,
                                    date=order_date,
                                    status=desired_status
                                )

            messages.success(
                request,
                "Your subscription has been updated successfully!"
            )

            return redirect("my_subscription")

    else:

        form = SubscriptionForm(
            instance=subscription
        )

    return render(
        request,
        "main/edit_subscription.html",
        {
            "form": form,
            "sub": subscription
        }
    )


# ==========================================
# MY SUBSCRIPTION
# ==========================================

@login_required
def my_subscription(request):

    subscription = Subscription.objects.filter(
        user=request.user,
        active=True
    ).order_by("-created_at").first()

    orders = []

    if subscription:

        orders = subscription.orders.select_related(
            "meal"
        ).order_by("date")

    return render(
        request,
        "main/my_subscription.html",
        {
            "sub": subscription,
            "orders": orders,
            "today": timezone.localdate(),
        }
    )


# ==========================================
# SUBSCRIPTION HISTORY
# ==========================================

@login_required
def subscription_history(request):

    subscriptions = Subscription.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "main/subscription_history.html",
        {
            "subscriptions": subscriptions,
        }
    )


# ==========================================
# DELETE SUBSCRIPTION HISTORY
# ==========================================

@login_required
def delete_subscription_history(request, subscription_id):

    if request.method != "POST":
        return redirect("subscription_history")

    subscription = get_object_or_404(
        Subscription,
        id=subscription_id,
        user=request.user,
        active=False
    )

    subscription.delete()

    messages.success(
        request,
        "Subscription history deleted successfully!"
    )

    return redirect("subscription_history")


# ==========================================
# PAUSE / RESUME SUBSCRIPTION - AJAX
# ==========================================

@login_required
def toggle_subscription_pause(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request."
            },
            status=405
        )

    try:

        subscription = get_current_subscription(
            request.user
        )

    except Http404:

        return JsonResponse(
            {
                "success": False,
                "message": "No active subscription found."
            },
            status=404
        )

    subscription.paused = not subscription.paused

    subscription.save(
        update_fields=["paused"]
    )

    future_orders = Order.objects.filter(
        subscription=subscription,
        date__gte=timezone.localdate(),
        status__in=["pending", "paused"]
    )

    if subscription.paused:

        future_orders.update(
            status="paused"
        )

    else:

        future_orders.update(
            status="pending"
        )

    return JsonResponse({
        "success": True,
        "paused": subscription.paused,
        "message": (
            "Subscription paused successfully."
            if subscription.paused
            else "Subscription resumed successfully."
        )
    })


# ==========================================
# PAYMENT TOGGLE - AJAX
# ==========================================

@login_required
def toggle_paid(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request."
            },
            status=405
        )

    try:

        subscription = get_current_subscription(
            request.user
        )

    except Http404:

        return JsonResponse(
            {
                "success": False,
                "message": "No active subscription found."
            },
            status=404
        )

    subscription.paid = not subscription.paid

    subscription.save(
        update_fields=["paid"]
    )

    return JsonResponse({
        "success": True,
        "paid": subscription.paid,
        "message": (
            "Payment marked as Paid."
            if subscription.paid
            else "Payment status changed to Unpaid."
        )
    })


# ==========================================
# LEGACY PAUSE / RESUME
# ==========================================

@login_required
def toggle_pause(request):

    if request.method != "POST":
        return redirect("my_subscription")

    try:

        subscription = get_current_subscription(
            request.user
        )

    except Http404:

        messages.error(
            request,
            "No active subscription found."
        )

        return redirect("my_subscription")

    today = timezone.localdate()

    subscription.paused = not subscription.paused

    subscription.save(
        update_fields=["paused"]
    )

    if subscription.paused:

        subscription.orders.filter(
            date__gte=today,
            status="pending"
        ).update(
            status="paused"
        )

        messages.success(
            request,
            "Your subscription has been paused successfully."
        )

    else:

        subscription.orders.filter(
            date__gte=today,
            status="paused"
        ).update(
            status="pending"
        )

        messages.success(
            request,
            "Your subscription has been resumed successfully."
        )

    return redirect("my_subscription")


# ==========================================
# CANCEL SUBSCRIPTION
# ==========================================

@login_required
def cancel_subscription(request):

    if request.method != "POST":
        return redirect("my_subscription")

    try:

        subscription = get_current_subscription(
            request.user
        )

    except Http404:

        messages.error(
            request,
            "No active subscription found."
        )

        return redirect("my_subscription")

    today = timezone.localdate()

    with transaction.atomic():

        subscription.active = False
        subscription.paused = False
        subscription.cancelled_at = timezone.now()

        subscription.save(
            update_fields=[
                "active",
                "paused",
                "cancelled_at"
            ]
        )

        # Cancel future pending and paused orders
        subscription.orders.filter(
            date__gte=today,
            status__in=["pending", "paused"]
        ).update(
            status="cancelled"
        )

    messages.success(
        request,
        "Your subscription has been cancelled successfully!"
    )

    return redirect("my_subscription")


# ==========================================
# SKIP MEAL
# ==========================================

@login_required
def skip_meal(request, order_id):

    if request.method != "POST":
        return redirect("my_subscription")

    order = get_object_or_404(
        Order,
        id=order_id,
        subscription__user=request.user
    )

    today = timezone.localdate()

    if order.date < today:

        messages.error(
            request,
            "Past meals cannot be skipped."
        )

    elif order.status != "pending":

        messages.error(
            request,
            "This meal cannot be skipped."
        )

    else:

        order.status = "cancelled"

        order.save(
            update_fields=["status"]
        )

        messages.success(
            request,
            f"{order.meal_name} has been skipped successfully!"
        )

    return redirect("my_subscription")


# ==========================================
# CHANGE DIET
# ==========================================

@login_required
def change_diet(request):

    try:

        subscription = get_current_subscription(
            request.user
        )

    except Http404:

        messages.error(
            request,
            "No active subscription found."
        )

        return redirect("my_subscription")

    if request.method == "POST":

        new_diet = request.POST.get("diet")

        if new_diet in dict(
            Subscription.SUBSCRIPTION_DIET_CHOICES
        ):

            subscription.diet_preference = new_diet

            subscription.save(
                update_fields=["diet_preference"]
            )

            messages.success(
                request,
                "Diet preference updated successfully."
            )

        else:

            messages.error(
                request,
                "Invalid diet preference."
            )

        return redirect("my_subscription")

    return render(
        request,
        "main/change_diet.html",
        {
            "sub": subscription,
            "choices": Subscription.SUBSCRIPTION_DIET_CHOICES,
        }
    )


# ==========================================
# MEAL CATEGORY
# ==========================================

def meal_category(request, category):

    categories = {
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "evening_snacks": "Evening Snacks",
        "beverages": "Shakes & Beverages",
        "dinner": "Dinner",
    }

    if category not in categories:
        raise Http404("Meal category not found")

    meals = Meal.objects.filter(
        category=category
    ).order_by("name")

    return render(
        request,
        "main/meal_category.html",
        {
            "meals": meals,
            "category": category,
            "category_title": categories[category],
        }
    )


# ==========================================
# MEAL DETAIL
# ==========================================

def meal_detail(request, meal_id):

    meal = get_object_or_404(
        Meal,
        id=meal_id
    )

    return render(
        request,
        "main/meal_detail.html",
        {
            "meal": meal
        }
    )
