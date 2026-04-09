import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.conf import settings
from orders.models import Order, Invoice
import random
import string
from datetime import datetime
from weasyprint import HTML

def generate_invoice_number():
    """Generate unique invoice number"""
    prefix = 'INV'
    timestamp = datetime.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}{timestamp}{random_str}"

class Command(BaseCommand):
    help = 'Generate PDF invoices for all existing orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate invoices even if they already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Get orders without invoices, or all orders if force=True
        if force:
            orders = Order.objects.all()
            # Delete existing invoices if regenerating
            Invoice.objects.all().delete()
            self.stdout.write(self.style.WARNING('Deleted all existing invoices'))
        else:
            orders = Order.objects.filter(invoice__isnull=True)
        
        self.stdout.write(f'Found {orders.count()} orders to process')
        
        company_email = getattr(settings, 'SITE_EMAIL', 'capservicers@gmail.com')
        company_phone = getattr(settings, 'SITE_PHONE', '7510158899')
        
        created_count = 0
        failed_count = 0
        
        for order in orders:
            try:
                # Create invoice record
                invoice_number = generate_invoice_number()
                invoice = Invoice.objects.create(
                    order=order,
                    invoice_number=invoice_number
                )
                
                # Generate PDF from HTML template
                html_string = render_to_string('orders/invoice_pdf_template.html', {
                    'invoice': invoice,
                    'order': order,
                    'company_email': company_email,
                    'company_phone': company_phone,
                })
                
                # Convert HTML to PDF
                pdf_file = HTML(string=html_string).write_pdf()
                
                # Save PDF to model
                pdf_filename = f"invoice_{invoice_number}.pdf"
                invoice.pdf_file.save(pdf_filename, ContentFile(pdf_file), save=True)
                
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Generated invoice {invoice_number} for Order #{order.order_number}'
                ))
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f'✗ Failed to generate invoice for Order #{order.order_number}: {str(e)}'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Generated {created_count} invoices. Failed: {failed_count}'
        ))

        # Show summary
        self.stdout.write(f'\nTotal orders: {Order.objects.count()}')
        self.stdout.write(f'Orders with PDF invoices: {Invoice.objects.exclude(pdf_file="").count()}')