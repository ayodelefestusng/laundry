


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
    return render(request, 'myapp/admin_dashboard.html', context)



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
        return render(request, 'myapp/htmx/item_table_row.html', {'item': new_item})
    
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
            return render(request, 'myapp/htmx/item_table_row.html', {'item': updated_item})
        else:
            # Pass the form with errors back to the template
            return render(request, 'myapp/htmx/edit_item_form_row.html', {'form': form, 'item': item, 'all_categories': all_categories})
    else: # GET request
        form = LaundryItemForm(instance=item)
        return render(request, 'myapp/htmx/edit_item_form_row.html', {'form': form, 'item': item, 'all_categories': all_categories})


@require_http_methods(["DELETE"])
@user_passes_test(is_admin)
def htmx_delete_item(request, item_id):
    """
    Handles HTMX DELETE request to remove a laundry item.
    """
    item = get_object_or_404(LaundryItem, id=item_id)
    item.delete()
    return HttpResponse(status=200) # Returns an empty response with a success status code


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
    email_html_content = render_to_string('myapp/htmx/invoice_email.html', {
        'order': order,
        'summary': summary,
        'items': items,
        'customer_name': request.user.first_name or "Valued Customer"
    })
    
    try:
        subject = f"Invoice for your Laundry Order #{order.id}"
        from_email = settings.DEFAULT_FROM_EMAIL
        # Using a dummy email as we don't have a real customer model with an email field
        recipient_list = ["test@example.com"]
        
        # Send the email
        send_mail(
            subject,
            '',  # Empty message body as we're using html_message
            from_email,
            recipient_list,
            html_message=email_html_content,
        )
        
        # Return success message to the frontend
        return render(request, 'myapp/htmx/invoice_sent_message.html')
    except Exception as e:
        # Return an error message to the frontend if email sending fails
        return HttpResponse(f"<div class='alert alert-danger mt-3'>Failed to send invoice: {e}</div>", status=500)


def htmx_get_services(request):
    """
    HTMX view to fetch services based on the selected category.
    """
    category_id = request.GET.get('category')
    services = Service.objects.filter(category_id=category_id).order_by('service_type') if category_id else Service.objects.none()
    return render(request, 'myapp/htmx/service_options.html', {'services': services})

def htmx_get_service_details(request):
    """
    HTMX view to fetch the service price and delivery time.
    """
    service_id = request.GET.get('service')
    service = get_object_or_404(Service, id=service_id) if service_id else None
    return render(request, 'myapp/htmx/service_details.html', {'service': service})

def htmx_get_order_summary(request, order_id):
    """
    HTMX view to fetch and render the live order summary.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    summary = get_order_summary(order)
    return render(request, 'myapp/htmx/order_summary.html', {'summary': summary})

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
            return render(request, 'myapp/paypal_success.html')
        else:
            return HttpResponse(f"PayPal payment failed: {payment.error}", status=400)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)

def paypal_cancel(request):
    """
    Handles the redirect from a canceled PayPal payment.
    Renders the cancel page.
    """
    return render(request, 'myapp/paypal_cancel.html')

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
            
            return render(request, 'myapp/comment_success.html') # Redirect to a success page
    else:
        form = CommentForm()
    
    return render(request, 'myapp/add_comment.html', {'form': form, 'order': order})

def order_detail(request, order_id):
    """
    Placeholder view for displaying order details.
    """
    order = get_object_or_404(CustomerRequest, id=order_id)
    return HttpResponse(f"Order details for {order.id}")
