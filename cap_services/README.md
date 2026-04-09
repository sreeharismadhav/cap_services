# CAP Services - E-Commerce Platform

## 🚀 Overview
Web-based e-commerce platform for computer sales, delivery, and servicing.

## 🛠 Tech Stack
- Python 3.11.9
- Django 4.2.11
- SQLite/PostgreSQL
- Redis
- Celery
- Bootstrap 5

## 📦 Apps
1. **core** - Shared utilities, base models, enums
2. **accounts** - User authentication, profiles, addresses
3. **store** - Products, categories, inventory
4. **orders** - Cart, checkout, payments, invoices
5. **staff** - Staff tasks, assignments, tracking
6. **admin_panel** - Custom admin dashboard

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/cap_services.git
cd cap_services

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver