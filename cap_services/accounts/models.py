from django.db import models
from django.core.validators import RegexValidator
from core.models import BaseModel, Address
from core.enums import UserRole, AddressType


class User(BaseModel):
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be in format: '+919999999999'"
    )
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, validators=[phone_validator])
    whatsapp_number = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.CUSTOMER)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    whatsapp_opt_in = models.BooleanField(default=False)
    whatsapp_opt_in_at = models.DateTimeField(null=True, blank=True)
    sms_opt_in = models.BooleanField(default=True)
    email_opt_in = models.BooleanField(default=True)
    password = models.CharField(max_length=255)
    last_login = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return f"Profile of {self.user.email}"


class UserAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='user_addresses')
    is_default = models.BooleanField(default=False)
    address_type = models.CharField(max_length=20, choices=AddressType.choices, default=AddressType.HOME)
    receiver_name = models.CharField(max_length=150, blank=True)
    receiver_phone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.address}"


class PasswordReset(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.email} - {self.otp}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()