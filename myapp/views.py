from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Order, OrderItem, Service, ServiceCategory, Comment
from .forms import OrderForm, OrderItemForm, CommentForm, CustomUserCreationForm, AddItemForm
from django.contrib import messages, auth
from django.views.decorators.http import require_http_methods
from .utils import is_admin
from django.core.mail import send_mail
import json
from uuid import UUID
from uuid import UUID
from django.db import IntegrityError
from django.contrib.auth.decorators import user_passes_test
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)
import requests
# User-facing views

def homepage(request):
    """
    Renders the homepage.
    """
    return render(request, 'homepage.html')

def register(request):
    """
    Renders the user registration form and handles form submission.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            messages.success(request, 'Registration successful. Welcome!')
            return redirect('homepage')
        else:
            messages.error(request, 'There was an error with your registration.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def custom_logout(request):
    """
    Logs the user out and redirects to the homepage.
    """
    auth.logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('homepage')

@login_required
@require_http_methods(["GET", "POST"])
def customer_order1(request):
    """
    Allows a customer to place a new order.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        print ("Form Data:", request.POST)
        if form.is_valid():
            try:
                order = form.save(commit=False)
                order.customer = request.user
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
                return redirect('admin_dashboard')
            except IntegrityError:
                messages.error(
                    request, "An error occurred while placing the order. Please try again.")    
            # Redirect to the admin review page for now for testing
            
        else:
            print("Form errors:", form.errors)
        
    else:
        form = OrderForm()
    return render(request, 'customer_order.html', {'form': form})



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
def customer_dashboard(request):
    """
    Renders the customer dashboard with a list of their orders.
    """
    customer_orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    context = {'customer_orders': customer_orders}
    return render(request, 'customer_dashboard.html', context)

@login_required
def order_detail(request, order_id):
    """
    Displays the details of a specific order.
    """
    # order = get_object_or_404(Order, id=order_id, customer=request.user)
    order = get_object_or_404(Order, id=order_id)
    print ("Order ID:", order)
    context = {'order': order}
    return render(request, 'order_detail.html', context)

@login_required
def customer_review(request, order_id):
    """
    Renders the page for a customer to review an order and add a comment.
    """
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    context = {'order': order}
    return render(request, 'customer_review.html', context)

@login_required
def accept_order(request, order_id):
    """
    Allows a customer to accept an order.
    """
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    order.status = 'accepted'
    order.save()
    messages.success(request, "Your order has been accepted. Thank you!")
    return redirect('customer_dashboard')

@login_required
def comment_order(request, order_id):
    """
    Allows a customer to leave a comment on their order.
    """
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.order = order
            comment.author = request.user
            comment.save()
            order.has_comment = True
            order.save()
            return redirect('comment_success')
    else:
        form = CommentForm()
    context = {'order': order, 'form': form}
    return render(request, 'add_comment.html', context)

def comment_success(request):
    """
    Renders a success page after a comment is submitted.
    """
    return render(request, 'comment_success.html')

# Admin-facing views

def admin_dashboard(request):
    """
    Admin dashboard to view pending, in-progress, and commented orders.
    """
    # pending_requests = Order.objects.filter(status='pending')
    # in_progress_orders = Order.objects.filter(status='in_progress')
    # commented_orders = Order.objects.filter(has_comment=True, comment__is_approved=False).distinct()
    
    pending_requests = Order.objects.filter(status='pending').order_by('created_at')
    in_progress_orders = Order.objects.filter(status='in_progress').order_by('-created_at')
    commented_orders = Order.objects.filter(status='commented').order_by('-created_at')
    
    context = {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
    }
    return render(request, 'admin_dashboard.html', context)

@require_http_methods(["GET"])
def admin_review_request(request, order_id):
    """
    Renders the admin review page for a specific order.
    """
    order = get_object_or_404(Order, id=order_id)
    form = OrderItemForm()
    all_categories = ServiceCategory.objects.all()
    
    context = {
        'order': order,
        'form': form,
        'all_categories': all_categories,
    }
    return render(request, 'admin_review_request.html', context)

@is_admin
@require_http_methods(["POST"])
def admin_approve_comment(request, order_id):
    """
    Allows an admin to approve a customer's comment.
    """
    order = get_object_or_404(Order, id=order_id)
    comment = order.comment_set.first()
    if comment:
        comment.is_approved = True
        comment.save()
        order.has_comment = False
        order.save()
    messages.success(request, "Comment approved successfully.")
    return redirect('admin_dashboard')

# HTMX endpoints
@require_http_methods(["GET"])
def htmx_get_services(request):
    """
    Returns service options for a given category.
    """
    category_id = request.GET.get('category')
    if not category_id:
        return HttpResponse('')
    
    services = Service.objects.filter(category_id=category_id)
    context = {'services': services}
    return render(request, 'htmx/service_options.html', context)

@require_http_methods(["GET"])
def htmx_get_service_details(request):
    """
    Returns a snippet of HTML with price and delivery details for a given service.
    """
    service_id = request.GET.get('service')
    service = None
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            pass # Service not found, template will handle with N/A
    
    context = {'service': service}
    return render(request, 'htmx/service_details.html', context)

