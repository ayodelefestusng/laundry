from django.urls import path
from . import views

urlpatterns = [
    # Customer-facing views
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('order/', views.customer_order, name='customer_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # HTMX views
    path('htmx/add-item/<int:order_id>/', views.htmx_add_item, name='htmx_add_item'),
    path('htmx/edit-item/<int:item_id>/', views.htmx_edit_item, name='htmx_edit_item'),
    path('htmx/delete-item/<int:item_id>/', views.htmx_delete_item, name='htmx_delete_item'),
    path('htmx/get-services/', views.htmx_get_services, name='htmx_get_services'),
    path('htmx/get-service-details/', views.htmx_get_service_details, name='htmx_get_service_details'),
    path('htmx/order-summary/<int:order_id>/', views.htmx_get_order_summary, name='htmx_order_summary'),
    path('htmx/send-invoice/<int:order_id>/', views.htmx_send_invoice, name='htmx_send_invoice'),

    # Comment views
    path('order/<int:order_id>/comment/', views.comment_order, name='comment_order'),
    path('comment/success/', views.comment_success, name='comment_success'),

    # Payment views
    path('stripe/checkout/<int:order_id>/', views.create_stripe_checkout, name='stripe_checkout'),
    path('paypal/payment/<int:order_id>/', views.create_paypal_payment, name='create_paypal_payment'),
    path('paypal/success/', views.paypal_success, name='paypal_success'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),

    # Admin views
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/review/<int:order_id>/', views.admin_review_request, name='admin_review_request'),
    path('admin/approve-comment/<int:order_id>/', views.admin_approve_comment, name='admin_approve_comment'),
]
