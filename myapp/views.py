from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.forms import modelformset_factory
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Max
import uuid
from django.shortcuts import render, get_object_or_404
from .models import Service
# ... other imports

from django.shortcuts import get_object_or_404
from .models import Service
from django.http import HttpResponse


from .models import CustomerRequest, LaundryItem, WorkflowHistory, CustomUser, Service
from .forms import ServiceRequestForm, AdminItemForm, CustomUserCreationForm
from .utils import generate_qr_base64

from django.shortcuts import get_object_or_404
from .models import Service

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import F, Sum, Max
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import CustomerRequest, LaundryItem, Service, Category, ServiceType
from .forms import LaundryItemForm
from .utils import is_admin

import stripe
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import F, Sum, Max
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import CustomerRequest, LaundryItem, Service, Category, ServiceType
from .forms import LaundryItemForm, CommentForm
from .utils import is_admin

from django.shortcuts import get_object_or_404
from .models import LaundryItem
from .forms import AdminItemForm
from django.contrib.auth.decorators import user_passes_test

import stripe
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import F, Sum, Max
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from .models import CustomerRequest, LaundryItem, Service, Category, ServiceType
from .forms import LaundryItemForm, CommentForm
from .utils import is_admin

import stripe
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import F, Sum, Max
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from .models import CustomerRequest, LaundryItem, Service, Category, ServiceType
from .forms import LaundryItemForm, CommentForm
from .utils import is_admin


# import paypalrestsdk
import paypalrestsdk
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import F, Sum, Max
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from .models import CustomerRequest, LaundryItem, Service, Category, ServiceType
from .forms import LaundryItemForm, CommentForm
from .utils import is_admin

# Configure PayPal SDK
# Note: You should set PAYPAL_MODE, PAYPAL_CLIENT_ID, and PAYPAL_CLIENT_SECRET
# in your settings.py file.
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})







# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# ... other imports
# A custom decorator to restrict access to admin users.
def is_admin(user):
    return user.is_authenticated and user.is_staff

# ==============================================================================
#  Customer-facing Views
# ==============================================================================

def home(request):
    """
    Renders the home page.
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
def service_request(request):
    """
    Allows a customer to submit a new laundry service request.
    """
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.user = request.user
            new_request.save()
            send_mail(
                'Laundry Service Request Confirmation',
                'Your request has been received. A dispatch agent will visit shortly.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            return redirect('order_detail', order_id=new_request.id)
    else:
        initial_data = {
            'address': request.user.address,
            'contact_number': request.user.phone_number,
        }
        form = ServiceRequestForm(initial=initial_data)
    return render(request, 'customer_order.html', {'form': form})

@login_required
def order_detail1(request, order_id):
    """
    Displays the details of a specific order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})

@login_required
def order_review(request, order_id):
    """
    Allows a customer to review a finalized order from the admin.
    """
    order = get_object_or_404(CustomerRequest, id=order_id, user=request.user)
    context = {'order': order}
    return render(request, 'customer_review.html', context)

@require_POST
@login_required
def accept_order(request, order_id):
    """
    Handles a customer accepting a finalized order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id, user=request.user)
    if not order.batch_id:
        order.batch_id = str(uuid.uuid4())[:8].upper()
    order.status = 'accepted'
    order.save()
    return render(request, 'batch_id_display.html', {'batch_id': order.batch_id})

@require_POST
@login_required
def comment_order(request, order_id):
    """
    Allows a customer to leave a comment on a finalized order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id, user=request.user)
    comment = request.POST.get('comment')
    order.comment = comment
    order.status = 'commented'
    order.save()
    return render(request, 'comment_success.html')

# ==============================================================================
#  Admin-facing Views
# ==============================================================================


@user_passes_test(is_admin)
def admin_dashboard1(request):
    """
    Displays the main admin dashboard with categorized requests.
    """
    pending_requests = CustomerRequest.objects.filter(status='pending_review')
    in_progress_orders = CustomerRequest.objects.filter(status='in_progress')
    commented_orders = CustomerRequest.objects.filter(status='commented')
    return render(request, 'admin_dashboard.html', {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
    })

