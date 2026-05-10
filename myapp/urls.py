

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import tenant_admin_views

app_name = 'laundry'

urlpatterns = [
    # General app views
    path('homes2/', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('login/', auth_views.LoginView.as_view(authentication_form=views.CustomAuthenticationForm), name='login'),

    path("check-username/", views.check_username, name='check_username'),


    #  path("register/", views.register, name="register"),
    path("setup-password/<int:user_id>/<str:token>/", views.setup_password, name="setup_password"),
    path("password-reset/", views.password_reset_request, name="password_reset"),
    path("change-password/", views.change_password, name="change_password"),
    
    
    path('terms-and-privacy/', views.terms_and_privacy, name='terms_and_privacy'),



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
    path('view_order_admin/<uuid:order_id>/', views.view_order_admin, name='view_order_admin'),
    
    # BI Dashboard Views
    path('bi/dashboard/', views.dashboard_view, name='dashboard'),
    path('bi/dashboard-async/', views.dashboard_details_async, name='dashboard_details_async'),
    path('bi/export/', views.export_bi_csv, name='export_bi_csv'),
    
    # Commission Dashboard Views
    path('commission/', views.commission_dashboard, name='commission_dashboard'),
    path('commission/export/', views.export_commission_csv, name='export_commission_csv'),
    
    # Employee Workflow views
    path('employee/queue/', views.employee_queue, name='employee_queue'),
    path('employee/accept/<int:item_id>/', views.accept_item, name='accept_item'),
    path('employee/reject/<int:item_id>/', views.reject_item, name='reject_item'),
    path('transit/', views.qr_transit_scanner, name='qr_transit_scanner'),
    path('transit/scan/', views.htmx_transit_scan, name='htmx_transit_scan'),
    path('dispatch/inward/', views.dispatch_inward, name='dispatch_inward'),
    path('dispatch/delivery/', views.dispatch_delivery, name='dispatch_delivery'),
    # path('htmx_update_shipping/<uuid:order_id>/', views.htmx_update_shipping, name='htmx_update_shipping'),

    # HTMX endpoints
    path('htmx/get_services/', views.htmx_get_package_options, name='htmx_get_package_options'),
    path('htmx/get_service_details/', views.htmx_get_package_details, name='htmx_get_package_details'),
    path('htmx/add_item/<uuid:order_id>/', views.htmx_add_item, name='htmx_add_item'),
    path('htmx/edit_item/<int:item_id>/', views.htmx_edit_item, name='htmx_edit_item'),
    path('htmx/delete_item/<int:item_id>/', views.htmx_delete_item, name='htmx_delete_item'),
    path('htmx/get_order_summary/<uuid:order_id>/', views.htmx_get_order_summary, name='htmx_get_order_summary'),
    path('htmx/track_order/', views.htmx_track_order, name='htmx_track_order'),
    # path('htmx/calculate_delivery/', views.htmx_calculate_delivery, name='htmx_calculate_delivery'),
    path('htmx/calculate_delivery/<uuid:order_id>/', views.htmx_calculate_delivery, name='htmx_calculate_delivery'),
    path('htmx/update_shipping/<uuid:order_id>/', views.htmx_update_shipping, name='htmx_update_shipping'),
    path('htmx/send_invoice/<uuid:order_id>/', views.htmx_send_invoice, name='htmx_send_invoice'),
    path('api/assign_qr_to_item/<int:item_id>/', views.api_assign_qr_to_item, name='api_assign_qr_to_item'),
    path('api/catalog/', views.api_get_catalog, name='api_get_catalog'),
    path('reschedule/delivery/', views.reschedule_delivery, name='reschedule_delivery'),

#  # HTMX endpoints
#     path('htmx/get_services/', views.htmx_get_services, name='htmx_get_services'),
#     path('htmx/get_service_details/', views.htmx_get_service_details, name='htmx_get_service_details'),



 path('htmx/get_towns/', views.htmx_get_towns, name='htmx_get_towns'),
 path('htmx/calculate_deliverys/', views.htmx_calculate_deliverys, name='htmx_calculate_deliverys'),
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

    # Tenant Admin Hub Generic Views
    path('tenant-settings/', tenant_admin_views.tenant_admin_hub, name='tenant_admin_hub'),
    path('tenant-settings/<str:model_name>/', tenant_admin_views.TenantGenericListView.as_view(), name='tenant_admin_list'),
    path('tenant-settings/<str:model_name>/create/', tenant_admin_views.TenantGenericCreateView.as_view(), name='tenant_admin_create'),
    path('tenant-settings/<str:model_name>/<int:pk>/update/', tenant_admin_views.TenantGenericUpdateView.as_view(), name='tenant_admin_update'),
    path('tenant-settings/<str:model_name>/<int:pk>/delete/', tenant_admin_views.TenantGenericDeleteView.as_view(), name='tenant_admin_delete'),
    
    # QR Code Generation
    path('generate-qr-codes/', tenant_admin_views.generate_qr_codes, name='generate_qr_codes'),
]
