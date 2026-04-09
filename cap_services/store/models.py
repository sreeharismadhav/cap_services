from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from core.models import BaseModel
from core.enums import ProductStatus, InventoryChangeType
from accounts.models import User
from .managers import CategoryManager, ProductManager
import random
import string


class Category(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:category', args=[self.slug])
    
    @property
    def subcategories(self):
        return self.children.all()
    
    objects = CategoryManager()


class Brand(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    specifications = models.JSONField(default=dict, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.sku = f"PRD{random_str}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    @property
    def current_price(self):
        return self.discounted_price or self.price

    @property
    def discount_percentage(self):
        if self.discounted_price and self.price:
            return int(((self.price - self.discounted_price) / self.price) * 100)
        return 0
    
    objects = ProductManager()


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'is_primary']

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductAttribute(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.name}: {self.value}"


class Inventory(BaseModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"{self.product.name} - Stock: {self.available}"

    @property
    def available(self):
        return self.quantity - self.reserved

    @property
    def is_low_stock(self):
        return self.available <= self.low_stock_threshold

    def reserve(self, quantity):
        if self.available >= quantity:
            self.reserved += quantity
            self.save()
            return True
        return False

    def release(self, quantity):
        self.reserved = max(0, self.reserved - quantity)
        self.save()

    def deduct(self, quantity):
        if self.available >= quantity:
            self.quantity -= quantity
            self.reserved = max(0, self.reserved - quantity)
            self.save()
            return True
        return False


class InventoryHistory(BaseModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='history')
    old_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    change_type = models.CharField(max_length=20, choices=InventoryChangeType.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.inventory.product.name} - {self.change_type}"


class Review(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(1,1),(2,2),(3,3),(4,4),(5,5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.rating}★"