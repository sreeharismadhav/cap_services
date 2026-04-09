from .models import Order, Invoice
from core.utils import generate_invoice_number
from django.template.loader import render_to_string
from django.core.files import File
import tempfile
import os


def generate_invoice_pdf(order):
    """Generate PDF invoice for order"""
    try:
        from weasyprint import HTML
        
        # Get or create invoice
        invoice, created = Invoice.objects.get_or_create(order=order)
        
        # Render HTML template
        context = {'order': order, 'invoice': invoice}
        html_string = render_to_string('orders/invoice_pdf.html', context)
        
        # Create PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            HTML(string=html_string).write_pdf(tmp_file.name)
            invoice.pdf_file.save(f'invoice_{invoice.invoice_number}.pdf', File(open(tmp_file.name, 'rb')))
            invoice.save()
        
        os.unlink(tmp_file.name)
        return invoice.pdf_file.url
        
    except ImportError:
        return None


def get_order_status_display(status):
    """Get display name for order status"""
    status_map = {
        'PLACED': 'Order Placed',
        'CONFIRMED': 'Confirmed',
        'PROCESSING': 'Processing',
        'SHIPPED': 'Shipped',
        'ASSIGNED': 'Assigned to Staff',
        'DELIVERED': 'Delivered',
        'CANCELLED': 'Cancelled',
    }
    return status_map.get(status, status)


def can_cancel_order(order):
    """Check if order can be cancelled"""
    cancel_statuses = ['PLACED', 'CONFIRMED', 'PROCESSING']
    return order.status in cancel_statuses