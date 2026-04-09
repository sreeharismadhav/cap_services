from django.test import TestCase
from .utils import generate_otp, format_price, mask_email, mask_phone, validate_indian_phone, validate_pincode


class CoreUtilsTest(TestCase):
    def test_generate_otp(self):
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
    
    def test_format_price(self):
        self.assertEqual(format_price(1000), '₹1,000.00')
        self.assertEqual(format_price(None), '₹0')
    
    def test_mask_email(self):
        self.assertEqual(mask_email('test@example.com'), 't***@example.com')
        self.assertEqual(mask_email('a@b.com'), 'a*@b.com')
    
    def test_mask_phone(self):
        self.assertEqual(mask_phone('9876543210'), '987****3210')
    
    def test_validate_indian_phone(self):
        self.assertTrue(validate_indian_phone('9876543210'))
        self.assertFalse(validate_indian_phone('1234567890'))
    
    def test_validate_pincode(self):
        self.assertTrue(validate_pincode('560001'))
        self.assertFalse(validate_pincode('56001'))