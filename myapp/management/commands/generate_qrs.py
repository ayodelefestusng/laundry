from django.core.management.base import BaseCommand
from myapp.models import QR, Tenant
from myapp.utils import get_signed_token
import uuid

import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


def generate_qr_image(code):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_pdf(qr_queryset, filename="qr_codes.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    cols = 5
    rows = 10
    margin = 35
    cell_width = (width - 2 * margin) / cols
    cell_height = (height - 2 * margin) / rows
    
    for i, qr in enumerate(qr_queryset):
        # Handle multiple pages if count > 40
        if i > 0 and i % (cols * rows) == 0:
            c.showPage()
            
        page_idx = i % (cols * rows)
        col = page_idx % cols
        row = page_idx // cols # 0 to 9
        
        # Calculate x, y (PDF y is from bottom)
        x = margin + col * cell_width
        y = height - margin - (row + 1) * cell_height
        
        img_data = generate_qr_image(qr.code)
        img = ImageReader(BytesIO(img_data))
        
        # Center QR in cell
        qr_size = 80
        pad_x = (cell_width - qr_size) / 2
        pad_y = (cell_height - qr_size) / 2 + 10 # room for text below
        
        c.drawImage(img, x + pad_x, y + pad_y, width=qr_size, height=qr_size)
        
        # Label below QR
        c.setFont("Helvetica", 6)
        # Use a shortened version if signed code is long
        display_code = (qr.code[:30] + '..') if len(qr.code) > 30 else qr.code
        c.drawCentredString(x + cell_width/2, y + pad_y - 12, display_code)

    c.save()


class Command(BaseCommand):
    help = 'Pre-generates QR codes for the Laundry system and outputs them to PDF.'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Number of QR codes to generate')
        parser.add_argument('--tenant', type=int, help='Tenant ID to assign QR codes to')

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        tenant_id = kwargs.get('tenant')

        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Tenant with id {tenant_id} does not exist."))
                return
        else:
            tenant = Tenant.objects.first()

        if not tenant:
            self.stderr.write(self.style.ERROR("No tenant found. Cannot create QR codes."))
            return

        qr_list = []
        for _ in range(count):
            raw_uuid = str(uuid.uuid4())
            signed_code = get_signed_token(raw_uuid)
            qr_list.append(QR(code=signed_code, tenant=tenant, status='unused'))

        QR.objects.bulk_create(qr_list)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully generated {len(qr_list)} QR codes for tenant {tenant.name}."
        ))

        # Generate PDF with the newly created QR codes
        qrs = QR.objects.filter(tenant=tenant).order_by('-id')[:count]
        filename = f"qr_codes_{tenant.name}.pdf"
        generate_qr_pdf(qrs, filename=filename)

        self.stdout.write(self.style.SUCCESS(
            f"PDF with {count} QR codes generated for tenant {tenant.name} at {filename}."
        ))

        # python manage.py generate_qrs 50
        # python manage.py generate_qrs 50 --tenant 1