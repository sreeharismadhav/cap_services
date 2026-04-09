import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.utils.html import strip_tags

from core.views import get_base_template
from .models import User, Profile, UserAddress, PasswordReset
from .forms import (
    LoginForm, RegisterForm, ProfileForm, AddressForm,
    UserAddressForm, ForgotPasswordForm, ResetPasswordForm
)
from core.models import Address
from core.utils import generate_otp, log_activity
from datetime import timedelta

import sendgrid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from sendgrid.helpers.mail import Mail
from django.conf import settings

logger = logging.getLogger(__name__)

def login_view(request):
    if request.session.get('user_id'):
        return redirect('core:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['user_role'] = user.role
            
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            log_activity(user, 'LOGIN', request=request)
            messages.success(request, f'Welcome back, {user.full_name}!')
            
            return redirect('core:home')
    else:
        form = LoginForm()

    context = {'form': form}
    context['base_template'] = get_base_template(request.session.get('user_role'))    
    return render(request, 'accounts/login.html', context)


def logout_view(request):
    if request.session.get('user_id'):
        try:
            user = User.objects.get(id=request.session['user_id'])
            log_activity(user, 'LOGOUT', request=request)
        except:
            pass
    
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('accounts:login')


def register_view(request):
    if request.session.get('user_id'):
        return redirect('core:home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            request.session['user_id'] = user.id
            request.session['user_email'] = user.email
            request.session['user_role'] = user.role
            
            log_activity(user, 'REGISTER', request=request)
            messages.success(request, 'Registration successful!')
            return redirect('core:home')
    else:
        form = RegisterForm()
    
    context = {'form': form}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'accounts/register.html', context)


def profile_view(request):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']
                profile.save()
            messages.success(request, 'Profile updated')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=user)
    
    context = {'user': user, 'profile': profile, 'form': form}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'accounts/profile.html', context)


def addresses_view(request):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    profile = Profile.objects.get(user=user)
    addresses = UserAddress.objects.filter(user=user).select_related('address')
    
    context = {
        'user': user,
        'profile': profile,
        'addresses': addresses,
        'base_template': 'core/base.html'
    }
    return render(request, 'accounts/addresses.html', context)

@require_POST
def set_default_address(request, address_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    address = get_object_or_404(UserAddress, id=address_id, user=user)
    
    # Set all addresses to not default, then set this one as default
    UserAddress.objects.filter(user=user).update(is_default=False)
    address.is_default = True
    address.save()
    
    messages.success(request, 'Default address updated')
    return redirect('accounts:addresses')


def edit_address(request, address_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    address = get_object_or_404(UserAddress, id=address_id, user=user)
    
    if request.method == 'POST':
        address_form = AddressForm(request.POST, instance=address.address)
        user_address_form = UserAddressForm(request.POST, instance=address)
        
        if address_form.is_valid() and user_address_form.is_valid():
            address_form.save()
            user_address_form.save()
            messages.success(request, 'Address updated successfully')
            return redirect('accounts:addresses')
    else:
        address_form = AddressForm(instance=address.address)
        user_address_form = UserAddressForm(instance=address)
    
    context = {
        'address_form': address_form,
        'user_address_form': user_address_form,
        'address': address,
        'user': user,
        'profile': Profile.objects.get(user=user),
        'base_template': 'core/base.html'
    }
    return render(request, 'accounts/edit_address.html', context)


def add_address_view(request):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    profile = Profile.objects.get(user=user)
    
    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        user_address_form = UserAddressForm(request.POST)
        
        if address_form.is_valid() and user_address_form.is_valid():
            address = address_form.save()
            user_address = user_address_form.save(commit=False)
            user_address.user = user
            user_address.address = address
            user_address.save()
            
            messages.success(request, 'Address added successfully')
            return redirect('accounts:addresses')
    else:
        address_form = AddressForm()
        user_address_form = UserAddressForm()
    
    context = {
        'address_form': address_form,
        'user_address_form': user_address_form,
        'user': user,
        'profile': profile,
        'base_template': 'core/base.html'
    }
    return render(request, 'accounts/add_address.html', context)


def delete_address_view(request, address_id):
    if not request.session.get('user_id'):
        return redirect('accounts:login')
    
    user = User.objects.get(id=request.session['user_id'])
    user_address = UserAddress.objects.filter(id=address_id, user=user).first()
    
    if user_address:
        address = user_address.address
        user_address.delete()
        address.delete()
        messages.success(request, 'Address deleted')
    
    return redirect('accounts:addresses')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            otp = generate_otp()
            
            # Save OTP to database
            PasswordReset.objects.create(
                user=user,
                otp=otp,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # Prepare HTML email
            subject = '🔐 Password Reset Request - CAP Services'
            
            html_message = render_to_string('emails/password_reset_otp.html', {
                'user': user,
                'otp': otp,
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
                'site_email': settings.SITE_EMAIL,
                'site_phone': settings.SITE_PHONE,
                'year': timezone.now().year,
                'expiry_minutes': 10
            })
            
            plain_message = strip_tags(html_message)
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(request, f'📧 OTP sent to {user.email}')
                request.session['reset_email'] = user.email
                return redirect('accounts:reset_password')
                
            except Exception as e:
                messages.error(request, 'Failed to send email. Please try again.')
                logger.error(f"Email error: {e}")
    else:
        form = ForgotPasswordForm()
    
    context = {'form': form}
    return render(request, 'accounts/forgot_password.html', context)

def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordReset.objects.filter(
                    user=user,
                    otp=otp,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if otp_record:
                    otp_record.is_used = True
                    otp_record.save()
                    user.set_password(password)
                    user.save()
                    
                    # Clear session
                    del request.session['reset_email']
                    
                    # Send confirmation email
                    send_mail(
                        subject='Password Changed Successfully - CAP Services',
                        message=f'Hi {user.first_name},\n\nYour password has been successfully changed. If you did not perform this action, please contact support immediately.\n\n- CAP Services Team',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                    
                    messages.success(request, 'Password reset successful! Please login.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'Invalid or expired OTP')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
    else:
        form = ResetPasswordForm()
    
    context = {'form': form}
    context['base_template'] = get_base_template(request.session.get('user_role'))
    return render(request, 'accounts/reset_password.html', context)