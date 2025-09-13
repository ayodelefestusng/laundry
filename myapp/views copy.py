import uuid
import json
import decimal
import logging
import requests
from datetime import timedelta
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.mail import send_mail
from .forms import (
    CustomUserCreationForm,
    OrderForm,
    OrderItemForm,
    CommentForm,
    ServiceForm
)
from .models import Order, OrderItem, Service, Comment, CustomUser, ServiceCategory

# Set the logging level for debug information
logging.basicConfig(level=logging.DEBUG)


def is_admin(user):
    return user.is_staff


def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, "Registration successful.")
            return redirect('home')
        messages.error(
            request, "Unsuccessful registration. Invalid information.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def customer_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                messages.success(
                    request, 'Order placed successfully! We will contact you shortly.')
                send_mail(
                'Laundry Service Request Confirmation',
                'Your request has been received. A dispatch agent will visit shortly.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
                return redirect('order_detail', order_id=order.id)
            except IntegrityError:
                messages.error(
                    request, "An error occurred while placing the order. Please try again.")
    else:
        form = OrderForm()
    return render(request, 'customer_order.html', {'form': form})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to view this order.")
        return redirect('home')

    items = order.items.all()
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'order_detail.html', context)


# HTMX Views
@login_required
@user_passes_test(is_admin)
def htmx_get_services(request):
    category_id = request.GET.get('category')
    if category_id:
        services = Service.objects.filter(category_id=category_id)
    else:
        services = Service.objects.all()
    return render(request, 'htmx/service_options.html', {'services': services})


@login_required
@user_passes_test(is_admin)
def htmx_get_service_details(request):
    service_id = request.GET.get('service')
    service = get_object_or_404(Service, id=service_id)
    return render(request, 'htmx/service_details.html', {'service': service})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def htmx_add_item(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    form = OrderItemForm(request.POST)

    if form.is_valid():
        service = form.cleaned_data['service']
        price = service.price
        delivery_time_days = service.delivery_time_days
        
        try:
            item = form.save(commit=False)
            item.order = order
            item.price = price
            item.delivery_time_days = delivery_time_days
            item.save()
            return render(request, 'htmx/item_table_row.html', {'item': item})
        except IntegrityError as e:
            return HttpResponse(f"Error: {e}", status=400)
    
    return HttpResponse(form.errors.as_json(), status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "PUT"])
