from django.core.management.base import BaseCommand
from myapp.models import Color, Tenant

COMMON_COLORS = [
    ("Black",        "#000000"),
    ("White",        "#FFFFFF"),
    ("Navy Blue",    "#001F5B"),
    ("Royal Blue",   "#4169E1"),
    ("Sky Blue",     "#87CEEB"),
    ("Red",          "#E3000F"),
    ("Maroon",       "#800000"),
    ("Burgundy",     "#800020"),
    ("Pink",         "#FF69B4"),
    ("Hot Pink",     "#FF1493"),
    ("Green",        "#008000"),
    ("Olive Green",  "#708238"),
    ("Mint Green",   "#98FF98"),
    ("Yellow",       "#FFD700"),
    ("Orange",       "#FF7F00"),
    ("Peach",        "#FFDAB9"),
    ("Brown",        "#8B4513"),
    ("Beige",        "#F5F5DC"),
    ("Cream",        "#FFFDD0"),
    ("Grey",         "#808080"),
    ("Charcoal",     "#36454F"),
    ("Silver",       "#C0C0C0"),
    ("Purple",       "#800080"),
    ("Lavender",     "#E6E6FA"),
    ("Indigo",       "#4B0082"),
    ("Teal",         "#008080"),
    ("Turquoise",    "#40E0D0"),
    ("Khaki",        "#C3B091"),
    ("Tan",          "#D2B48C"),
    ("Multicolor",   "#FF00FF"),
]


class Command(BaseCommand):
    help = "Seed common garment colors for all active tenants."

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Seed only for a specific tenant code (e.g. DMC). Defaults to all active tenants.',
        )

    def handle(self, *args, **options):
        tenant_code = options.get('tenant')
        if tenant_code:
            tenants = Tenant.objects.filter(code=tenant_code, is_active=True)
        else:
            tenants = Tenant.objects.filter(is_active=True)

        if not tenants.exists():
            self.stdout.write(self.style.WARNING("No active tenants found."))
            return

        created_total = 0
        for tenant in tenants:
            created_count = 0
            for name, hex_code in COMMON_COLORS:
                _, created = Color.objects.get_or_create(
                    name=name,
                    tenant=tenant,
                    defaults={'hex_code': hex_code}
                )
                if created:
                    created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"[{tenant.code}] {tenant.name}: {created_count} colors seeded ({len(COMMON_COLORS) - created_count} already existed).")
            )
            created_total += created_count

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created_total} total colors created across {tenants.count()} tenant(s)."))
