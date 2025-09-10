from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from .utils import generate_qr_base64
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from .forms import CustomUserCreationForm

def home(request):
    return HttpResponse("Welcome to My Laundry Service!")

# laundry/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    return render(request, 'laundry/profile.html')

# def submit_order(request):
#     # Parse items, calculate delivery, save order
#     order = Order.objects.create(customer=request.user)
#     # Add items, calculate delivery
#     order.expected_delivery = calculate_expected_delivery(order.items.all())
#     order.save()
#     send_confirmation_email(order)
#     return render(request, 'orders/confirmation.html', {'order': order})

from django.core.mail import send_mail

def send_confirmation_email(order):
    send_mail(
        subject="Laundry Request Received",
        message=f"Your order has been received. Dispatch will visit shortly.",
        recipient_list=[order.customer.email],
        from_email="noreply@laundry.com"
    )




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Max
import qrcode
import uuid
import os
from .models import CustomerRequest, LaundryItem, WorkflowHistory
from .forms import ServiceRequestForm, AdminItemForm

# A custom decorator to restrict access to admin users.
def is_admin(user):
    return user.is_staff

# Customer-facing Views

@login_required
def service_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.user = request.user
            new_request.save()
            # Send confirmation email
            send_mail(
                'Laundry Service Request Confirmation',
                'Your request has been received. A dispatch agent will visit shortly.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            return redirect('order_detail', new_request.id)
    else:
        form = ServiceRequestForm()
    return render(request, 'laundry/customer_order.html', {'form': form})



# laundry/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import CustomerRequest

# ... other views

def order_detail(request, order_id):
    """
    Displays the details of a specific order.
    """
    order = get_object_or_404(CustomerRequest, id=order_id, user=request.user)
    return render(request, 'laundry/order_detail.html', {'order': order})


def order_review(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    context = {'order': order}
    return render(request, 'laundry/customer_review.html', context)

def accept_order(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    if not order.batch_id:
        order.batch_id = str(uuid.uuid4())[:8].upper()
        order.status = 'accepted'
        order.save()
    return render(request, 'laundry/batch_id_display.html', {'batch_id': order.batch_id})


@require_POST
def comment_order(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    if request.method == 'POST':
        comment = request.POST.get('comment')
        order.comment = comment
        order.status = 'commented'
        order.save()
        return render(request, 'laundry/comment_success.html')
    return render(request, 'laundry/comment_form.html')




# HTMX-specific Views

def htmx_order_summary(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    return render(request, 'laundry/htmx/order_summary.html', {'order': order})

def htmx_comment_form(request, order_id):
    return render(request, 'laundry/htmx/comment_form.html', {'order_id': order_id})

def htmx_submit_comment(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    order.comment = request.POST.get('comment')
    order.status = 'commented'
    order.save()
    return render(request, 'laundry/htmx/comment_submitted.html')

# Admin-facing Views

@user_passes_test(is_admin)
def admin_dashboard(request):
    pending_requests = CustomerRequest.objects.filter(status='pending_review')
    in_progress_orders = CustomerRequest.objects.filter(status='in_progress')
    commented_orders = CustomerRequest.objects.filter(status='commented')
    return render(request, 'laundry/admin_dashboard.html', {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
    })

@user_passes_test(is_admin)
def admin_review_request(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    if request.method == 'POST':
        item_forms = [AdminItemForm(request.POST, prefix=str(i), instance=item) for i, item in enumerate(order.items.all())]
        if all(form.is_valid() for form in item_forms):
            for form in item_forms:
                form.save()
            
            # Calculate overall delivery time
            max_delivery_time = order.items.all().aggregate(Max('delivery_time_days'))['delivery_time_days__max']
            # Re-send email to customer for review
            send_mail(
                'Your Laundry Order is Ready for Review',
                f'Please review your order details. Expected delivery date: {max_delivery_time} days. Use this link: http://127.0.0.1:8000/order-review/{order_id}/',
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=False,
            )

                    # Generate QR codes for all items
            for item in order.items.all():
                if not item.qr_code_base64:
                    qr_data = f'laundry-item-{item.id}'
                    item.qr_code_base64 = generate_qr_base64(qr_data)
                    item.save()
            return redirect('admin_dashboard')
    else:
        item_forms = [AdminItemForm(prefix=str(i)) for i in range(5)] # Example, adjust as needed
    return render(request, 'laundry/admin_review_request.html', {'order': order, 'item_forms': item_forms})




@user_passes_test(is_admin)
def update_item_details(request, item_id):
    item = get_object_or_404(LaundryItem, id=item_id)
    if request.method == 'POST':
        form = AdminItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            # HTMX response to update the item row
            return render(request, 'laundry/htmx/item_row.html', {'item': item})
    else:
        form = AdminItemForm(instance=item)
    return render(request, 'laundry/htmx/item_edit_form.html', {'form': form, 'item': item})

@user_passes_test(is_admin)
def generate_qr_codes(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    for item in order.items.all():
        if not item.qr_code_data:
            qr_data = f'laundry-item-{item.id}'
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            # Save QR code image (consider a storage solution like S3)
            img_path = os.path.join(settings.MEDIA_ROOT, 'qrcodes', f'item-{item.id}.png')
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            img.save(img_path)
            item.qr_code_data = qr_data
            item.save()
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def update_workflow_stage(request, item_id):
    item = get_object_or_404(LaundryItem, id=item_id)
    new_stage = request.POST.get('stage')
    if new_stage in dict(item.WORKFLOW_STAGES):
        item.current_stage = new_stage
        item.save()
        WorkflowHistory.objects.create(item=item, stage=new_stage)
        # Check if all items are completed
        order = item.request
        if all(i.current_stage == 'ready_for_pickup' for i in order.items.all()):
            # Send completion notification
            send_mail(
                'Your Laundry Order is Ready',
                f'Order {order.batch_id} is ready for pickup or dispatch.',
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=False,
            )
            order.status = 'ready_for_delivery'
            order.save()
    return render(request, 'laundry/htmx/workflow_status.html', {'item': item})

@user_passes_test(is_admin)
def admin_approve_comment(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    order.batch_id = str(uuid.uuid4())[:8].upper()
    order.status = 'accepted'
    order.save()
    return redirect('admin_dashboard')




def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'laundry/register.html', {'form': form})





@require_POST
def accept_order(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id, user=request.user)
    if not order.batch_id:
        order.batch_id = str(uuid.uuid4())[:6].upper()
        order.status = 'accepted'
        order.save()
    return render(request, 'laundry/batch_id_display.html', {'batch_id': order.batch_id})

