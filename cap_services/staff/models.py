from django.db import models
from django.utils import timezone
from core.models import BaseModel
from core.enums import TaskType, TaskStatus, ServiceStatus
from accounts.models import User
from orders.models import Order
from store.models import Product
import random
import string


class ServiceBooking(BaseModel):
    """Service booking by customers"""
    booking_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='service_bookings')
    
    device_type = models.CharField(max_length=100)
    device_model = models.CharField(max_length=100, blank=True)
    issue_description = models.TextField()
    
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=255, blank=True)
    map_link = models.URLField(blank=True)
    
    preferred_date = models.DateField()
    preferred_time_slot = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=20, choices=ServiceStatus.choices, default=ServiceStatus.REQUESTED)
    assigned_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_services', limit_choices_to={'role': 'STAFF'})
    
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    technician_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.booking_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.booking_number:
            prefix = 'SVC'
            timestamp = timezone.now().strftime('%y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.booking_number = f"{prefix}{timestamp}{random_str}"
        super().save(*args, **kwargs)

    def update_status(self, new_status, user, notes=""):
        if self.status != new_status:
            old_status = self.status
            self.status = new_status
            self.save()
            
            ServiceStatusHistory.objects.create(
                service=self,
                status=new_status,
                changed_by=user,
                notes=notes
            )


class ServiceStatusHistory(BaseModel):
    """Track service status changes"""
    service = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=ServiceStatus.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Service status histories"

    def __str__(self):
        return f"{self.service.booking_number} - {self.status}"


class StaffTask(BaseModel):
    """Tasks assigned to staff members"""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', limit_choices_to={'role': 'STAFF'})
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.ASSIGNED)
    
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_tasks')
    service = models.ForeignKey(ServiceBooking, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_tasks')
    
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    priority = models.PositiveSmallIntegerField(default=2, choices=[
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    ])
    
    notes = models.TextField(blank=True)
    completion_notes = models.TextField(blank=True)
    customer_rating = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(1,1),(2,2),(3,3),(4,4),(5,5)])
    customer_feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-priority', 'assigned_at']

    def __str__(self):
        task_for = self.order or self.service
        return f"{self.get_task_type_display()} - {task_for} - {self.staff.email}"

    @property
    def customer(self):
        if self.order:
            return self.order.user
        elif self.service:
            return self.service.user
        return None

    @property
    def customer_name(self):
        if self.customer:
            return self.customer.full_name
        return None

    @property
    def customer_phone(self):
        if self.customer:
            return self.customer.phone
        return None

    @property
    def customer_address(self):
        if self.order and self.order.shipping_address:
            return self.order.shipping_address.address
        elif self.service:
            return {
                'address_line1': self.service.address_line1,
                'address_line2': self.service.address_line2,
                'city': self.service.city,
                'state': self.service.state,
                'pincode': self.service.pincode,
                'landmark': self.service.landmark,
            }
        return None

    def accept(self):
        self.status = TaskStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

    def start(self):
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()

    def complete(self, notes=""):
        self.status = TaskStatus.COMPLETED
        self.completed_at = timezone.now()
        self.completion_notes = notes
        self.save()
        
        if self.order:
            self.order.update_status('DELIVERED', self.staff, "Delivered by staff")
        elif self.service:
            self.service.update_status('COMPLETED', self.staff, "Service completed by staff")


class StaffTracking(BaseModel):
    """Live location tracking for staff"""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_tracking', limit_choices_to={'role': 'STAFF'})
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    accuracy = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Staff Tracking"

    def __str__(self):
        return f"{self.staff.email} - {self.created_at}"

    @property
    def map_url(self):
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"


class StaffShift(BaseModel):
    """Staff work shifts"""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts', limit_choices_to={'role': 'STAFF'})
    shift_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, related_name='staff_shifts')
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-shift_date', 'start_time']

    def __str__(self):
        return f"{self.staff.email} - {self.shift_date}"

    @property
    def is_active(self):
        return self.clock_in and not self.clock_out

    def clock_in_now(self):
        self.clock_in = timezone.now()
        self.save()

    def clock_out_now(self):
        self.clock_out = timezone.now()
        self.save()


class StaffPerformance(BaseModel):
    """Track staff performance metrics"""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance', limit_choices_to={'role': 'STAFF'})
    period_start = models.DateField()
    period_end = models.DateField()
    
    tasks_assigned = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_on_time = models.PositiveIntegerField(default=0)
    tasks_late = models.PositiveIntegerField(default=0)
    
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    incentive_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-period_start']
        unique_together = ['staff', 'period_start', 'period_end']

    def __str__(self):
        return f"{self.staff.email} - {self.period_start} to {self.period_end}"

    @property
    def completion_rate(self):
        if self.tasks_assigned > 0:
            return (self.tasks_completed / self.tasks_assigned) * 100
        return 0

    @property
    def on_time_rate(self):
        if self.tasks_completed > 0:
            return (self.tasks_on_time / self.tasks_completed) * 100
        return 0

class Department(BaseModel):
    """Department types for staff"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-building', help_text="FontAwesome icon class")
    color = models.CharField(max_length=20, default='#3b82f6', help_text="Department color code")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class StaffDepartment(BaseModel):
    """Staff to Department mapping (Many-to-Many with extra data)"""
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_departments', limit_choices_to={'role': 'STAFF'})
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='staff_members')
    is_primary = models.BooleanField(default=False, help_text="Primary department for this staff")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_departments')
    
    class Meta:
        unique_together = ['staff', 'department']
        ordering = ['-is_primary', 'assigned_at']
    
    def __str__(self):
        return f"{self.staff.email} - {self.department.name}"