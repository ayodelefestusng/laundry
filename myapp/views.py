import datetime
import uuid
import stripe
import paypalrestsdk

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone

from .models import (
    Order, OrderItem, Service, ServiceCategory,
    Comment, CustomUser, ORDER_STATUS,
)
from .forms import (
    OrderForm, OrderItemForm, CommentForm, CustomUserCreationForm
)
from .utils import is_admin

stripe.api_key = settings.STRIPE_SECRET_KEY

def calculate_and_update_order(order):
    """
    Helper function to calculate and update an order's total price and delivery date.
    This prevents code repetition in multiple views.
    """
    items_qs = order.items.all()
    order.total_price = items_qs.aggregate(total_price=Sum('price'))['total_price'] or 0
    if items_qs.exists():
        max_delivery_days = max(item.delivery_time_days for item in items_qs)
        order.estimated_delivery_date = order.pickup_date + timezone.timedelta(days=max_delivery_days)
    else:
        order.estimated_delivery_date = None
    order.save()
    return calculate_order_summary(order)


def calculate_order_summary(order):
    """
    Calculates the total price, number of items, and estimated delivery date for an order.
    """
    total_price = sum(item.price for item in order.items.all())
    total_items = order.items.count()
    delivery_date = None
    if order.items.exists():
        max_delivery_days = max(item.delivery_time_days for item in order.items.all())
        delivery_date = order.pickup_date + timezone.timedelta(days=max_delivery_days)

    return {
        'total_price': total_price,
        'total_items': total_items,
        'delivery_date': delivery_date
    }


# Customer-facing views

def home(request):
    """
    Renders the homepage.
    """
    return render(request, 'home.html')


