from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('table/<int:table_id>/', views.welcome, name='welcome'),

    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('current_order/', views.current_order, name='current_order'),
    path('checkout/', views.checkout, name='checkout'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('place_order/', views.place_order, name='place_order'),
    path("my-orders/", views.my_orders, name="my_orders"),
    path('success/', views.success, name='success'),
    path("request-bill/", views.request_bill, name="request_bill"),
    path("payment/", views.payment, name="payment"),
    path("thank-you/<int:table_id>/", views.thank_you, name="thank_you"),
    path("restaurant/orders/", views.admin_orders, name="admin_orders"),
    path(
    "restaurant/served-orders/",
    views.served_orders_history,
    name="served_orders_history",
),
    path(
    "restaurant/order-item/<int:item_id>/<str:status>/",
    views.update_order_item_status,
    name="update_order_item_status",
),
]