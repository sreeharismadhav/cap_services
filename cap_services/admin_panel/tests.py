from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from .models import AdminAlert


class AdminPanelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            email='admin@example.com',
            role='ADMIN'
        )
        self.admin.set_password('admin123')
        self.admin.save()
        
        self.customer = User.objects.create(
            email='customer@example.com',
            role='CUSTOMER'
        )
        self.customer.set_password('pass123')
        self.customer.save()

    def test_admin_alert_creation(self):
        alert = AdminAlert.objects.create(
            title='Test Alert',
            message='This is a test alert',
            alert_type='INFO'
        )
        self.assertEqual(alert.title, 'Test Alert')
        self.assertEqual(str(alert), f'Test Alert - {alert.created_at}')

    def test_admin_dashboard_access_denied_for_customer(self):
        self.client.post(reverse('accounts:login'), {
            'email': 'customer@example.com',
            'password': 'pass123'
        })
        response = self.client.get(reverse('admin_panel:dashboard'))
        # Should redirect or return 403
        self.assertNotEqual(response.status_code, 200)

    def test_admin_dashboard_access_granted_for_admin(self):
        self.client.post(reverse('accounts:login'), {
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)