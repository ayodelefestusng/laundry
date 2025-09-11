from django.urls import path
from . import views

urlpatterns = [
    # Customer-facing URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),

    path('customer/order/', views.customer_order, name='customer_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('comment/<int:order_id>/', views.comment_order, name='comment_order'),
    
    # Payment URLs
    path('stripe/checkout/<int:order_id>/', views.create_stripe_checkout, name='stripe_checkout'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('paypal/payment/<int:order_id>/', views.create_paypal_payment, name='paypal_payment'),
    path('paypal/success/', views.paypal_success, name='paypal_success'),

    # Admin URLs
    path('admins/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admins/review/<int:order_id>/', views.admin_review_request, name='admin_review_request'),
    path('admin/approve_comment/<int:order_id>/', views.admin_approve_comment, name='admin_approve_comment'),

    # HTMX URLs for dynamic content
    path('htmx/order_summary/<int:order_id>/', views.htmx_get_order_summary, name='htmx_get_order_summary'),
    path('htmx/add_item/<int:order_id>/', views.htmx_add_item, name='htmx_add_item'),
    path('htmx/edit_item/<int:order_id>/<int:item_id>/', views.htmx_edit_item, name='htmx_edit_item'),
    path('htmx/delete_item/<int:order_id>/<int:item_id>/', views.htmx_delete_item, name='htmx_delete_item'),
    path('htmx/send_invoice/<int:order_id>/', views.htmx_send_invoice, name='htmx_send_invoice'),
]