@require_http_methods(["POST"])
def htmx_add_item(request, order_id):
    """
    Adds a new OrderItem to an existing Order.
    """
    order = get_object_or_404(Order, id=order_id)
    form = AddItemForm(request.POST)
   

    if form.is_valid():
        try:
            service = form.cleaned_data['service']
            name = form.cleaned_data['name']
            color = form.cleaned_data['color']
            
            # Calculate price and delivery time from the selected service
           
            price = service.price

            delivery_time_days = service.delivery_time_days
            
            # Create and save the new OrderItem
            new_item = OrderItem.objects.create(
                order=order,
                service=service,
                name=name,
                color=color,
                price=price,
                delivery_time_days=delivery_time_days
            )
            
            # Return the new item row to be appended to the table
            # return render(request, 'htmx/item_table_row.html', {'item': new_item})
        
            response = render(request, 'htmx/item_table_row.html', {'item': new_item})
            response['HX-Trigger'] = 'refresh-summary'
            return response


            # After successful creation, redirect to the same page to force a full reload
            # return redirect('admin_review_request', order_id=order.id)

        except KeyError as e:
            logger.error(f"KeyError in htmx_add_item: {e}. Form data: {request.POST}")
            return HttpResponseBadRequest("Form data is missing required fields. Please ensure all inputs are filled.")
    else:
        logger.error(f"Form validation failed in htmx_add_item. Errors: {form.errors}")
        return HttpResponseBadRequest(render_to_string('htmx/add_item_errors.html', {'errors': form.errors}))
    
@require_http_methods(["GET", "POST"])
def htmx_edit_item(request, item_id):
    """
    Handles editing of an existing OrderItem via HTMX.
    """
    item = get_object_or_404(OrderItem, id=item_id)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return render(request, 'htmx/item_table_row.html', {'item': item})
        else:
            return HttpResponseBadRequest(render_to_string('htmx/add_item_errors.html', {'errors': form.errors}))
    else:
        form = OrderItemForm(instance=item)
        return render(request, 'htmx/edit_item_form.html', {'form': form, 'item': item})

@require_http_methods(["DELETE"])
def htmx_delete_item(request, item_id):
    """
    Deletes an existing OrderItem.
    """
    item = get_object_or_404(OrderItem, id=item_id)
    item.delete()
    return HttpResponse(status=200, headers={'HX-Trigger': 'refresh-summary'})

@require_http_methods(["GET"])
def htmx_get_order_summary(request, order_id):
    """
    Returns an updated order summary snippet.
    """
    order = get_object_or_404(Order, id=order_id)
    
    total_items = order.items.count()
    total_price = order.items.aggregate(total=Sum('price'))['total'] or 0
    
    # Calculate earliest possible delivery date
    delivery_date = None
    if order.items.exists():
        max_delivery_days = order.items.all().order_by('-delivery_time_days').first().delivery_time_days
        delivery_date = order.created_at.date() + timedelta(days=max_delivery_days)

    summary = {
        'total_items': total_items,
        'total_price': total_price,
        'delivery_date': delivery_date
    }
    
    context = {'summary': summary}
    return render(request, 'htmx/order_summary.html', context)

@require_http_methods(["POST"])
def htmx_send_invoice1(request, order_id):
    """
    Simulates sending an invoice and returns a success message.
    """
    order = get_object_or_404(Order, id=order_id)
    order.status = 'in_progress' # Mark as in progress after invoicing
    order.save()
    
    return render(request, 'htmx/invoice_sent_message.html')
@require_http_methods(["POST"])
def htmx_send_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # order.status = 'in_progress' # Mark as in progress after invoicing
    # order.save()

    items = order.items.all()
    if not items:
        return HttpResponse("No items to invoice.", status=400)

    # Calculate summary details
    total_price = sum(item.price for item in items)
    if items:
        max_delivery_days = max(item.delivery_time_days for item in items)
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
        # 'customer_name': order.customer.get_full_name() or order.customer.username,
        'customer_name': order.customer_name or order.customer.email,
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
    # total_price = sum(item.service.price for item in items)
    total_price = sum(item.price for item in items)
    print ("Total Price:", total_price)
    
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
            "reference_id": str(order.id), 
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
        return redirect('homepage')

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
        # order_id_from_paypal = response.json()['purchase_units'][0]['reference_id']
        # order = get_object_or_404(Order, pk=order_id_from_paypal)
        
        order_id_from_paypal = response.json()['purchase_units'][0].get('reference_id')
        if not order_id_from_paypal:
            messages.error(request, "Order reference not found in PayPal response.")
            return redirect('homepage')
        
        
        # Validate that the reference_id is a valid UUID before trying to look it up
        try:
            UUID(order_id_from_paypal)
        except ValueError:
            messages.error(request, f"Invalid order reference received from PayPal: {order_id_from_paypal}.")
            return redirect('homepage')
        print ("Order ID from PayPal:", order_id_from_paypal)
        order = get_object_or_404(Order, pk=order_id_from_paypal)
        order.status = 'paid'
        order.save()

        messages.success(request, "Your payment was successful!")
        return render(request, 'paypal_success.html')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error capturing PayPal payment: {e}")
        messages.error(request, "There was an issue processing your payment. Please contact support.")
        return redirect('homepage')


def paypal_cancel(request):
    """Handles a canceled PayPal payment."""
    messages.warning(request, "Your payment was canceled.")
    return render(request, 'paypal_cancel.html')





def stripe_success(request):
    """ Handles successful Stripe payments. """
    # You may want to get the order ID from the session or request parameters
    # and update the order status here.
    return render(request, 'stripe_success.html')

def stripe_cancel(request):
    """ Handles canceled Stripe payments. """
    return render(request, 'stripe_cancel.html')
