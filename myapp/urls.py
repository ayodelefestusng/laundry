from django.urls import path
from . import views

urlpatterns = [
    # Customer-facing URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('request-service/', views.service_request, name='service_request'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order-review/<int:order_id>/', views.order_review, name='order_review'),
    path('accept-order/<int:order_id>/', views.accept_order, name='accept_order'),
    path('comment-order/<int:order_id>/', views.comment_order, name='comment_order'),

    # HTMX-specific URLs
    path('htmx/order-summary/<int:order_id>/', views.htmx_order_summary, name='htmx_order_summary'),
    path('htmx/comment-form/<int:order_id>/', views.htmx_comment_form, name='htmx_comment_form'),
    path('htmx/submit-comment/<int:order_id>/', views.htmx_submit_comment, name='htmx_submit_comment'),
    path('htmx/add-item-form/', views.htmx_add_item_form, name='htmx_add_item_form'),
    path('htmx/get-services/', views.htmx_get_services, name='htmx_get_services'),

path('htmx/get-service-details/', views.htmx_get_service_details, name='htmx_get_service_details'),


    # Admin-facing URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-review-request/<int:order_id>/', views.admin_review_request, name='admin_review_request'),
    path('update-item-details/<int:item_id>/', views.update_item_details, name='update_item_details'),
    path('generate-qr-codes/<int:order_id>/', views.generate_qr_codes, name='generate_qr_codes'),
    path('update-workflow-stage/<int:item_id>/', views.update_workflow_stage, name='update_workflow_stage'),
    path('admin-approve-comment/<int:order_id>/', views.admin_approve_comment, name='admin_approve_comment'),
]