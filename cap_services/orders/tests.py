from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from store.models import Category, Product, Inventory
from .models import Cart, CartItem, Order, Coupon


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@example.com')
        self.user.set_password('pass123')
        self.user.save()
        
        self.category = Category.objects.create(name='Laptops')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Laptop',
            price=50000,
            sku='LAP123'
        )
        Inventory.objects.create(product=self.product, quantity=50)

    def test_add_to_cart(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        self.assertEqual(cart.item_count, 2)
        self.assertEqual(cart.subtotal, 100000)

    def test_cart_total(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, price=50000)
        self.assertEqual(cart.total, 50000)


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@example.com')
        self.user.set_password('pass123')
        self.user.save()

    def test_create_order(self):
        order = Order.objects.create(
            user=self.user,
            subtotal=50000,
            total=50000
        )
        self.assertTrue(order.order_number)
        self.assertEqual(order.status, 'PLACED')


class CartViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@example.com')
        self.user.set_password('pass123')
        self.user.save()
        
        self.category = Category.objects.create(name='Laptops')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Laptop',
            price=50000,
            sku='LAP123'
        )
        Inventory.objects.create(product=self.product, quantity=50)

    def test_cart_detail_view(self):
        session = self.client.session
        session.save()
        
        response = self.client.get(reverse('orders:cart_detail'))
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart(self):
        self.client.post(reverse('accounts:login'), {
            'email': 'test@example.com',
            'password': 'pass123'
        })
        
        response = self.client.post(reverse('orders:cart_add', args=[self.product.id]), {
            'quantity': 2
        })
        self.assertRedirects(response, reverse('orders:cart_detail'))


class CouponTest(TestCase):
    def setUp(self):
        self.coupon = Coupon.objects.create(
            code='SAVE10',
            discount_type='PERCENT',
            discount_value=10,
            valid_from='2024-01-01',
            valid_to='2025-12-31',
            max_uses=100
        )

    def test_coupon_valid(self):
        self.assertTrue(self.coupon.is_valid)

    def test_coupon_str(self):
        self.assertEqual(str(self.coupon), 'SAVE10')