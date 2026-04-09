from django.db import models


class ProductManager(models.Manager):
    """Custom manager for Product model"""
    
    def active(self):
        """Return only active products"""
        return self.filter(status='ACTIVE', is_active=True)
    
    def featured(self):
        """Return featured products"""
        return self.active().filter(is_featured=True)
    
    def bestsellers(self):
        """Return bestseller products"""
        return self.active().filter(is_bestseller=True)
    
    def in_stock(self):
        """Return products with stock available"""
        return self.active().filter(inventory__available__gt=0)
    
    def by_category(self, category_slug):
        """Return products by category slug"""
        return self.active().filter(category__slug=category_slug)
    
    def search(self, query):
        """Search products by name or description"""
        return self.active().filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        )
    
    def price_range(self, min_price, max_price):
        """Filter products by price range"""
        return self.active().filter(price__gte=min_price, price__lte=max_price)


class CategoryManager(models.Manager):
    """Custom manager for Category model"""
    
    def active(self):
        """Return only active categories"""
        return self.filter(is_active=True)
    
    def main_categories(self):
        """Return main categories (no parent)"""
        return self.active().filter(parent__isnull=True)
    
    def subcategories(self, parent_id):
        """Return subcategories of a parent"""
        return self.active().filter(parent_id=parent_id)