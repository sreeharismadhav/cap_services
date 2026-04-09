from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer'
    STAFF = 'STAFF', 'Staff'
    ADMIN = 'ADMIN', 'Admin'


class OrderStatus(models.TextChoices):
    PLACED = 'PLACED', 'Placed'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PROCESSING = 'PROCESSING', 'Processing'
    SHIPPED = 'SHIPPED', 'Shipped'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'
    RETURNED = 'RETURNED', 'Returned'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'


class PaymentMethod(models.TextChoices):
    UPI = 'UPI', 'UPI'
    CARD = 'CARD', 'Card'
    NETBANKING = 'NETBANKING', 'Net Banking'
    CASH = 'CASH', 'Cash'


class TaskType(models.TextChoices):
    DELIVERY = 'DELIVERY', 'Delivery'
    PICKUP = 'PICKUP', 'Pickup'
    SERVICE = 'SERVICE', 'Service'


class TaskStatus(models.TextChoices):
    ASSIGNED = 'ASSIGNED', 'Assigned'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class ServiceStatus(models.TextChoices):
    REQUESTED = 'REQUESTED', 'Requested'
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class ReturnStatus(models.TextChoices):
    REQUESTED = 'REQUESTED', 'Requested'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    REFUNDED = 'REFUNDED', 'Refunded'


class CouponType(models.TextChoices):
    PERCENT = 'PERCENT', 'Percentage'
    FIXED = 'FIXED', 'Fixed Amount'


class ProductStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    ACTIVE = 'ACTIVE', 'Active'
    OUT_OF_STOCK = 'OUT_OF_STOCK', 'Out of Stock'
    DISCONTINUED = 'DISCONTINUED', 'Discontinued'


class AddressType(models.TextChoices):
    HOME = 'HOME', 'Home'
    OFFICE = 'OFFICE', 'Office'
    OTHER = 'OTHER', 'Other'


class InventoryChangeType(models.TextChoices):
    PURCHASE = 'PURCHASE', 'Purchase'
    SALE = 'SALE', 'Sale'
    RETURN = 'RETURN', 'Return'
    ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
    RESERVE = 'RESERVE', 'Reserve'
    RELEASE = 'RELEASE', 'Release'

class ReportType(models.TextChoices):
    SALES = 'SALES', 'Sales Report'
    INVENTORY = 'INVENTORY', 'Inventory Report'
    STAFF = 'STAFF', 'Staff Performance'
    CUSTOMER = 'CUSTOMER', 'Customer Analytics'
    FINANCIAL = 'FINANCIAL', 'Financial Report'


class AlertType(models.TextChoices):
    INFO = 'INFO', 'Info'
    WARNING = 'WARNING', 'Warning'
    ERROR = 'ERROR', 'Error'
    SUCCESS = 'SUCCESS', 'Success'