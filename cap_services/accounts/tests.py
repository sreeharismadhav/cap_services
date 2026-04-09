from django.test import TestCase
from .models import User


class AccountsTest(TestCase):
    def test_create_user(self):
        user = User.objects.create(
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        user.set_password('testpass123')
        user.save()
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))