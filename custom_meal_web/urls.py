from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/", views.menu_view, name="menu"),
    path("meals/<str:category>/",views.meal_category,name="meal_category"),
    path("meal/<int:meal_id>/",views.meal_detail,name="meal_detail"),
    path("skip-meal/<int:order_id>/",views.skip_meal,name="skip_meal"),
    path("toggle-subscription-pause/",views.toggle_subscription_pause,name="toggle_subscription_pause"),
    path("cancel-subscription/",views.cancel_subscription,name="cancel_subscription"),
    path("subscription-history/",views.subscription_history,name="subscription_history"),
    path("delete-subscription-history/<int:subscription_id>/",views.delete_subscription_history,name="delete_subscription_history"),
    path("register/", views.register, name="register"),
    path("login/",auth_views.LoginView.as_view(template_name="main/login.html"),name="login",),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("my-subscription/", views.my_subscription, name="my_subscription"),
    path("toggle-paid/", views.toggle_paid, name="toggle_paid"),
    path("toggle-pause/", views.toggle_pause, name="toggle_pause"),
    path("change-diet/", views.change_diet, name="change_diet"),
    path("edit-subscription/",views.edit_subscription,name="edit_subscription"),
    
]