def htmx_edit_item(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id)
    if request.method == "GET":
        form = OrderItemForm(instance=item)
        return render(request, 'htmx/item_edit_form.html', {'item': item, 'form': form})

    elif request.method == "PUT":
        data = json.loads(request.body)
        print ("Ale",data)
        form = OrderItemForm(data, instance=item)
        if form.is_valid():
            service = form.cleaned_data['service']
            item = form.save(commit=False)
            item.price = service.price
            item.delivery_time_days = service.delivery_time_days
            item.save()
            return render(request, 'htmx/item_table_row.html', {'item': item})
        return HttpResponse(form.errors.as_json(), status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def htmx_delete_item(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id)
    item.delete()
    return HttpResponse(status=200)


@login_required
@user_passes_test(is_admin)
def htmx_get_order_summary(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    
    items = order.items.all()
    # Corrected to access price through the related Service object
    total_price = sum(item.service.price for item in items)
    
    if items:
        max_delivery_days = max(item.service.delivery_time_days for item in items)
        estimated_delivery_date = timezone.now().date() + timedelta(days=max_delivery_days)
    else:
        estimated_delivery_date = None

    summary = {
        'total_items': items.count(),
        'total_price': total_price,
        'delivery_date': estimated_delivery_date,
    }
    
    return render(request, 'htmx/order_summary.html', {'summary': summary})


@login_required
@user_passes_test(is_admin)
def htmx_send_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    items = order.items.all()
    if not items:
        return HttpResponse("No items to invoice.", status=400)

    # Calculate summary details
    total_price = sum(item.service.price for item in items)
    if items:
        max_delivery_days = max(item.service.delivery_time_days for item in items)
        estimated_delivery_date = timezone.now().date() + timedelta(days=max_delivery_days)
    else:
        estimated_delivery_date = None

    summary = {
        'total_items': items.count(),
        'total_price': total_price,
        'delivery_date': estimated_delivery_date,
    }
    
    # Update order details in the database
    order.total_price = total_price
    order.estimated_delivery_date = estimated_delivery_date
    order.status = 'invoice_sent'
    order.save()

    # Generate absolute URLs for the email links
    paypal_url = request.build_absolute_uri(reverse('paypal_checkout', args=[order.id]))
    comment_url = request.build_absolute_uri(reverse('comment_order', args=[order.id]))

    # Render email template as a string
    email_html_content = render_to_string('htmx/invoice_email.html', {
        'order': order,
        'items': items,
        'summary': summary,
        'customer_name': order.customer_name,
        'paypal_url': paypal_url,
        'comment_url': comment_url,
    })




    # Send email
    try:
        email = EmailMessage(
            f'Invoice for Order #{order.id}',
            email_html_content,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer_email],
        )
        email.content_subtype = "html"  # Main content is now html
        email.send()
        return render(request, 'htmx/invoice_sent_message.html')
    except Exception as e:
        messages.error(request, f'Failed to send email: {e}')
        return HttpResponse("Failed to send invoice.", status=500)


# Admin Views
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    pending_requests = Order.objects.filter(status='pending').order_by('created_at')
    in_progress_orders = Order.objects.filter(
        status='in_progress').order_by('-created_at')
    commented_orders = Order.objects.filter(
        status='commented').order_by('-created_at')
    
    context = {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_review_request(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except (Order.DoesNotExist, ValueError):
        messages.error(request, "Invalid order ID provided.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order details updated successfully.')
            return redirect('admin_review_request', order_id=order.id)
    else:
        form = OrderForm(instance=order)

    items = order.items.all()
    add_item_form = OrderItemForm()
    service_form = ServiceForm()
    
    # Pass all service categories to the context
    all_categories = ServiceCategory.objects.all()

    context = {
        'order': order,
        'form': form,
        'items': items,
        'add_item_form': add_item_form,
        'service_form': service_form,
        'all_categories': all_categories,
    }
    return render(request, 'admin_review.html', context)


@login_required
@user_passes_test(is_admin)
def admin_approve_comment(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        if order.status != 'commented':
            messages.error(request, 'This order is not awaiting comment approval.')
            return redirect('admin_dashboard')
    except (Order.DoesNotExist, ValueError):
        messages.error(request, "Invalid order ID.")
        return redirect('admin_dashboard')

    comment = get_object_or_404(Comment, order=order)
    
    if request.method == 'POST':
        order.status = 'in_progress'
        order.save()
        messages.success(request, f'Comment for order #{order.id} approved and status changed to In Progress.')
        return redirect('admin_dashboard')
        
    context = {
        'order': order,
        'comment': comment
    }
    return render(request, 'admin_approve_comment.html', context)


# Comment Views
def comment_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.order = order
            comment.save()
            order.status = 'commented'
            order.save()
            return redirect('comment_success')
    else:
        form = CommentForm()

    context = {
        'order': order,
        'form': form,
    }
    return render(request, 'add_comment.html', context)


def comment_success(request):
    return render(request, 'comment_success.html')


# Payment Views
def get_paypal_access_token():
    """Retrieves a PayPal access token."""
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post(f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token", auth=auth, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting PayPal access token: {e}")
        return None


def create_paypal_payment(request, order_id):
    """Initiates a PayPal checkout and redirects the user."""
    order = get_object_or_404(Order, pk=order_id)
    items = order.items.all()
    if not items:
        messages.error(request, "Cannot create a payment for an empty order.")
        return redirect('order_detail', order_id=order.id)
    
    # Calculate total price
    total_price = sum(item.service.price for item in items)
    
    access_token = get_paypal_access_token()
    if not access_token:
        messages.error(request, "Failed to connect to PayPal. Please try again later.")
        return redirect('order_detail', order_id=order.id)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": str(total_price)
            }
        }],
        "application_context": {
            "return_url": request.build_absolute_uri(reverse('paypal_success')),
            "cancel_url": request.build_absolute_uri(reverse('paypal_cancel')),
        }
    }

    try:
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        
        # Redirect to PayPal's approval link
        for link in response.json()['links']:
            if link['rel'] == 'approve':
                return redirect(link['href'])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error creating PayPal order: {e}")
        messages.error(request, "Failed to create a PayPal payment. Please try again.")

    return redirect('order_detail', order_id=order.id)


def paypal_success(request):
    """Handles a successful PayPal payment."""
    token = request.GET.get('token')
    
    access_token = get_paypal_access_token()
    if not access_token:
        messages.error(request, "Failed to confirm payment. Please contact support.")
        return redirect('home')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        # Capture the payment
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{token}/capture",
            headers=headers
        )
        response.raise_for_status()

        # Update order status to 'paid'
        order_id_from_paypal = response.json()['purchase_units'][0]['reference_id']
        order = get_object_or_404(Order, pk=order_id_from_paypal)
        order.status = 'paid'
        order.save()

        messages.success(request, "Your payment was successful!")
        return render(request, 'paypal_success.html')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error capturing PayPal payment: {e}")
        messages.error(request, "There was an issue processing your payment. Please contact support.")
        return redirect('home')


def paypal_cancel(request):
    """Handles a canceled PayPal payment."""
    messages.warning(request, "Your payment was canceled.")
    return render(request, 'paypal_cancel.html')


def create_stripe_checkout(request, order_id):
    return HttpResponse("This view would initiate a Stripe checkout. Currently, it's a placeholder.")


def stripe_success(request):
    return render(request, 'stripe_success.html')


def stripe_cancel(request):
    return render(request, 'stripe_cancel.html')
