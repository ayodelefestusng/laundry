import logging
from math import log
import uuid
import json
import hmac
import hashlib
from chromadb import logger
import requests
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, send_mail
from django.db import IntegrityError
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import strip_tags
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from .forms import (
AddItemForm, CommentForm, OrderForm, OrderItemForm,CustomUserChangeForm,RegistrationForm,
CustomUserCreationForm,PasswordSetupForm,PasswordChangeForm,PasswordSetupForm,
) 
from .models import Comment, Order, OrderItem, Package, ServiceCategory, Payment, CustomUser, PremiumClient, QR, WorkflowHistory, WorkflowInstance, WorkflowStage, Tenant
from .utils import is_admin

from .models import log_with_context


# User-facing views
@csrf_exempt
def homepage(request):
    """
    Renders the homepage.
    """
    logger.info(f"User {request.user} accessed the homepage.")
    return render(request, 'homepage.html')

@csrf_exempt
def registerv1(request):
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



def check_username(request):

    if request.method == "GET":
        return HttpResponse("Oya")
    elif request.method == "POST":
        email = request.POST.get('email')
        print("AJADI", email)

        if email and CustomUser.objects.filter(email=email).exists():
            return HttpResponse("This username already exists")
        return HttpResponse("")  # Empty response if email is available or not provided

@csrf_exempt
def register(request):
    # logger.info(f"User {request.POST} accessed the register page.")
    logger.info(f"User {request.POST} accessed the register VIEW")
    if request.method == "POST":
        logger.info(f"User {request.POST} accessed the register page.")
        form = RegistrationForm(request.POST)
        if form.is_valid():
            logger.info(f"User {request.POST} accessed the register page.")
            user = form.save(commit=False)
            user.set_password(None)  # User sets password later
            user.save()

            token = default_token_generator.make_token(user)
            link = request.build_absolute_uri(reverse("laundry:setup_password", args=[user.pk, token]))
            # link = f"{settings.SITE_DOMAIN}{reverse('users:setup_password', args=[user.pk, token])}"

            # send_mail(
            #     "Set Your Password",
            #     f"Click the link to set your password: {link}",
            #     settings.DEFAULT_FROM_EMAIL,
            #     [user.email],
            # )
            # Render HTML template
            html_content = render_to_string("emails/register_email.html", {
                    "user": user,
                    "ceate_link": link,
    
                })
            text_content = strip_tags(html_content)

            # Send email
            msg = EmailMultiAlternatives(
                subject="Set Your Password",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            messages.success(request, "Registration successful! Please check your email to set your password.")

            # return render(request, "myapp/registration_success.html", {"email": user.email})
            return render(request, "registration/password_setup_sent.html", {"email": user.email})
    else:
        logger.info(f"User {request.POST} accessed the register page.")
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})

@csrf_exempt
def setup_password(request, user_id, token):
    user = CustomUser.objects.get(pk=user_id)
    if default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = PasswordSetupForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect("laundry:login")
                # return HttpResponseRedirect("login")
        else:
            form = PasswordSetupForm(user)
        return render(request, "registration/setup_password.html", {"form": form})
    else:
        return render(request, "registration/error.html", {"message": "Invalid token"})

