from django.db import models
from core.models import BaseModel
from core.enums import ReportType, AlertType
from accounts.models import User


class AdminPreference(BaseModel):
    """Admin dashboard preferences"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='admin_preferences',
        limit_choices_to={'role': 'ADMIN'}
    )
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])
    default_dashboard = models.CharField(max_length=50, default='main', choices=[
        ('main', 'Main Dashboard'),
        ('sales', 'Sales Dashboard'),
        ('inventory', 'Inventory Dashboard'),
        ('staff', 'Staff Dashboard'),
    ])
    widget_order = models.JSONField(default=list)
    collapsed_sidebar = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - Preferences"


class AdminAlert(BaseModel):
    """System alerts for admins"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=AlertType.choices, default=AlertType.INFO)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, blank=True, related_name='read_alerts')
    link = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.created_at}"


class SystemReport(BaseModel):
    """Generated reports for admin"""
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    title = models.CharField(max_length=200)
    data = models.JSONField(default=dict)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_reports'
    )
    period_start = models.DateField()
    period_end = models.DateField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start} to {self.period_end}"


class DashboardWidget(BaseModel):
    """Customizable dashboard widgets"""
    name = models.CharField(max_length=100)
    widget_key = models.CharField(max_length=50, unique=True)
    widget_type = models.CharField(max_length=50, choices=[
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('counter', 'Counter'),
        ('list', 'List'),
    ])
    config = models.JSONField(default=dict)
    is_enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class AuditLog(BaseModel):
    """Admin audit log for tracking changes"""
    admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='admin_audit_logs',
        limit_choices_to={'role': 'ADMIN'}
    )
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Audit logs"

    def __str__(self):
        return f"{self.admin.email if self.admin else 'System'} - {self.action} - {self.created_at}"


class Announcement(BaseModel):
    """System announcements shown to users"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Critical'),
    ], default='info')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    target_roles = models.JSONField(default=list, help_text="['CUSTOMER', 'STAFF', 'ADMIN']")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    @property
    def is_current(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date