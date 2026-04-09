from django.test import TestCase
from django.urls import reverse
from .models import Category, Product, Brand, Inventory
from accounts.models import User


class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(
            name='Laptops',
            description='All kinds of laptops'
        )
        self.assertEqual(category.name, 'Laptops')
        self.assertTrue(category.slug)

    def test_category_str(self):
        category = Category.objects.create(name='Printers')
        self.assertEqual(str(category), 'Printers')


class BrandModelTest(TestCase):
    def test_create_brand(self):
        brand = Brand.objects.create(name='HP')
        self.assertEqual(brand.name, 'HP')
        self.assertTrue(brand.slug)

    def test_brand_str(self):
        brand = Brand.objects.create(name='Dell')
        self.assertEqual(str(brand), 'Dell')


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Laptops')
        self.brand = Brand.objects.create(name='Asus')
        
    def test_create_product(self):
        product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name='Gaming Laptop',
            price=65000,
            sku='LAP123'
        )
        self.assertEqual(product.name, 'Gaming Laptop')
        self.assertEqual(product.price, 65000)
        self.assertTrue(product.slug)
        self.assertTrue(product.sku)

    def test_current_price_without_discount(self):
        product = Product.objects.create(
            category=self.category,
            name='Office Laptop',
            price=45000
        )
        self.assertEqual(product.current_price, 45000)

    def test_current_price_with_discount(self):
        product = Product.objects.create(
            category=self.category,
            name='Gaming Laptop',
            price=70000,
            discounted_price=60000
        )
        self.assertEqual(product.current_price, 60000)
        self.assertEqual(product.discount_percentage, 14)

    def test_product_str(self):
        product = Product.objects.create(
            category=self.category,
            name='MacBook Air'
        )
        self.assertEqual(str(product), 'MacBook Air')


class InventoryModelTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Laptops')
        self.product = Product.objects.create(
            category=category,
            name='Test Laptop'
        )

    def test_inventory_creation(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=50
        )
        self.assertEqual(inventory.quantity, 50)
        self.assertEqual(inventory.reserved, 0)

    def test_available_stock(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=50,
            reserved=10
        )
        self.assertEqual(inventory.available, 40)

    def test_is_low_stock(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=3,
            low_stock_threshold=5
        )
        self.assertTrue(inventory.is_low_stock)

    def test_reserve_stock(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=50
        )
        result = inventory.reserve(10)
        self.assertTrue(result)
        self.assertEqual(inventory.reserved, 10)
        self.assertEqual(inventory.available, 40)

    def test_reserve_stock_insufficient(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=5
        )
        result = inventory.reserve(10)
        self.assertFalse(result)
        self.assertEqual(inventory.reserved, 0)

    def test_release_stock(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=50,
            reserved=20
        )
        inventory.release(10)
        self.assertEqual(inventory.reserved, 10)

    def test_deduct_stock(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=50,
            reserved=10
        )
        result = inventory.deduct(20)
        self.assertTrue(result)
        self.assertEqual(inventory.quantity, 30)
        self.assertEqual(inventory.reserved, 0)

    def test_deduct_stock_insufficient(self):
        inventory = Inventory.objects.create(
            product=self.product,
            quantity=10
        )
        result = inventory.deduct(20)
        self.assertFalse(result)


class ProductListViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Laptops')
        Product.objects.create(
            category=category,
            name='Product 1',
            price=10000,
            status='ACTIVE'
        )
        Product.objects.create(
            category=category,
            name='Product 2',
            price=20000,
            status='ACTIVE'
        )

    def test_product_list_view(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Product 1')
        self.assertContains(response, 'Product 2')


class ProductDetailViewTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Laptops')
        self.product = Product.objects.create(
            category=category,
            name='Test Laptop',
            slug='test-laptop',
            price=50000,
            status='ACTIVE'
        )

    def test_product_detail_view(self):
        response = self.client.get(reverse('store:product_detail', args=['test-laptop']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Laptop')