@user_passes_test(is_admin)
def admin_review_request1(request, order_id):
    """
    Allows an admin to review and finalize a customer's request.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    AdminItemFormSet = modelformset_factory(
        LaundryItem,
        form=AdminItemForm,
        extra=5,
        fields=('name', 'service', 'color')
    )
    if request.method == 'POST':
        formset = AdminItemFormSet(request.POST, queryset=order.items.all())
        if formset.is_valid():
            order.items.all().delete()
            for form in formset:
                if form.cleaned_data:
                    item = form.save(commit=False)
                    item.request = order
                    item.save()
            total_price = sum(item.price for item in order.items.all() if item.price is not None)
            max_delivery_time = order.items.all().aggregate(Max('service__delivery_time_days'))['service__delivery_time_days__max']
            send_mail(
                'Your Laundry Order is Ready for Review',
                f'Please review your order details. Total price: ${total_price}. Expected delivery date: {max_delivery_time} days. Use this link: http://your-domain.com/order-review/{order_id}/',
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=False,
            )
            return redirect('admin_dashboard')
    else:
        formset = AdminItemFormSet(queryset=order.items.all())
    return render(request, 'admin_review_request.html', {
        'order': order,
        'item_forms': formset
    })

@user_passes_test(is_admin)
def generate_qr_codes(request, order_id):
    """
    Generates QR codes for each item in an order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    for item in order.items.all():
        if not item.qr_code_base64:
            qr_data = f'laundry-item-{item.id}'
            item.qr_code_base64 = generate_qr_base64(qr_data)
            item.save()
    return redirect('admin_review_request', order_id=order_id)

@user_passes_test(is_admin)
def update_workflow_stage(request, item_id):
    """
    Updates the workflow stage of a single item.
    """
    item = get_object_or_404(LaundryItem, id=item_id)
    new_stage = request.POST.get('stage')
    if new_stage in dict(item.WORKFLOW_STAGES):
        item.current_stage = new_stage
        item.save()
        WorkflowHistory.objects.create(item=item, stage=new_stage)
        order = item.request
        if all(i.current_stage == 'ready_for_pickup' for i in order.items.all()):
            order.status = 'ready_for_delivery'
            order.save()
            send_mail(
                'Your Laundry Order is Ready',
                f'Order {order.batch_id} is ready for pickup or dispatch.',
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=False,
            )
    return render(request, 'htmx/workflow_status.html', {'item': item})

@user_passes_test(is_admin)
def admin_approve_comment(request, order_id):
    """
    Allows an admin to approve a customer's comment and accept the order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    order.batch_id = str(uuid.uuid4())[:8].upper()
    order.status = 'accepted'
    order.save()
    return redirect('admin_dashboard')


# In your views.py file

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def update_item_details(request, item_id):
    item = get_object_or_404(LaundryItem, id=item_id)
    if request.method == 'POST':
        form = AdminItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            # Assuming you are using HTMX to update a single row
            return render(request, 'htmx/item_row.html', {'item': item})
    else:
        form = AdminItemForm(instance=item)
    return render(request, 'htmx/item_edit_form.html', {'form': form, 'item': item})



# ==============================================================================
#  HTMX-specific Views
# ==============================================================================

def htmx_get_service_details1(request, service_id):
    """
    HTMX view to return a template fragment with price and delivery time.
    """
    service = get_object_or_404(Service, id=service_id)
    return render(request, 'htmx/service_details.html', {'service': service})

def htmx_order_summary(request, order_id):
    """
    HTMX view to render a summary of an order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    return render(request, 'htmx/order_summary.html', {'order': order})

def htmx_comment_form(request, order_id):
    """
    HTMX view to render a comment form.
    """
    return render(request, 'htmx/comment_form.html', {'order_id': order_id})

def htmx_submit_comment(request, order_id):
    """
    HTMX view to submit a comment.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    order.comment = request.POST.get('comment')
    order.status = 'commented'
    order.save()
    return render(request, 'htmx/comment_submitted.html')




# Eniyan
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import F, Sum, Max
from datetime import date, timedelta

from .models import CustomerRequest, LaundryItem, Service, Category, ServiceType
from .forms import LaundryItemForm
from .utils import is_admin


# Helper function to calculate order summary
def get_order_summary(order):
    total_price = order.items.aggregate(total=Sum('service__price'))['total'] or 0
    # Corrected: Use Max() to get the latest delivery time
    latest_delivery_days = order.items.aggregate(max_days=Max('service__delivery_time_days'))['max_days']
    
    delivery_date = None
    if latest_delivery_days:
        delivery_date = date.today() + timedelta(days=latest_delivery_days)
        
    return {
        'total_items': order.items.count(),
        'total_price': total_price,
        'delivery_date': delivery_date
    }

@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Renders the admin dashboard with lists of pending, in-progress, and commented requests.
    """
    pending_requests = CustomerRequest.objects.filter(status='pending_review')
    in_progress_orders = CustomerRequest.objects.filter(status='Accepted')
    commented_orders = CustomerRequest.objects.filter(comment__isnull=False)

    context = {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
    }
    return render(request, 'admin_dashboard.html', context)




