from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from .models import StaffTask, ServiceBooking, StaffShift
from core.enums import TaskType, TaskStatus, ServiceStatus


class StaffTaskModelTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create(
            email='staff@example.com',
            role='STAFF'
        )
        self.staff.set_password('pass123')
        self.staff.save()

    def test_create_task(self):
        task = StaffTask.objects.create(
            staff=self.staff,
            task_type=TaskType.DELIVERY,
            priority=2
        )
        self.assertEqual(task.status, TaskStatus.ASSIGNED)
        self.assertEqual(task.get_task_type_display(), 'Delivery')


class ServiceBookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='customer@example.com')
        self.user.set_password('pass123')
        self.user.save()

    def test_create_booking(self):
        booking = ServiceBooking.objects.create(
            user=self.user,
            device_type='Laptop',
            issue_description='Not turning on',
            address_line1='123 Main St',
            city='Bangalore',
            state='Karnataka',
            pincode='560001',
            preferred_date=timezone.now().date()
        )
        self.assertTrue(booking.booking_number)
        self.assertEqual(booking.status, ServiceStatus.REQUESTED)