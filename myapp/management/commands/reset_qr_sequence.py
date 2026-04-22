from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Reset the QR sequence to continue from the max existing ID'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get max ID from QR table
            cursor.execute('SELECT MAX(id) FROM myapp_qr')
            max_id = cursor.fetchone()[0] or 0
            self.stdout.write(f'Max QR ID: {max_id}')
            
            # Reset sequence to max_id + 1
            cursor.execute(f"SELECT setval('myapp_qr_id_seq', {max_id}, true)")
            self.stdout.write(self.style.SUCCESS(f'Sequence reset to {max_id + 1}'))