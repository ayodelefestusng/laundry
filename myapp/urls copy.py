import uuid
from django.urls import path

from . import views

urlpatterns = [
    # Customer-facing views
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('customer/order/', views.customer_order, name='customer_order'),
    path('order/<uuid:order_id>/', views.order_detail, name='order_detail'),

    # HTMX views
    path('htmx/add-item/<uuid:order_id>/', views.htmx_add_item, name='htmx_add_item'),
    path('htmx/get-services/', views.htmx_get_services, name='htmx_get_services'),
    path('htmx/get-service-details/', views.htmx_get_service_details, name='htmx_get_service_details'),
    # Corrected path for OrderItem to use <int:item_id>
    path('htmx/edit-item/<int:item_id>/', views.htmx_edit_item, name='htmx_edit_item'),
    # Corrected path for OrderItem to use <int:item_id>
    path('htmx/delete-item/<int:item_id>/', views.htmx_delete_item, name='htmx_delete_item'),
    path('htmx/order-summary/<uuid:order_id>/', views.htmx_get_order_summary, name='htmx_get_order_summary'),
    path('htmx/send-invoice/<uuid:order_id>/', views.htmx_send_invoice, name='htmx_send_invoice'),

    # Comment views
    path('comment/<uuid:order_id>/', views.comment_order, name='comment_order'),
    path('comment/success/', views.comment_success, name='comment_success'),

    # Payment views
    path('stripe/checkout/<uuid:order_id>/', views.create_stripe_checkout, name='stripe_checkout'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
    path('paypal/checkout/<uuid:order_id>/', views.create_paypal_payment, name='paypal_checkout'),
    path('paypal/success/', views.paypal_success, name='paypal_success'),
    path('paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),

    # Admin views
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('review/<uuid:order_id>/', views.admin_review_request, name='admin_review_request'),
    path('approve/<uuid:order_id>/', views.admin_approve_comment, name='admin_approve_comment'),
]