@user_passes_test(is_admin)
def admin_review_request(request, order_id):
    """
    Renders the main admin review page with a single form to add a new item
    and a list of existing items.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    form = LaundryItemForm()
    all_categories = Category.objects.all()
    
    context = {
        'order': order,
        'form': form,
        'all_categories': all_categories,
        'order_summary': get_order_summary(order)
    }
    return render(request, 'admin_review_request.html', context)

@require_POST
@user_passes_test(is_admin)
def htmx_add_item(request, order_id):
    """
    Handles HTMX POST request to add a new laundry item to an order.
    Returns a rendered table row for the newly created item.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    form = LaundryItemForm(request.POST)

    if form.is_valid():
        new_item = form.save(commit=False)
        new_item.request = order
        new_item.save()
        
        # Return the new table row to be appended to the list
        return render(request, 'htmx/item_table_row.html', {'item': new_item})
    
    # If the form is not valid, you can return a response with errors
    return HttpResponse("<p class='text-danger'>Form is not valid.</p>", status=400)


@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def htmx_edit_item(request, item_id):
    """
    Handles HTMX GET/POST requests for editing a laundry item.
    GET: Returns a form to edit the item.
    POST: Saves the changes and returns the updated table row.
    """
    item = get_object_or_404(LaundryItem, id=item_id)
    all_categories = Category.objects.all()
    
    if request.method == 'POST':
        form = LaundryItemForm(request.POST, instance=item)
        if form.is_valid():
            updated_item = form.save()
            return render(request, 'htmx/item_table_row.html', {'item': updated_item})
        else:
            # Pass the form with errors back to the template
            return render(request, 'htmx/edit_item_form_row.html', {'form': form, 'item': item, 'all_categories': all_categories})
    else: # GET request
        form = LaundryItemForm(instance=item)
        return render(request, 'htmx/edit_item_form_row.html', {'form': form, 'item': item, 'all_categories': all_categories})


@require_http_methods(["DELETE"])
@user_passes_test(is_admin)
def htmx_delete_item(request, item_id):
    """
    Handles HTMX DELETE request to remove a laundry item.
    """
    item = get_object_or_404(LaundryItem, id=item_id)
    item.delete()
    return HttpResponse(status=200) # Returns an empty response with a success status code


# Eniyan2
@require_POST
@user_passes_test(is_admin)
def htmx_send_invoice(request, order_id):
    """
    Calculates the final summary, updates the order, and sends the invoice to the customer.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    # Calculate order summary
    summary = get_order_summary(order)
    order.total_price = summary['total_price']
    order.delivery_date = summary['delivery_date']
    order.status = 'pending_review'
    order.save()

    # Get all items related to the order
    items = order.items.all()
    
    # Render the invoice email HTML content
    email_html_content = render_to_string('htmx/invoice_email.html', {
        'order': order,
        'summary': summary,
        'items': items,
        'customer_name': request.user.first_name or "Valued Customer"
    })
    
    try:
        subject = f"Invoice for your Laundry Order #{order.id}"
        from_email = settings.DEFAULT_FROM_EMAIL
        # from_email="ayodelefestusng@gmail.com"
        # Using a dummy email as we don't have a real customer model with an email field
        recipient_list = ["ayodelefestusng@gmail.com"]
        
        # Send the email
        send_mail(
            subject,
            '',  # Empty message body as we're using html_message
            from_email,
            recipient_list,
            html_message=email_html_content,
        )
        
        # Return success message to the frontend
        return render(request, 'htmx/invoice_sent_message.html')
    except Exception as e:
        # Return an error message to the frontend if email sending fails
        return HttpResponse(f"<div class='alert alert-danger mt-3'>Failed to send invoice: {e}</div>", status=500)


def htmx_get_services(request):
    """
    HTMX view to fetch services based on the selected category.
    """
    category_id = request.GET.get('category')
    services = Service.objects.filter(category_id=category_id).order_by('service_type') if category_id else Service.objects.none()
    return render(request, 'htmx/service_options.html', {'services': services})

def htmx_get_service_details(request):
    """
    HTMX view to fetch the service price and delivery time.
    """
    service_id = request.GET.get('service')
    service = get_object_or_404(Service, id=service_id) if service_id else None
    return render(request, 'htmx/service_details.html', {'service': service})

def htmx_get_order_summary(request, order_id):
    """
    HTMX view to fetch and render the live order summary.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    summary = get_order_summary(order)
    return render(request, 'htmx/order_summary.html', {'summary': summary})


