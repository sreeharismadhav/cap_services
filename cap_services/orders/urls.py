from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('invoice/pdf/<int:order_id>/', views.invoice_pdf, name='invoice_pdf'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('payment/initiate/<int:order_id>/', views.payment_initiate, name='payment_initiate'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/failed/<int:order_id>/', views.payment_failed, name='payment_failed'),
    path('payment/retry/<int:order_id>/', views.payment_retry, name='payment_retry'),
    path('payment/success/<int:order_id>/', views.payment_success, name='payment_success'),
]