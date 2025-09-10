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
def order_detail(request, order_id):
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
def admin_dashboard(request):
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


# In your myapp/views.py file

from django.shortcuts import get_object_or_404
from .models import LaundryItem
from .forms import AdminItemForm
from django.contrib.auth.decorators import user_passes_test

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




# myapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.forms import modelformset_factory
from .models import CustomerRequest, LaundryItem, Service, Category
from .forms import AdminItemForm
# ... (other imports)

def is_admin(user):
    return user.is_authenticated and user.is_staff
# myapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.forms import modelformset_factory
from django.db.models import Max
from django.forms import formset_factory
import uuid

from .models import CustomerRequest, LaundryItem, WorkflowHistory, Service, Category
from .forms import ServiceRequestForm, AdminItemForm, CustomUserCreationForm
from .utils import generate_qr_base64

# ... (all other existing views)

@user_passes_test(is_admin)
def admin_review_request(request, order_id):
    order = get_object_or_404(CustomerRequest, id=order_id)
    
    AdminItemFormSet = modelformset_factory(
        LaundryItem,
        form=AdminItemForm,
        extra=0, # Initially we show existing forms, not extra empty ones
        fields=('category', 'service', 'name', 'color'),
        can_delete=True
    )

    if request.method == 'POST':
        formset = AdminItemFormSet(request.POST, queryset=order.items.all())
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.request = order
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            return redirect('admin_dashboard')
    else:
        formset = AdminItemFormSet(queryset=order.items.all())
    
    return render(request, 'admin_review_request.html', {
        'order': order,
        'formset': formset
    })



@user_passes_test(is_admin)
def htmx_add_item_form1(request):
    """
    HTMX view to render a new empty form row.
    """
    
    AdminItemFormSet = modelformset_factory(
        LaundryItem,
        form=AdminItemForm,
        extra=1,
        fields=('category', 'service', 'name', 'color'),
        can_delete=True
    )
    # Create an empty form instance
    form = AdminItemFormSet(prefix='item_form')
    
    form = form.empty_form # Get the empty form from the formset
    
    return render(request, 'htmx/item_form_row.html', {'form': form})


@user_passes_test(is_admin)
def htmx_add_item_form(request):
    """
    HTMX view to render a new empty form row.
    """
    AdminItemFormSet = modelformset_factory(
        LaundryItem,
        form=AdminItemForm,
        extra=1,
        fields=('category', 'service', 'name', 'color'),
        can_delete=True
    )
    print("aluke")
    formset = AdminItemFormSet(prefix='form')  # Match the main formset prefix
    form = formset.empty_form


    return render(request, 'htmx/item_form_row.html', {'form': form})


def htmx_get_services(request):
    """
    HTMX view to fetch services based on the selected category.
    """
    # Dynamically find the category field from GET params
    category_id = None
    for key in request.GET:
        if key.endswith('-category'):
            category_id = request.GET.get(key)
            break

    print("Fetched Category ID:", category_id)

    services = Service.objects.filter(category_id=category_id).order_by('service_type') if category_id else Service.objects.none()

    return render(request, 'htmx/service_options.html', {'services': services})





# myapp/views.py

def htmx_get_service_details(request):
    """
    HTMX view to return a template fragment with price and delivery time.
    """
    service_id = None

    # Dynamically find the service field from GET params
    for key in request.GET:
        if key.endswith('-service'):
            service_id = request.GET.get(key)
            break

    if service_id:
        service = get_object_or_404(Service, id=service_id)
        return render(request, 'htmx/service_details.html', {'service': service})

    return HttpResponse("N/A<br>N/A")
    """
    HTMX view to return a template fragment with price and delivery time.
    """
    service_id = request.GET.get('item_form-__prefix__-service')
    if not service_id:
        # Fallback for existing forms
        service_id = request.GET.get('item_form-0-service')
    
    if service_id:
        service = get_object_or_404(Service, id=service_id)
        return render(request, 'htmx/service_details.html', {'service': service})
    
    return HttpResponse("")