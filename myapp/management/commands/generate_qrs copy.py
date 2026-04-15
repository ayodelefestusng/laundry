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

    x, y = 50, height - 100  # starting position
    for qr in qr_queryset:
        img_data = generate_qr_image(qr.code)
        img = ImageReader(BytesIO(img_data))
        c.drawImage(img, x, y, width=100, height=100)
        c.drawString(x, y - 15, f"Code: {qr.code}")

        # move down for next QR
        y -= 150
        if y < 100:  # new page if space runs out
            c.showPage()
            y = height - 100

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