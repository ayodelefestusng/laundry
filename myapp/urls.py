from django.urls import path

from . import views

app_name = 'laundry'

urlpatterns = [
    # General app views
    path('homes2/', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('', views.customer_order, name='customer_order'),
    # path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/order/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('customer/order/<uuid:order_id>/review/', views.customer_review, name='customer_review'),
    path('customer/order/<uuid:order_id>/accept/', views.accept_order, name='accept_order'),
    path('customer/order/<uuid:order_id>/comment/', views.comment_order, name='comment_order'),
    path('customer/order/<uuid:order_id>/confirm/', views.confirm_order, name='confirm_order'),
    path('comment/success/', views.comment_success, name='comment_success'),
    
    path('customer/assign_qr/<uuid:order_id>/', views.assign_qr_code, name='assign_qr_code'),
    path('assign_qr_to_order/<uuid:order_id>/', views.assign_qr_to_order_view, name='assign_qr_to_order'),
   
   
    

    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('review/<uuid:order_id>/', views.admin_review_request, name='admin_review_request'),
    path('approve_comment/<uuid:order_id>/', views.admin_approve_comment, name='admin_approve_comment'),
    
    # Employee Workflow views
    path('employee/queue/', views.employee_queue, name='employee_queue'),
    path('employee/accept/<int:item_id>/', views.accept_item, name='accept_item'),
    path('employee/reject/<int:item_id>/', views.reject_item, name='reject_item'),

    # HTMX endpoints
    path('htmx/get_services/', views.htmx_get_package_options, name='htmx_get_package_options'),
    path('htmx/get_service_details/', views.htmx_get_package_details, name='htmx_get_package_details'),
    path('htmx/add_item/<uuid:order_id>/', views.htmx_add_item, name='htmx_add_item'),
    path('htmx/edit_item/<int:item_id>/', views.htmx_edit_item, name='htmx_edit_item'),
    path('htmx/delete_item/<int:item_id>/', views.htmx_delete_item, name='htmx_delete_item'),
    path('htmx/get_order_summary/<uuid:order_id>/', views.htmx_get_order_summary, name='htmx_get_order_summary'),
    path('htmx/send_invoice/<uuid:order_id>/', views.htmx_send_invoice, name='htmx_send_invoice'),
    path('api/assign_qr_to_item/<int:item_id>/', views.api_assign_qr_to_item, name='api_assign_qr_to_item'),

    # Payment redirects
#     path('paypal/success/', views.paypal_success, name='paypal_success'),
#     path('paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
#    path('paypal/checkout/<uuid:order_id>/', views.create_paypal_payment, name='paypal_checkout'),
#     path('stripe/success/', views.stripe_success, name='stripe_success'),
#     path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),




    #Paystack 
path('paystack-callback/<uuid:order_id>/', views.paystack_callback_view, name='paystack_callback'),
    # 🎯 2. LIVE WEBHOOK URL (Server-to-server confirmation)
    path('paystack-webhook/', views.paystack_webhook_view, name='paystack_webhook'),
path('paystack/success/', views.paystack_success, name='paystack_success'),
    path('paystack/cancel/', views.paystack_cancel, name='paystack_cancel'),





    path('send_email/', views.laundry_request_confirmation, name='confirm_laundry'),



]
