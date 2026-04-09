from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Address(BaseModel):
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=255, blank=True)
    map_link = models.URLField(blank=True)

    def __str__(self):
        return f"{self.address_line1}, {self.city} - {self.pincode}"

    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.pincode])
        if self.landmark:
            parts.append(f"Landmark: {self.landmark}")
        return ", ".join(parts)


class Branch(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='branches')
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    is_main_branch = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_main_branch:
            Branch.objects.filter(is_main_branch=True).exclude(id=self.id).update(is_main_branch=False)
        super().save(*args, **kwargs)


class ActivityLog(BaseModel):
    user_id = models.IntegerField(null=True, blank=True)
    user_email = models.CharField(max_length=150, blank=True)
    user_role = models.CharField(max_length=20, blank=True)
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100, blank=True, null=True)  # Add null=True
    object_id = models.CharField(max_length=50, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Activity logs"

    def __str__(self):
        return f"{self.user_email} - {self.action} - {self.created_at}"


class SystemConfig(BaseModel):
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    is_editable = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "System configurations"

    def __str__(self):
        return self.config_key

    @classmethod
    def get_value(cls, key, default=None):
        try:
            config = cls.objects.get(config_key=key)
            return config.config_value
        except cls.DoesNotExist:
            return default