def register(request):
    """
    Handles user registration.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def customer_order(request):
    """
    Handles the creation of a new customer order.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            send_mail(
                'Laundry Service Request Confirmation',
                f'Your request has been received. A dispatch agent will visit on {request.POST["pickup_date"]}',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm()

    context = {
        'form': form,
    }
    return render(request, 'customer_order.html', context)


@login_required
def order_detail(request, order_id):
    """
    Displays the details of a specific order.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    order_summary = calculate_order_summary(order)
    add_item_form = OrderItemForm()
    all_categories = ServiceCategory.objects.all()

    context = {
        'order': order,
        'order_items': order_items,
        'summary': order_summary,
        'add_item_form': add_item_form,
        'all_categories': all_categories,
    }
    return render(request, 'order_detail.html', context)


@login_required
def htmx_add_item(request, order_id):
    """
    Handles adding a new item to an order via HTMX.
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        form = OrderItemForm(request.POST)

        if form.is_valid():
            service = form.cleaned_data['service']
            new_item = form.save(commit=False)
            new_item.order = order
            new_item.name = form.cleaned_data['name']
            new_item.color = form.cleaned_data['color']
            new_item.price = service.price
            new_item.delivery_time_days = service.delivery_time_days
            new_item.save()

            # Recalculate and update the order summary
            item_summary = calculate_and_update_order(order)
            
            # Render new item row and updated summary
            return HttpResponse(
                render_to_string(
                    'htmx/item_table_row.html', {'item': new_item}
                ) + render_to_string(
                    'htmx/order_summary.html', {'summary': item_summary}
                )
            )
    return HttpResponseBadRequest("Invalid form submission")


def htmx_get_services(request):
    """
    Returns a list of services based on the selected category via HTMX.
    """
    category_id = request.GET.get('category')
    if category_id:
        services = Service.objects.filter(category_id=category_id)
    else:
        services = Service.objects.none()
    
    return render(request, 'htmx/service_options.html', {'services': services})


def htmx_get_service_details(request):
    """
    Returns the price and delivery time for a selected service via HTMX.
    """
    service_id = request.GET.get('service')
    service = get_object_or_404(Service, id=service_id) if service_id else None
    return render(request, 'htmx/service_details.html', {'service': service})


@login_required
def htmx_edit_item(request, item_id):
    """
    Handles editing an order item via HTMX.
    """
    item = get_object_or_404(OrderItem, id=item_id)
    if request.method == 'GET':
        form = OrderItemForm(instance=item)
        all_categories = ServiceCategory.objects.all()
        context = {
            'item': item,
            'form': form,
            'all_categories': all_categories,
        }
        return render(request, 'htmx/edit_item_form_row.html', context)
    
    elif request.method == 'POST':
        form = OrderItemForm(request.POST, instance=item)
        if form.is_valid():
            service = form.cleaned_data['service']
            item = form.save(commit=False)
            item.price = service.price
            item.delivery_time_days = service.delivery_time_days
            item.save()
            order = item.order
            
            # Recalculate and update the order summary
            item_summary = calculate_and_update_order(order)
            
            return render(request, 'htmx/item_table_row.html', {'item': item, 'summary': item_summary})

    return HttpResponseBadRequest("Invalid request method.")


@login_required
def htmx_delete_item(request, item_id):
    """
    Handles deleting an order item via HTMX.
    """
    if request.method == 'DELETE':
        item = get_object_or_404(OrderItem, id=item_id)
        order = item.order
        item.delete()
        
        # Recalculate and update the order summary
        calculate_and_update_order(order)
        
        return HttpResponse(status=204) # 204 No Content


@login_required
def htmx_get_order_summary(request, order_id):
    """
    Returns the updated order summary via HTMX.
    """
    order = get_object_or_404(Order, id=order_id)
    summary = calculate_order_summary(order)
    return render(request, 'htmx/order_summary.html', {'summary': summary})


def htmx_send_invoice(request, order_id):
    """
    Sends an invoice email to the customer and updates the order status.
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Recalculate summary before sending
        order_summary = calculate_order_summary(order)
        order.total_price = order_summary['total_price']
        order.estimated_delivery_date = order_summary['delivery_date']
        order.save()
        
        # Create the email content
        email_content = render_to_string(
            'htmx/invoice_email.html', 
            {'order': order, 'items': order.items.all(), 'summary': order_summary, 'customer_name': order.customer_name}
        )
        
        email = EmailMessage(
            f'Invoice for your Laundry Order #{order.id}',
            email_content,
            'from@example.com',
            [order.customer_email],
        )
        email.content_subtype = "html"
        email.send()

        # Update order status
        order.status = 'invoice_sent'
        order.save()
        
        return render(request, 'htmx/invoice_sent_message.html')

    return HttpResponseBadRequest("Invalid request method.")


def comment_order(request, order_id):
    """
    Handles the comment form submission.
    """
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.order = order
            comment.save()
            return redirect('comment_success')
    else:
        form = CommentForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'add_comment.html', context)


def comment_success(request):
    return render(request, 'comment_success.html')


def create_stripe_checkout(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # This is where you would integrate with Stripe's API
    # For now, it's a placeholder view
    # In a real app, you would create a Stripe checkout session here
    
    # Placeholder: redirect to a success page
    return render(request, 'stripe_success.html')


def create_paypal_payment(request, order_id):
    """
    Handles the creation of a PayPal payment.
    """
    order = get_object_or_404(Order, id=order_id)
    # This is where you would integrate with the PayPal API.
    # For now, it's a placeholder view. In a real application, you would:
    # 1. Create a PayPal Order.
    # 2. Redirect the user to the PayPal approval URL.
    
    # Placeholder: redirect to a success page
    return render(request, 'paypal_success.html')


def paypal_success(request):
    """
    Handles the redirect after a successful PayPal payment.
    """
    return render(request, 'paypal_success.html')


def stripe_success(request):
    # This view would be the success URL for Stripe checkout
    return render(request, 'stripe_success.html')


def stripe_cancel(request):
    # This view would be the cancel URL for Stripe checkout
    return render(request, 'stripe_cancel.html')


@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Displays the admin dashboard with various order statuses.
    """
    pending_requests = Order.objects.filter(status='pending')
    in_progress_orders = Order.objects.filter(status='in_progress')
    commented_orders = Order.objects.filter(comments__isnull=False).distinct()

    context = {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
    }
    return render(request, 'admin_dashboard.html', context)


@user_passes_test(is_admin)
def admin_review_request(request, order_id):
    """
    Allows an admin to review and process a pending order request.
    """
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    comments = Comment.objects.filter(order=order).order_by('-created_at')

    context = {
        'order': order,
        'order_items': order_items,
        'comments': comments,
    }
    return render(request, 'admin_review.html', context)


@user_passes_test(is_admin)
def admin_approve_comment(request, order_id):
    """
    Allows an admin to approve a comment and update the order status.
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Logic to approve the comment or change order status
    # For now, let's just update the order status
    order.status = 'in_progress'
    order.save()
    
    messages.success(request, f"Order #{order.id} has been approved and moved to In Progress.")
    
    # Redirect back to the admin dashboard or a success page
    return redirect('admin_dashboard')