@csrf_exempt
def password_reset_request(request):
    logger.info(f"User {request.POST} accessed the password reset VIEW")    
    if request.method == "POST":
        logger.info(f"User {request.POST} accessed the password reset page.")
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = CustomUser.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                link = request.build_absolute_uri(reverse("laundry:setup_password", args=[user.pk, token]))
                
                # send_mail(
                #     "Reset Your Password",
                #     f"Click the link to reset your password: {link}",
                #     "admin@example.com",
                #     [email],
                # )
                  # Render HTML template
                html_content = render_to_string("registration/password_reset_email.html", {
                    "user": user,
                    "reset_link": link,
                })
                text_content = strip_tags(html_content)

                # Send email
                msg = EmailMultiAlternatives(
                    subject="Reset Your Password",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    # from_email='Dignity Concept <upwardwave.dignity@gmail.com>',
                    to=[email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            return render(request, "registration/password_reset_sent.html", {"email": email})
    else:
        logger.info(f"User {request.POST} accessed the password reset page.")
        form = PasswordResetForm()
    return render(request, "registration/password_reset.html", {"form": form})

@csrf_exempt
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = authenticate(email=request.user.email, password=form.cleaned_data["old_password"])
            if user:
                user.set_password(form.cleaned_data["new_password"])
                user.save()
                logout(request)
                return redirect("laundry:login")
            else:
                return render(request, "myapp/change_password.html", {"form": form, "error": "Incorrect password"})
    else:
        form = PasswordChangeForm()
    return render(request, "registration/change_password.html", {"form": form})

def terms_and_privacy(request):
    return render(request, 'registration/terms_and_privacy.html')



@csrf_exempt
@login_required
def custom_logout(request):
    """
    Logs the user out and redirects to the homepage.
    """
    logger.info(f"User {request.user} logged out successfully.")
    auth.logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('laundry:customer_order')


@csrf_exempt
# @login_required
def customer_order(request):
    logger.info(f"User {request.user} is placing an order.")
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            logger.info(f"Form is valid: {form.cleaned_data}")
            try:
                order = form.save(commit=False)
                # order.user = request.user
                order.save()
                logger.info(f"Order created successfully: {order}")
                messages.success(
                    request, 'Order placed successfully! We will contact you shortly.')
                send_mail(
                'Laundry Service Request Confirmation',
                'Your request has been received. A dispatch agent will visit shortly.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
                return redirect('laundry:order_detail', order_id=order.id)
            except IntegrityError:
                messages.error(
                    request, "An error occurred while placing the order. Please try again.")
    else:
        form = OrderForm()
    return render(request, 'customer_order.html', {'form': form})

def admin_dashboard(request):
    """
    Admin dashboard to view pending, in-progress, and commented orders.
    """
    logger.info(f"Admin {request.user} is viewing admin dashboard.")
    
    pending_requests = Order.objects.filter(status='pending').order_by('created_at')
    in_progress_orders = Order.objects.filter(status='in_progress').order_by('-created_at')
    commented_orders = Order.objects.filter(status='commented').order_by('-created_at')
    confirmed_orders = Order.objects.filter(status='confirmed').order_by('-created_at')
    invoiced_sent = Order.objects.filter(status='invoice_sent').order_by('-created_at')
    # Pipeline data
    items = OrderItem.objects.all()
    pipeline_counts = {}
    for item in items:
        status = item.status or 'Unknown'
        pipeline_counts[status] = pipeline_counts.get(status, 0) + 1
        
    total_items = items.count()
    escalated_items = WorkflowHistory.objects.filter(action="Escalate").values('item').distinct().count()
    rejected_items = WorkflowHistory.objects.filter(action="Reject").values('item').distinct().count()

    context = {
        'pending_requests': pending_requests,
        'in_progress_orders': in_progress_orders,
        'commented_orders': commented_orders,
        'confirmed_orders': confirmed_orders,
        'invoiced_sent': invoiced_sent,
        'pipeline_counts': pipeline_counts,
        'total_items': total_items,
        'escalated_items': escalated_items,
        'rejected_items': rejected_items,
    }
    return render(request, 'admin_dashboard.html', context)





@csrf_exempt
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
                return redirect('laundry:admin_dashboard')
            except IntegrityError:
                messages.error(
                    request, "An error occurred while placing the order. Please try again.")    
            # Redirect to the admin review page for now for testing
            
        else:
            print("Form errors:", form.errors)
        
    else:
        form = OrderForm()
    return render(request, 'customer_order.html', {'form': form})



@csrf_exempt
@login_required
def customer_dashboard(request):
    logger.info(f"User {request.user} is viewing their dashboard.")
    """
    Renders the customer dashboard with a list of their orders.
    """
    # customer_orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    customer_orders = Order.objects.all().order_by('-created_at')
    context = {'orders': customer_orders}
    logger.info(f"Customer orders: {customer_orders}")
    return render(request, 'customer_dashboard.html', context)
@csrf_exempt
@login_required
def order_detail(request, order_id):
    logger.info(f"User {request.user} is viewing order {order_id}.")
    """
    Displays the details of a specific order.
    """
    # order = get_object_or_404(Order, id=order_id, customer=request.user)
    order = get_object_or_404(Order, id=order_id)
    logger.info(f"Order details: {order}")
    context = {'order': order}
    return render(request, 'order_detail.html', context)
@csrf_exempt
@login_required
def customer_review(request, order_id):
    """
    Renders the page for a customer to review an order and add a comment.
    """
    logger.info(f"User {request.user} is reviewing order {order_id}.")
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    logger.info(f"Order details: {order}")
    return render(request, 'customer_review.html', context)
@csrf_exempt
@login_required
def accept_order(request, order_id):
    """
    Allows a customer to accept an order.
    """
    log
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'accepted'
    order.save()
    messages.success(request, "Your order has been accepted. Thank you!")
    return redirect('laundry:customer_dashboard')
@csrf_exempt
@login_required
def comment_order(request, order_id):
    """
    Allows a customer to leave a comment on their order.
    """
    logger.info(f"User {request.user} is commenting on order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.order = order
            comment.author = order.customer_email
            # comment.author = order.customer_email or request.user.email  
            comment.body = form.cleaned_data['body']
            comment.save()
            order.is_confirmed = False
            order.status = "commented"
            # order.notes=comment.body
            order.save()
            logger.info(f"Comment added successfully: {comment}")
            return redirect('laundry:comment_success')
    else:
        form = CommentForm()
    context = {'order': order, 'form': form}
    return render(request, 'add_comment.html', context)


@login_required
def confirm_order(request, order_id):
    """
    Allows a customer to leave a comment on their order.
    """
    logger.info(f"User {request.user} is confirming order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
            order.is_confirmed = True
            order.status = "confirmed"
            order.save()
            logger.info(f"Order {order_id} confirmed successfully.")
            return redirect('laundry:admin_dashboard')
    else:
        form = CommentForm()
    context = {'order': order, 'form': form}
    return render(request, 'add_comment.html', context)

def comment_success(request):
    """
    Renders a success page after a comment is submitted.
    """
    logger.info(f"User {request.user} is viewing comment success page.")
    return render(request, 'comment_success.html')

def confirm_success(request):
    """
    Renders a success page after a confirmation is submitted.
    """
    logger.info(f"User {request.user} is viewing confirm success page.")
    return render(request, 'confirm_success.html')

def assign_qr_code(request, order_id):
    """
    Assigns a QR code to an order for tracking purposes.
    """
    logger.info(f"User {request.user} is assigning a QR code to order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    if not order.qr_code:
        order.qr_code = str(uuid.uuid4())
        order.save()
        logger.info(f"QR code assigned successfully: {order.qr_code}")
    else:
        logger.info(f"Order already has a QR code: {order.qr_code}")
    return redirect('laundry:order_detail', order_id=order.id)
# Admin-facing views


@require_http_methods(["GET"])
def admin_review_request(request, order_id):
    """
    Renders the admin review page for a specific order.
    """
    logger.info(f"Admin {request.user} is reviewing order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    form = OrderItemForm()
    packages = Package.objects.all()
    categories = ServiceCategory.objects.all()
    
    context = {
        'order': order,
        'form': form,
        'packages': packages,
        'categories': categories,
    }
    return render(request, 'admin_review_request.html', context)

@require_http_methods(["POST"])
def admin_approve_comment(request, order_id):
    """
    Handles admin responses to commented orders (Approve vs Review).
    Persists admin notes into the Comment model.
    """
    try:
        logger.info(f"Admin {request.user} is processing comment for order {order_id}.")
        order = get_object_or_404(Order, id=order_id)
        
        action = request.POST.get('action')
        admin_note = request.POST.get('admin_note', '').strip()
        
        # Persist Admin Comment into the Comment model
        if admin_note:
            from myapp.models import Comment
            Comment.objects.create(
                order=order,
                actor="staff",
                body=admin_note,
                is_approved=True
            )
            logger.info(f"Admin note saved for order {order_id}.")
            
        if action == 'approve':
            customer_comment = order.comment_set.filter(actor='customer').first()
            if customer_comment:
                customer_comment.is_approved = True
                customer_comment.save()
            
            order.has_comment = False
            order.status = "confirmed"
            order.save()
            messages.success(request, "Comment approved and order confirmed successfully.")
            return redirect('laundry:admin_dashboard')
            
        elif action == 'review':
            messages.success(request, "Note saved. Initializing review mode.")
            return redirect('laundry:admin_review_request', order_id=order.id)
            
        else:
            messages.error(request, "Invalid action requested.")
            return redirect('laundry:admin_dashboard')

    except Exception as e:
        logger.error(f"Error handling admin comment for order {order_id}: {e}", exc_info=True)
        messages.error(request, "An unexpected error occurred while processing the comment.")
        return redirect('laundry:admin_dashboard')

@require_http_methods(["GET"])
def view_order_admin(request, order_id):
    """
    Renders detailed workflow stages for an order's items for admin tracking.
    """
    try:
        logger.info(f"Admin {request.user} is viewing progress for order {order_id}.")
        order = get_object_or_404(Order, id=order_id)
        
        items = order.items.all()
        from django.contrib.contenttypes.models import ContentType
        from myapp.models import WorkflowInstance
        ct = ContentType.objects.get_for_model(OrderItem)
        
        items_data = []
        for item in items:
            instance = WorkflowInstance.objects.filter(content_type=ct, object_id=item.id).first()
            stage_chain = []
            current_stage = None
            
            if instance and instance.workflow:
                stage_chain = instance.workflow.stages.order_by('sequence')
                current_stage = instance.current_stage

            items_data.append({
                'item': item,
                'workflow_instance': instance,
                'stage_chain': stage_chain,
                'current_stage': current_stage
            })
            
        context = {
            'order': order,
            'items_data': items_data
        }
        return render(request, 'view_order_admin.html', context)
    except Exception as e:
        logger.error(f"Error fetching extended admin order view {order_id}: {e}", exc_info=True)
        messages.error(request, "Could not load the workflow tracker.")
        return redirect('laundry:admin_dashboard')

# HTMX endpoints
@require_http_methods(["GET"])
def htmx_check_email(request):
    """
    Checks if a user already has a pending order based on email.
    """
    logger.info(f"Checking for pending orders for email: {request.GET.get('customer_email', '').strip()}")
    email = request.GET.get('customer_email', '').strip()
    if email:
        # Check if they have an order that hasn't been picked up/processed yet
        pending_exists = Order.objects.filter(customer_email=email, status='pending').exists()
        if pending_exists:
            return HttpResponse('<div class="text-danger small fw-bold mb-3"><i class="fas fa-exclamation-circle me-1"></i>You already have a pending request to be picked up.</div>')
    return HttpResponse('')

@require_http_methods(["GET"])
def htmx_get_package_options(request):
    """
    Returns package options for a given category.
    """
    logger.info(f"User {request.user} is getting packages for category {request.GET.get('category')}.")
    category_id = request.GET.get('category')
    logger.info(f"ALEUKEM  {category_id}")

    if not category_id:
        # logger.error(f"User {request.user} is getting packages for category {request.GET.get('category')}.")
        return HttpResponse('')
    
    options= Package.objects.filter(category_id=category_id)
    context = {'options': options}
    return render(request, 'htmx/service_options.html', context)

@require_http_methods(["GET"])
def htmx_get_package_details(request):
    """
    Returns a snippet of HTML with price and delivery details for a given package.
    """
    logger.info(f"User {request.user} is getting package details for package {request.GET.get('package')}.")
    package_id = request.GET.get('package')
    package = None
    if package_id:
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            pass # Package not found, template will handle with N/A
    
    context = {'package': package}
    return render(request, 'htmx/service_details.html', context)

@require_http_methods(["POST"])
def htmx_add_item(request, order_id):
    """
    Adds a new OrderItem to an existing Order.
    """
    logger.info(f"User {request.user} is adding item to order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    form = AddItemForm(request.POST)
   

    if form.is_valid():
        try:
            package = form.cleaned_data['package']
            name = form.cleaned_data['name']
            color = form.cleaned_data['color']
            
            # Calculate price and delivery time from the selected service
           
            price = package.price

            delivery_time_days = package.delivery_time_days
            
            # Create and save the new OrderItem
            new_item = OrderItem.objects.create(
                order=order,
                package=package,
                name=name,
                color=color,
                price=price,
                delivery_time_days=delivery_time_days
            )
            logger.info(f"Item added successfully: {new_item}")
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
    logger.info(f"User {request.user} is editing item {item_id}.")
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
    logger.info(f"User {request.user} is deleting item {item_id}.")
    item = get_object_or_404(OrderItem, id=item_id)
    item.delete()
    return HttpResponse(status=200, headers={'HX-Trigger': 'refresh-summary'})

@require_http_methods(["GET"])
def htmx_get_order_summary(request, order_id):
    """
    Returns an updated order summary snippet.
    """
    logger.info(f"User {request.user} is getting order summary for order {order_id}.")
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
    logger.info(f"Order summary: {summary}")
    context = {'summary': summary}
    return render(request, 'htmx/order_summary.html', context)
@csrf_exempt
@require_http_methods(["POST"])
def htmx_send_invoice1(request, order_id):
    logger.info(f"User {request.user} is sending invoice for order {order_id}.")
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
    paypal_url = request.build_absolute_uri(reverse('laundry:paypal_checkout', args=[order.id]))
    comment_url = request.build_absolute_uri(reverse('laundry:comment_order', args=[order.id]))
    confirm_url = request.build_absolute_uri(reverse('laundry:confirm_order', args=[order.id]))
    print ("Ajadi URL",paypal_url)
    # Render email template as a string
    email_html_content = render_to_string('htmx/invoice_email.html', {
        'order': order,
        'items': items,
        'summary': summary,
        # 'customer_name': order.customer.get_full_name() or order.customer.username,
        'customer_name':  order.customer_name or order.customer.email,
        'paypal_url': paypal_url,
        'comment_url': comment_url,
        'confirm_url': confirm_url,
    })

    # Send email
    try:
        
        print("Email Content:", order.customer_email)
    
        email = EmailMessage(
        f'Invoice for Order #{order.id}',
        email_html_content,
        settings.DEFAULT_FROM_EMAIL,
        [order.customer_email],
    )
        email.content_subtype = "html"  # ✅ Set HTML content type
        result = email.send()  # ✅ Send the email
        print("Email send result:", result)
        return HttpResponse("Invoice Successfully sent")

    
        # return render(request, 'htmx/invoice_sent_message.html')

    except Exception as e:
        print("Email send error:", e)
        messages.error(request, f'Failed to send email: {e}')
        return HttpResponse("Failed to send invoice.", status=500)

@csrf_exempt
def get_paypal_access_token():
    logger.info("Getting PayPal access token.")
    """Retrieves a PayPal access token."""
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post(f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token", auth=auth, headers=headers, data=data)
        response.raise_for_status()
        logger.info(f"PayPal access token retrieved successfully: {response.json()['access_token']}")
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting PayPal access token: {e}")
        return None

@csrf_exempt
def create_paypal_payment(request, order_id):
    logger.info(f"User {request.user} is creating PayPal payment for order {order_id}.")
    """Initiates a PayPal checkout and redirects the user."""
    order = get_object_or_404(Order, pk=order_id)
    items = order.items.all()
    if not items:
        logger.error(f"User {request.user} tried to create a payment for an empty order.")
        messages.error(request, "Cannot create a payment for an empty order.")
        return redirect('laundry:order_detail', order_id=order.id)
    
    # Generate a unique reference
    ref = str(uuid.uuid4().hex[:15]).upper() 
    
    # Construct the base URL for the callback
    # The callback URL must include the unique reference to identify the payment
    # It will be constructed when calling this function
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    # Get the base URL (which needs the request object to build absolute URI)
    # The full callback URL must be passed from the calling view (htmx_send_invoice)
    # For now, we'll use a placeholder for the callback URL structure
    
    amount_kobo = int(order.total_price * 100) if order.total_price else 0
    return_data = {
        "email": order.customer_email,
        "amount": amount_kobo,
        "reference": ref,
        # Paystack will redirect the user to this URL after payment attempt
        "callback_url": "", # This will be set in htmx_send_invoice
        "metadata": {
            "order_id": str(order_id),
            "custom_fields": [
                {"display_name": "Order ID", "variable_name": "order_id", "value": str(order_id)}
            ]
        }
    }
    
    try:
        logger.info(f"User {request.user} is creating PayPal payment for order {order_id}.")
        response = requests.post(url, headers=headers, json=return_data, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.info(f"PayPal payment created successfully: {data}")
        if data.get("status") is True:
            return data["data"].get("authorization_url"), ref
        
        return None, None
        
    except requests.RequestException as e:
        # Log the error
        logger.error(f"Paystack initialization error for order {order_id}: {e}")
        return None, None

# Utility function to fetch data from the external API
@csrf_exempt
def verify_paystack_payment(ref):
    """
    Verifies a Paystack transaction using the reference and Secret Key.
    Returns: (is_verified: bool, data: dict)
    """
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        logger.info(f"Verifying PayPal payment for ref {ref}.")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        data = response.json()
        logger.info(f"PayPal payment verified successfully: {data}")
        # Check Paystack's specific success conditions
        is_verified = (data.get("status") is True and 
                       data.get("data", {}).get("status") == "success")
        
        return is_verified, data.get("data", {})
        
    except requests.RequestException as e:
        logger.error(f"Paystack verification error for ref {ref}: {e}")
        return False, {"message": "Verification failed due to network error."}


@csrf_exempt
def initiate_paystack_transaction(request, email, amount, order_id):
    """
    Initializes a transaction with the Paystack API.

    Args:
        request: The current Django request object (needed to build absolute URL).
        email (str): Customer's email address.
        amount (float): Transaction amount in your currency (e.g., Naira).
        order_id (uuid.UUID or str): The unique ID of the order.

    Returns:
        tuple: (authorization_url: str, reference: str) if successful, 
               or (None, None) on failure.
    """
    # Paystack requires amount in kobo/cent (integer), so multiply by 100
    logger.info(f"Initiating Paystack transaction for order {order_id} with email {email} and amount {amount}.")
    try:
        amount_kobo = int(amount * 100)
    except (TypeError, ValueError):
        logger.error(f"Invalid amount provided for Paystack initialization: {amount}")
        return None, None
    
    # Generate a unique reference for this transaction
    # Paystack recommends max 50 chars. We use 15 chars for simplicity.
    ref = str(uuid.uuid4().hex[:15]).upper() 
    
    # Construct the absolute callback URL for Paystack to redirect the user to.
    # We use 'kwargs' because your URL pattern uses a named parameter (uuid:order_id).
    callback_path = reverse('laundry:paystack_callback', kwargs={'order_id': order_id})
    callback_url = request.build_absolute_uri(callback_path)

    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        # Ensure PAYSTACK_SECRET_KEY is set in your settings.py
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "email": email,
        "amount": amount_kobo,
        "reference": ref,
        "callback_url": callback_url,
        "metadata": {
            "order_id": str(order_id),
            "custom_fields": [
                {"display_name": "Order ID", "variable_name": "order_id", "value": str(order_id)}
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        if data.get("status") is True:
            # Return the Paystack checkout URL and the generated reference
            return data["data"].get("authorization_url"), ref
        
        # Log Paystack's specific error message if status is False
        logger.error(f"Paystack API initialization failed: {data.get('message', 'Unknown error')}")
        return None, None
        
    except requests.RequestException as e:
        # Log network or HTTP errors
        logger.exception(f"Paystack initialization network error for order {order_id}: {e}")
        return None, None


@csrf_exempt
def htmx_send_invoice(request, order_id):
    logger.info(f"User {request.user} is sending invoice for order {order_id}.")
    order = get_object_or_404(Order, id=order_id)

    items = order.items.all()
    if not items:
        logger.error(f"User {request.user} tried to send an invoice for an empty order.")
        return HttpResponse("No items to invoice.", status=400)

    # Calculate totals
    total_price = sum(item.price for item in items)
    max_delivery_days = max(item.delivery_time_days for item in items) if items else 0
    estimated_delivery_date = timezone.now().date() + timedelta(days=max_delivery_days)

    order.total_price = total_price
    order.estimated_delivery_date = estimated_delivery_date
    order.status = 'invoice_sent'
    order.save()

    # Build URLs
    comment_url = request.build_absolute_uri(reverse('laundry:comment_order', args=[order.id]))
    confirm_url = request.build_absolute_uri(reverse('laundry:confirm_order', args=[order.id]))

    # Check if customer is PremiumClient
    try:
        premium_client = PremiumClient.objects.get(email=order.customer_email)
        is_premium = True
    except ObjectDoesNotExist:
        is_premium = False

    # If not premium, initialize Paystack
    paystack_url = None
    reference = None
    if not is_premium:
        paystack_url, reference = initiate_paystack_transaction(
            request=request,
            email=order.customer_email,
            amount=order.total_price,
            order_id=order.id
        )
        if not paystack_url or not reference:
            messages.error(request, 'Failed to initialize payment with Paystack.')
            return HttpResponse("Failed to initialize payment.", status=500)

        Payment.objects.create(
            order=order,
            amount=order.total_price,
            reference=reference,
            verified=False
        )
        logger.info(f"Payment record created for Order {order.id} with reference {reference}")

    # Prepare email content
    summary = {
        'total_items': items.count(),
        'total_price': total_price,
        'delivery_date': estimated_delivery_date,
    }

    email_html_content = render_to_string('htmx/invoice_email.html', {
        'order': order,
        'items': items,
        'summary': summary,
        'customer_name': order.customer_name or order.customer_email,
        'paystack_url': paystack_url,
        'comment_url': comment_url,
        'confirm_url': confirm_url,
        'is_premium': is_premium,  # pass flag to template
    })

    # Send email
    try:
        email = EmailMessage(
            f'Invoice for Order #{order.order_code}',
            email_html_content,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer_email],
        )
        email.content_subtype = "html"
        email.send()
        logger.info(f"Invoice email sent successfully to {order.customer_email} for Order {order.id}.")
        return render(request, 'htmx/invoice_sent_message.html')
    except Exception as e:
        logger.error(f"Email send error for Order {order.id}: {e}")
        messages.error(request, f'Failed to send email: {e}')
        return HttpResponse("Failed to send invoice.", status=500)

@csrf_exempt
def htmx_send_invoicev2(request, order_id):
    logger.info(f"User {request.user} is sending invoice for order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    
    items = order.items.all()
    if not items:
        logger.error(f"User {request.user} tried to send an invoice for an empty order.")
        return HttpResponse("No items to invoice.", status=400)

    # Calculate and update order details
    total_price = sum(item.price for item in items)
    max_delivery_days = max(item.delivery_time_days for item in items) if items else 0
    estimated_delivery_date = timezone.now().date() + timedelta(days=max_delivery_days)

    order.total_price = total_price
    order.estimated_delivery_date = estimated_delivery_date
    order.status = 'invoice_sent' # Mark status before attempting payment init
    order.save()
    logger.info(f"Order {order_id} updated with total price and estimated delivery date.")
    # ----------------------------------------------------
    # ✅ 1. Paystack Initialization
    # ----------------------------------------------------
    
    # Construct the correct callback URL (the view that handles the redirect)
    # The callback URL in Paystack must be a static path,
    # but for your dynamic path, Paystack will add the reference as a query param.
    callback_base_url = request.build_absolute_uri(reverse('laundry:paystack_callback', kwargs={'order_id': order.id}))

    # Call the utility function to initialize the transaction
    # paystack_url, reference = initiate_paystack_transaction(
    #     email=order.customer_email,
    #     amount=order.total_price,
    #     order_id=order.id,
    #     callback_url=callback_base_url # Pass the callback URL to the utility
    # )
    
    paystack_url, reference = initiate_paystack_transaction(
    request=request,  # <-- NEW: Pass the request object here
    email=order.customer_email,
    amount=order.total_price,
    order_id=order.id
)

    if not paystack_url or not reference:
        messages.error(request, 'Failed to initialize payment with Paystack.')
        return HttpResponse("Failed to initialize payment.", status=500)

    # 2. Create the Payment Record in your DB
    try:
        Payment.objects.create(
            # user=order.user.email, # Assuming the order has a 'customer' foreign key to User
            order=order,
            amount=order.total_price,
            reference=reference,
            verified=False
        )
        logger.info(f"Payment record created for Order {order.id} with reference {reference}")
    except Exception as e:
        logger.exception(f"Error creating payment record for Order {order.id}: {e}")
        messages.error(request, 'Payment record creation failed.')
        return HttpResponse("Failed to store payment record.", status=500)

    # ----------------------------------------------------
    # 3. Send Email with Paystack Link
    # ----------------------------------------------------
    
    summary = {
        'total_items': items.count(),
        'total_price': total_price,
        'delivery_date': estimated_delivery_date,
    }
    
    comment_url = request.build_absolute_uri(reverse('laundry:comment_order', args=[order.id]))
    confirm_url = request.build_absolute_uri(reverse('laundry:confirm_order', args=[order.id]))
    
    # The URL sent in the email is the Paystack checkout URL, NOT the callback URL
    email_html_content = render_to_string('htmx/invoice_email.html', {
        'order': order,
        'items': items,
        'summary': summary,
        'customer_name': order.customer_name or order.customer.email,
        'paystack_url': paystack_url, # ✅ Use the actual Paystack checkout URL
        'comment_url': comment_url,
        'confirm_url': confirm_url,
    })

    try:
        email = EmailMessage(
            f'Invoice for Order #{order.order_code}',
            email_html_content,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer_email],
        )
        email.content_subtype = "html"
        email.send()
        logger.info(f"Invoice email sent successfully to {order.customer_email} for Order {order.id}.")
        return render(request, 'htmx/invoice_sent_message.html')

    except Exception as e:
        logger.error(f"Email send error for Order {order.id}: {e}")
        messages.error(request, f'Failed to send email: {e}')
        return HttpResponse("Failed to send invoice.", status=500)
    


# Import your models and the verification utility
# from .models import Order, Payment 
# from .utils import verify_paystack_payment 
@csrf_exempt
@login_required
def paystack_callback_view(request, order_id):
    logger.info(f"User {request.user} is handling Paystack callback for order {order_id}.")
    """
    Handles the user redirect (Callback URL) after a payment attempt.
    It verifies the payment using the reference from the URL query params.
    """
    # 1. Retrieve the Order
    order = get_object_or_404(Order, id=order_id)

    # 2. Get the reference from the Paystack redirect
    ref = request.GET.get('reference')
    if not ref:
        logger.warning("Callback accessed for Order %s without 'reference'.", order_id)
        return redirect('laundry:paystack_cancel') # Redirect to cancellation page

    # 3. Find the existing Payment record
    try:
        payment = Payment.objects.get(reference=ref, order=order)
        logger.debug("Payment record found for reference: %s | Order: %s", ref, order_id)
    except Payment.DoesNotExist:
        logger.error("Payment record not found for reference: %s or does not match Order %s.", ref, order_id)
        return redirect('laundry:paystack_cancel')

    try:
        if not payment.verified:
            logger.info("Payment not verified yet. Attempting direct verification for reference: %s", ref)
            is_verified, paystack_data = verify_paystack_payment(ref)

            if is_verified:
                # Update Payment record
                payment.verified = True
                payment.save()
                logger.info("Payment verified manually for reference: %s", ref)

                # Update the Order status
                order.status = 'paid' # Assuming 'paid' is your status field value
                order.save()
                logger.info("Order %s marked as paid.", order_id)

            else:
                # Payment verification failed (e.g., failed transaction)
                error_message = paystack_data.get("message", "Payment failed or verification delayed.")
                logger.warning("Payment verification failed for reference: %s | Message: %s", ref, error_message)
                return redirect('laundry:paystack_cancel')
                
        # 4. Success - Redirect to the success page
        return redirect('laundry:paystack_success', order_id=order.id) 

    except Exception as e:
        logger.exception("Unexpected error during callback for reference %s: %s", ref, str(e))
        return redirect('laundry:paystack_cancel')
    


# Import your models (Order, Payment) and logging setup
# from .models import Order, Payment 
# import logging
# logger = logging.getLogger(__name__)

@csrf_exempt
def paystack_webhook_view(request):
    """
    Handles asynchronous notifications from Paystack (Webhook URL).
    Verifies the request signature before processing the event.
    """
    logger.info("Received Paystack webhook notification.")
    if request.method != 'POST':
        # Paystack only sends POST requests
        return HttpResponseBadRequest("Invalid request method.")

    # 1. Signature Verification (Security Check)
    signature = request.headers.get('X-Paystack-Signature')
    if not signature:
        logger.warning("Webhook missing signature header.")
        return HttpResponseBadRequest("No signature provided.")

    try:
        # Decode the request body and calculate the HMAC digest
        body = request.body.decode('utf-8')
        digest = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        # Compare the calculated digest with Paystack's signature
        if not hmac.compare_digest(digest, signature):
            logger.error("Webhook signature mismatch. Potential tampering.")
            return HttpResponseBadRequest("Invalid signature.")
    except Exception as sig_error:
        logger.exception("Error verifying webhook signature: %s", str(sig_error))
        return HttpResponseBadRequest("Signature verification failed.")

    # 2. Parse Payload
    try:
        data = json.loads(body)
    except json.JSONDecodeError as json_error:
        logger.error("Webhook payload is not valid JSON: %s", str(json_error))
        return HttpResponseBadRequest("Invalid JSON payload.")

    event = data.get('event')
    logger.debug("Webhook event received: %s", event)

    # 3. Process 'charge.success' Event
    if event == 'charge.success':
        transaction_data = data.get('data', {})
        reference = transaction_data.get('reference')

        if not reference:
            logger.error("Webhook missing payment reference in 'charge.success' payload.")
            return JsonResponse({"status": "error", "message": "No reference in payload"}, status=400)

        # Retrieve the Payment record using the reference
        try:
            payment = Payment.objects.select_related('order').get(reference=reference)
            logger.info("Payment record found for reference: %s", reference)
        except Payment.DoesNotExist:
            logger.warning("Payment record not found for reference: %s. Ignoring.", reference)
            # It's important to return 200 OK here so Paystack doesn't keep retrying.
            return JsonResponse({"status": "success", "message": "Payment record not found, but webhook received."})

        # Update Payment status
        if not payment.verified:
            payment.verified = True
            payment.save()
            logger.info("Payment verified by Webhook for reference: %s", reference)

            # Update the associated Order status
            if payment.order:
                payment.order.status = 'paid' # Assuming 'paid' is your desired status
                payment.order.save()
                logger.debug("Order %s marked as paid by Webhook.", payment.order.id)
            else:
                logger.warning("Payment %s has no associated order.", payment.id)

    # 4. Acknowledge Receipt
    # For any event processed (or ignored), you MUST return a 200 OK
    # to let Paystack know you received the notification successfully.
    return JsonResponse({"status": "success"})

@login_required
def paystack_success(request, order_id):
    """Displays a success page after payment is confirmed."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # You can add logic here to display order details or payment confirmation
    context = {
        'order': order,
        'message': f'Your payment for Order #{order.id} was successful!',
    }
    return render(request, 'laundry/paystack_success.html', context)


from django.shortcuts import render

# No login required if a public failure page is desired, or use login_required
def paystack_cancel(request):
    """Displays a failure/cancellation page after payment attempt failed or was canceled."""
    # You might want to get the order_id from the session or a query param if needed
    context = {
        'message': 'Your payment could not be completed. Please check your payment method or try again.',
        'support_email': settings.DEFAULT_FROM_EMAIL
    }
    return render(request, 'laundry/paystack_cancel.html', context)




@csrf_exempt
def laundry_request_confirmation(request):
    logger.info(f"User {request.user} is sending laundry request confirmation email.")
    send_mail(
        'Laundry Service Request Confirmation',
        'Your request has been received. A dispatch agent will visit shortly.',
        settings.DEFAULT_FROM_EMAIL,
        ['ayodelefestusng@gmail.com', 'upwardwave.dignity@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("Confirmation email sent.")

from django.db import transaction
@is_admin
@require_http_methods(["GET"])
def assign_qr_to_order_view(request, order_id):
    logger.info(f"User {request.user} is accessing QR assignment page for order {order_id}.")
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'assign_qr.html', context)

@csrf_exempt
@is_admin
@require_http_methods(["POST"])
def api_assign_qr_to_item(request, item_id):
    logger.info(f"User {request.user} is attempting to assign QR code to item {item_id}.")
    try:
        logger.info(f"User {request.user} is assigning QR code to item {item_id}.")
        data = json.loads(request.body)
        code = data.get('qr_code')
        if not code:
            return JsonResponse({'success': False, 'message': 'QR code is missing.'}, status=400)
            
        item = get_object_or_404(OrderItem, id=item_id)
        
        if item.qr_code:
            return JsonResponse({'success': False, 'message': 'Item already has a QR code assigned.'}, status=400)
            
        from myapp.models import QR
        try:
            qr = QR.objects.get(code=code)
        except QR.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'QR code not found.'}, status=404)
            
        if qr.status != 'unused':
            return JsonResponse({'success': False, 'message': 'QR code is already used.'}, status=400)
            
        with transaction.atomic():
            # 1. Update QR record
            qr.status = 'assigned'
            qr.save()
            
            # 2. Assign to item. This triggers OrderItem.save() 
            # which internally triggers item.order.check_and_update_status()
            item.qr_code = code
            if not hasattr(request.user, 'employee'):
                logger.error(f"User {request.user.email} is not linked to an Employee record.")
                return JsonResponse({
                    'success': False, 
                    'message': 'You must be registered as an employee to perform this action.'
                }, status=403)
            logger.info(f"Employee {request.user.employee} is attempting to assign QR code to item {item_id}.")
            if hasattr(request.user, 'employee'):
                item.qr_initiator = request.user.employee
            item.save()
            
            # 3. Refresh the order object to get the updated status from the save signal
            item.order.refresh_from_db()
            logger.info(f"QR {code} assigned to Item {item.id}. Order status: {item.order.status}, Invoice sent: {item.order.has_invoice_sent}")
            
            return JsonResponse({
                'success': True, 
                'order_status': item.order.status,
                'invoice_sent': item.order.has_invoice_sent
            })

    except Exception as e:
        logger.error(f"Error assigning QR code: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'An internal error occurred.'}, status=500)



@csrf_exempt
@is_admin
@require_http_methods(["POST"])
def api_assign_qr_to_itemv1(request, item_id):
    logger.info(f"User {request.user} is attempting to assign QR code to item {item_id}.")
    try:
        data = json.loads(request.body)
        code = data.get('qr_code')
        if not code:
            return JsonResponse({'success': False, 'message': 'QR code is missing.'}, status=400)
            
        item = get_object_or_404(OrderItem, id=item_id)
        
        # Check if item already has a QR
        if item.qr_code:
            return JsonResponse({'success': False, 'message': 'Item already has a QR code assigned.'}, status=400)
            
        from myapp.models import QR
        try:
            qr = QR.objects.get(code=code)
        except QR.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'QR code not found in system.'}, status=404)
            
        if qr.status != 'unused':
            return JsonResponse({'success': False, 'message': 'QR code is already used or invalid.'}, status=400)
            
        # Assign QR
        with transaction.atomic():
            qr.status = 'assigned'
            # qr.order_item = item
            qr.save()
            
            item.qr_code = code
            item.save()
            order_updated = item.order.check_and_update_invoice_status()
            logger.info(f"QR {code} assigned to Item {item.id}. Order update: {order_updated}")
            return JsonResponse({
                'success': True, 
                'order_status': item.order.status,
                'invoice_sent': item.order.has_invoice_sent
            })
            # if order_updated:
            #     return JsonResponse({'success': True, 'message': 'QR code assigned successfully.'})
            # else:
            #     return JsonResponse({'success': False, 'message': 'QR code assigned successfully but order status not updated.'})
    except Exception as e:
        logger.error(f"Error assigning QR code: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

from django.contrib.contenttypes.models import ContentType
@csrf_exempt
@login_required
def employee_queue(request):
    logger.info(f"User {request.user} is accessing the employee queue.")
    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, "Employee profile not found.")
        return redirect('homepage')

    ct = ContentType.objects.get_for_model(OrderItem)
    instances = WorkflowInstance.objects.filter(
        content_type=ct, 
        completed_at__isnull=True,
        current_stage__responsible_officer=employee
    )
    
    manager_instances = WorkflowInstance.objects.filter(
        content_type=ct,
        completed_at__isnull=True,
        current_stage__responsible_officer__line_manager=employee
    )
    
    deputy_instances = WorkflowInstance.objects.filter(
        content_type=ct,
        completed_at__isnull=True,
        current_stage__responsible_officer__deputy_person=employee
    )
    
    all_instances = (instances | manager_instances | deputy_instances).distinct()

    context = {
        'instances': all_instances,
    }
    return render(request, 'employee_queue.html', context)
@csrf_exempt
@login_required
def accept_item(request, item_id):
    logger.info(f"User {request.user} is attempting to accept item {item_id}.")
    item = get_object_or_404(OrderItem, id=item_id)
    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, "Employee profile required.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    ct = ContentType.objects.get_for_model(OrderItem)
    instance = WorkflowInstance.objects.filter(content_type=ct, object_id=item.id).first()
    
    if not instance:
        workflow = None
        if item.package.workflows.exists():
            workflow = item.package.workflows.first()
            first_stage = workflow.stages.order_by('sequence').first()
            if first_stage:
                instance = WorkflowInstance.objects.create(
                    workflow=workflow,
                    content_type=ct,
                    object_id=item.id,
                    current_stage=first_stage,
                    initiated_by=employee
                )
    
    if not instance:
        messages.error(request, "No workflow configured for this item's package.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    stage = instance.current_stage
    officer = stage.responsible_officer

    can_accept = False
    if officer == employee or officer.line_manager == employee or officer.deputy_person == employee or request.user.is_superuser:
        can_accept = True
    elif getattr(request.user, 'is_hr_admin', False):
        can_accept = True

    if not can_accept:
        messages.error(request, "Order not at your stage.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    from_stage_name = stage.service_action.name if stage.service_action else f"Stage {stage.sequence}"
    
    next_stage = WorkflowStage.objects.filter(
        workflow=instance.workflow,
        sequence__gt=stage.sequence
    ).order_by('sequence').first()

    if next_stage:
        instance.current_stage = next_stage
        instance.save()
        item.status = next_stage.service_action.name if next_stage.service_action else f"Stage {next_stage.sequence}"
        item.save()
        to_stage_name = item.status
        messages.success(request, f"Item moved to {to_stage_name}.")
    else:
        instance.completed_at = timezone.now()
        instance.save()
        item.status = 'completed'
        item.save()
        to_stage_name = 'Completed'
        messages.success(request, "Item workflow completed.")

    WorkflowHistory.objects.create(
        item=item,
        from_stage=from_stage_name,
        to_stage=to_stage_name,
        actor=employee,
        action="Accept"
    )

    referer = request.META.get('HTTP_REFERER', '')
    if 'transit' in referer:
        return redirect('laundry:qr_transit_scanner')
    return redirect('laundry:employee_queue')
@csrf_exempt
@login_required
def reject_item(request, item_id):
    logger.error(f"User {request.user} is attempting to reject item {item_id}.")
    item = get_object_or_404(OrderItem, id=item_id)
    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, "Employee profile required.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    ct = ContentType.objects.get_for_model(OrderItem)
    instance = WorkflowInstance.objects.filter(content_type=ct, object_id=item.id).first()
    
    if not instance:
        messages.error(request, "No workflow instance found.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    stage = instance.current_stage
    officer = stage.responsible_officer

    can_reject = False
    if officer == employee or officer.line_manager == employee or officer.deputy_person == employee or request.user.is_superuser:
        can_reject = True
    elif getattr(request.user, 'is_hr_admin', False):
        can_reject = True

    if not can_reject:
        messages.error(request, "Order not at your stage.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    from_stage_name = stage.service_action.name if stage.service_action else f"Stage {stage.sequence}"

    target_stage_id = request.POST.get('target_stage_id')
    rejection_reason = request.POST.get('rejection_reason', 'Rejected during transit')

    if target_stage_id:
        prev_stage = WorkflowStage.objects.filter(id=target_stage_id).first()
    else:
        prev_stage = WorkflowStage.objects.filter(
            workflow=instance.workflow,
            sequence__lt=stage.sequence
        ).order_by('-sequence').first()

    if prev_stage:
        instance.current_stage = prev_stage
        instance.save()
        item.status = prev_stage.service_action.name if prev_stage.service_action else f"Stage {prev_stage.sequence}"
        item.save()
        to_stage_name = item.status
        messages.warning(request, f"Item rejected and sent back to {to_stage_name}. Reason: {rejection_reason}")
        
        prev_actor = prev_stage.responsible_officer
        
        WorkflowHistory.objects.create(
            item=item,
            from_stage=from_stage_name,
            to_stage=to_stage_name,
            actor=employee,
            previous_actor=prev_actor,
            notes=f"Returned to {to_stage_name}. Reason: {rejection_reason}",
            action="Reject"
        )
    else:
        messages.error(request, "Cannot reject further. Item is at the first stage.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    referer = request.META.get('HTTP_REFERER', '')
    if 'transit' in referer:
        return redirect('laundry:qr_transit_scanner')
    return redirect('laundry:employee_queue')

# --------------------------------------------
# TRANSIT SCANNER (WORKFLOW ENGINE EXTENSION)
# --------------------------------------------
@require_http_methods(["GET"])
def qr_transit_scanner(request):
    """
    Renders the page for scanning items to transition them in their workflow.
    """
    logger.info(f"User {request.user} is accessing the QR transit scanner.")

    return render(request, 'transit_scanner.html')

@csrf_exempt
@require_http_methods(["POST"])
def htmx_transit_scan(request):
    """
    Called via HTMX POST when a QR code is scanned in transit.
    Returns the action card (transit_action_card.html) for that item.
    """
    import json
    logger.info(f"User {request.user} submitted a transit scan.")
    try:
        data = json.loads(request.body)
        decoded_text = data.get('decodedText', '').strip()
    except json.JSONDecodeError:
        decoded_text = request.POST.get('decodedText', '').strip()

    if not decoded_text:
        return HttpResponse('<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-1"></i>Invalid scan data received.</div>')

    # Find the order item by QR code
    item = OrderItem.objects.filter(qr_code=decoded_text).first()
    if not item:
        return HttpResponse('<div class="alert alert-danger"><i class="fas fa-search me-1"></i>No item found matching this QR code.</div>')

    from django.contrib.contenttypes.models import ContentType
    from myapp.models import WorkflowInstance
    ct = ContentType.objects.get_for_model(OrderItem)
    instance = WorkflowInstance.objects.filter(content_type=ct, object_id=item.id).first()

    if not instance:
        return HttpResponse('<div class="alert alert-warning"><i class="fas fa-info-circle me-1"></i>This item has no assigned workflow engine yet.</div>')
        
    if instance.completed_at:
        return HttpResponse('<div class="alert alert-success"><i class="fas fa-check-circle me-1"></i>This item has already completed its workflow lifecycle.</div>')

    # Get prior stages for selective rejection
    prior_stages = []
    if instance.current_stage:
        prior_stages = instance.workflow.stages.filter(sequence__lt=instance.current_stage.sequence).order_by('-sequence')

    context = {
        'item': item,
        'instance': instance,
        'current_stage': instance.current_stage,
        'prior_stages': prior_stages
    }
    return render(request, 'htmx/transit_action_card.html', context)
