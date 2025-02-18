from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.contrib import messages
from sslcommerz_lib import SSLCOMMERZ
import string
import random
from .models import Subscription, Payment

# Create your views here.

@login_required
def pricing(request):
    return render(request, 'payment/pricing.html')

@login_required
def checkout(request, plan):
    # Validate plan
    if plan not in ['business', 'enterprise']:
        return redirect('payment:pricing')
    
    context = {
        'plan': plan,
    }
    return render(request, 'payment/checkout.html', context)

def unique_transaction_id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@login_required
def initiate_payment(request, plan):
    # Get plan amount in BDT
    amount = 1250 if plan == 'business' else 2500
    
    settings_dict = {
        'store_id': settings.SSLC_STORE_ID,
        'store_pass': settings.SSLC_STORE_PASSWORD,
        'issandbox': True
    }
    
    sslcz = SSLCOMMERZ(settings_dict)
    post_body = {
        'total_amount': amount,
        'currency': "BDT",
        'tran_id': unique_transaction_id_generator(),
        'success_url': request.build_absolute_uri('/payment/success/'),
        'fail_url': request.build_absolute_uri('/payment/cancel/'),
        'cancel_url': request.build_absolute_uri('/payment/cancel/'),
        'emi_option': 0,
        'cus_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'cus_email': request.user.email,
        'cus_phone': request.user.profile.phone if hasattr(request.user, 'profile') else "N/A",
        'cus_add1': "N/A",
        'cus_city': "N/A",
        'cus_country': "Bangladesh",
        'shipping_method': "NO",
        'multi_card_name': "",
        'num_of_item': 1,
        'product_name': f"{plan.title()} Plan Subscription",
        'product_category': "Subscription",
        'product_profile': "non-physical-goods"
    }

    response = sslcz.createSession(post_body)
    if response['status'] == 'SUCCESS':
        # Store payment info
        Payment.objects.create(
            user=request.user,
            amount=amount,
            stripe_payment_id=post_body['tran_id'],
            status='pending'
        )
        return redirect(response['GatewayPageURL'])
    else:
        messages.error(request, 'Payment initialization failed. Please try again.')
        return redirect('payment:pricing')

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        payment = Payment.objects.filter(
            stripe_payment_id=request.POST.get('tran_id'),
            status='pending'
        ).first()
        
        if payment:
            payment.status = 'succeeded'
            payment.save()
            
            # Create or update subscription
            Subscription.objects.update_or_create(
                user=payment.user,
                defaults={
                    'plan': 'business' if payment.amount == 1250 else 'enterprise',
                    'is_active': True,
                    'stripe_subscription_id': payment.stripe_payment_id
                }
            )
            
            messages.success(
                request, 
                'Payment successful! Your subscription has been activated.',
                extra_tags='success'
            )
        
    return render(request, 'payment/success.html')

@csrf_exempt
def payment_cancel(request):
    if request.method == 'POST':
        payment = Payment.objects.filter(
            stripe_payment_id=request.POST.get('tran_id'),
            status='pending'
        ).first()
        
        if payment:
            payment.status = 'failed'
            payment.save()
            
            messages.error(
                request, 
                'Payment was cancelled. Please try again or contact support if you need assistance.',
                extra_tags='error'
            )
    
    return redirect('payment:pricing')

@login_required
def contact_sales(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        company = request.POST.get('company')
        message = request.POST.get('message')
        
        try:
            send_mail(
                subject=f'Enterprise Plan Inquiry from {name}',
                message=f"""
                Name: {name}
                Email: {email}
                Company: {company}
                Message: {message}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SALES_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your interest! Our sales team will contact you shortly.')
            return redirect('payment:pricing')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again.')
    
    return render(request, 'payment/contact_sales.html', {'user': request.user})