@csrf_exempt
def stripe_checkout1(request, order_id):
    """
    Creates a Stripe Checkout Session for the order and redirects the user to it.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    # In a real application, you would create a list of line items from the order.
    # For this example, we'll create a single line item.
    line_item = {
        'price_data': {
            'currency': 'usd',
            'product_data': {
                'name': f'Laundry Order #{order.id}',
            },
            'unit_amount': int(order.total_price * 100), # Stripe requires amount in cents
        },
        'quantity': 1,
    }
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[line_item],
            mode='payment',
            success_url=request.build_absolute_uri('stripe/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('stripe/cancel/'),
            client_reference_id=order.id,
        )
        return redirect(checkout_session.url, code=303)
    except stripe.error.StripeError as e:
        return HttpResponse(f"An error occurred during payment processing: {e}", status=400)

@csrf_exempt
def stripe_checkout(request, order_id):
    """
    Creates a Stripe Checkout Session for the order and redirects the user to it.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    # Construct the absolute URLs using the new SITE_URL setting
    success_url = settings.SITE_URL + reverse('stripe_success') + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = settings.SITE_URL + reverse('stripe_cancel')
    
    # In a real application, you would create a list of line items from the order.
    # For this example, we'll create a single line item.
    line_item = {
        'price_data': {
            'currency': 'usd',
            'product_data': {
                'name': f'Laundry Order #{order.id}',
            },
            'unit_amount': int(order.total_price * 100), # Stripe requires amount in cents
        },
        'quantity': 1,
    }
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[line_item],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=order.id,
        )
        return redirect(checkout_session.url, code=303)
    except stripe.error.StripeError as e:
        return HttpResponse(f"An error occurred during payment processing: {e}", status=400)



def add_comment1(request, order_id):
    """
    View for the customer to leave a comment on the order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # Process the comment, e.g., save it to the database
            # This is a placeholder for the actual comment saving logic
            comment_text = form.cleaned_data['comment']
            # You would likely save this comment to a Comment model
            
            return render(request, 'comment_success.html') # Redirect to a success page
    else:
        form = CommentForm()
    
    return render(request, 'add_comment.html', {'form': form, 'order': order})

def stripe_success(request):
    """
    Handles the redirect from a successful Stripe payment.
    Updates the order status and renders the success page.
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        return HttpResponse("Session ID not found.", status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        order_id = session.client_reference_id
        order = get_object_or_404(CustomerRequest, id=order_id)
        
        # Get the payment intent ID from the session. This is the official payment reference.
        payment_intent_id = session.payment_intent
        
        # Update order status to 'Accepted' and save the payment reference
        order.status = 'Accepted'
        # IMPORTANT: You must add a 'payment_reference' field to your CustomerRequest model for this to work.
        order.payment_reference = payment_intent_id
        order.save()
        
        return render(request, 'stripe_success.html')
    
    except stripe.error.StripeError as e:
        return HttpResponse(f"An error occurred: {e}", status=500)
    except Exception as e:
        return HttpResponse("An internal server error occurred.", status=500)

def stripe_cancel(request):
    """
    Handles the redirect from a canceled Stripe payment.
    Renders the cancel page.
    """
    return render(request, 'stripe_cancel.html')



# PayPal

def paypal_checkout(request, order_id):
    """
    Creates a PayPal payment and redirects the user to the approval URL.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            # Use SITE_URL to build absolute URLs
            "return_url": settings.SITE_URL + reverse('paypal_success') + '?orderId=' + str(order.id),
            "cancel_url": settings.SITE_URL + reverse('paypal_cancel') + '?orderId=' + str(order.id)},
        "transactions": [{
            "amount": {
                "total": f"{order.total_price:.2f}",
                "currency": "USD" },
            "description": f"Laundry Order #{order.id}"}]})
    
    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    else:
        return HttpResponse(f"PayPal payment creation failed: {payment.error}", status=400)

def paypal_success(request):
    """
    Handles the redirect from a successful PayPal payment.
    Verifies the payment and updates the order status.
    """
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    order_id = request.GET.get('orderId')
    
    payment = paypalrestsdk.Payment.find(payment_id)

    try:
        if payment.execute({"payer_id": payer_id}):
            order = get_object_or_404(CustomerRequest, id=order_id)
            order.status = 'Accepted'
            order.payment_reference = payment_id
            order.save()
            return render(request, 'paypal_success.html')
        else:
            return HttpResponse(f"PayPal payment failed: {payment.error}", status=400)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)

def paypal_cancel(request):
    """
    Handles the redirect from a canceled PayPal payment.
    Renders the cancel page.
    """
    return render(request, 'paypal_cancel.html')





def add_comment(request, order_id):
    """
    View for the customer to leave a comment on the order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # Process the comment, e.g., save it to the database
            # This is a placeholder for the actual comment saving logic
            comment_text = form.cleaned_data['comment']
            # You would likely save this comment to a Comment model
            
            return render(request, 'comment_success.html') # Redirect to a success page
    else:
        form = CommentForm()
    
    return render(request, 'add_comment.html', {'form': form, 'order': order})

def order_detail(request, order_id):
    """
    Placeholder view for displaying order details.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    return HttpResponse(f"Order details for {order.id}")

