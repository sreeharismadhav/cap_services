from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import BaseModel
from core.enums import OrderStatus, PaymentStatus, PaymentMethod, ReturnStatus, CouponType
from accounts.models import User, UserAddress
from store.models import Product, Inventory, InventoryHistory
import random
import string


class Cart(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_id = models.CharField(max_length=255, null=True, blank=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Cart - {self.user.email if self.user else self.session_id}"

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def discount_total(self):
        if self.coupon:
            if self.coupon.discount_type == CouponType.PERCENT:
                return (self.subtotal * self.coupon.discount_value / 100)
            elif self.coupon.discount_type == CouponType.FIXED:
                return min(self.coupon.discount_value, self.subtotal)
        return self.coupon_discount

    @property
    def total(self):
        return self.subtotal - self.discount_total

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        self.items.all().delete()
        self.coupon = None
        self.coupon_discount = 0
        self.save()


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.current_price
        super().save(*args, **kwargs)


class Coupon(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=CouponType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        return (self.valid_from <= now <= self.valid_to and 
                self.used_count < self.max_uses and
                self.is_active)


class CouponUsage(BaseModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['coupon', 'user', 'order']

    def __str__(self):
        return f"{self.coupon.code} - {self.user.email}"


class Order(BaseModel):
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.PROTECT, related_name='orders')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PLACED)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            prefix = 'ORD'
            timestamp = timezone.now().strftime('%y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.order_number = f"{prefix}{timestamp}{random_str}"
        super().save(*args, **kwargs)

    def update_status(self, new_status, user, notes=""):
        if self.status != new_status:
            old_status = self.status
            self.status = new_status
            self.save()
            
            OrderStatusHistory.objects.create(
                order=self,
                status=new_status,
                changed_by=user,
                notes=notes
            )


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class OrderStatusHistory(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=OrderStatus.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


class Payment(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    gateway_name = models.CharField(max_length=50, blank=True)
    gateway_response = models.JSONField(default=dict)
    payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == PaymentStatus.PAID and not self.payment_date:
            self.payment_date = timezone.now()
        super().save(*args, **kwargs)


class Invoice(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            prefix = 'INV'
            timestamp = timezone.now().strftime('%y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.invoice_number = f"{prefix}{timestamp}{random_str}"
        super().save(*args, **kwargs)


class Return(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='returns')
    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT, related_name='returns')
    quantity = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=ReturnStatus.choices, default=ReturnStatus.REQUESTED)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Return #{self.id} - {self.order.order_number}"

    def approve(self, user, refund_amount=None):
        self.status = ReturnStatus.APPROVED
        self.approved_by = user
        self.refund_amount = refund_amount or self.order_item.price * self.quantity
        self.save()
        
        # Update inventory
        self.order_item.product.inventory.quantity += self.quantity
        self.order_item.product.inventory.save()