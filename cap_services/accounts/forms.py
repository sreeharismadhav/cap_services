from django import forms
from django.core.exceptions import ValidationError
from .models import User, UserAddress, Profile
from core.models import Address
from core.utils import validate_indian_phone
from core.enums import AddressType


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise ValidationError('Invalid email or password')
                if not user.is_active:
                    raise ValidationError('Account is disabled')
                cleaned_data['user'] = user
            except User.DoesNotExist:
                raise ValidationError('Invalid email or password')
        
        return cleaned_data


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm password'
    }))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not validate_indian_phone(phone):
            raise ValidationError('Enter a valid 10-digit Indian phone number')
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('Phone number already registered')
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already registered')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'CUSTOMER'
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_line1', 'address_line2', 'city', 'state', 'pincode', 'landmark', 'map_link']
        widgets = {
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House/Flat No., Building Name'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, Area'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN Code'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landmark (optional)'}),
            'map_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Google Maps Link (optional)'}),
        }
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        from core.utils import validate_pincode
        if not validate_pincode(pincode):
            raise ValidationError('Enter a valid 6-digit PIN code')
        return pincode


class UserAddressForm(forms.ModelForm):
    address_type = forms.ChoiceField(choices=AddressType.choices, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = UserAddress
        fields = ['address_type', 'is_default', 'receiver_name', 'receiver_phone']
        widgets = {
            'receiver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receiver name (optional)'}),
            'receiver_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receiver phone (optional)'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            raise ValidationError('No account found with this email')
        return email


class ResetPasswordForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter OTP'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm new password'
    }))
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match')
        
        if password and len(password) < 8:
            raise ValidationError('Password must be at least 8 characters')
        
        return cleaned_data