import logging
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from myapp.models import Tenant, Package, Cluster, Color, ServiceCategory, ServiceChoices

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Duplicates Package, Cluster, and Color records from one tenant to another (DMC to BigFish)'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, default='DMC', help='Source tenant code')
        parser.add_argument('--target', type=str, default='BigFish', help='Target tenant code')

    def handle(self, *args, **options):
        source_code = options['source']
        target_code = options['target']

        try:
            source_tenant = Tenant.objects.get(code=source_code)
            target_tenant = Tenant.objects.get(code=target_code)
        except Tenant.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Error: Tenant with code provided not found. {e}"))
            return

        self.stdout.write(self.style.NOTICE(f"Starting duplication from '{source_code}' to '{target_code}'..."))

        with transaction.atomic():
            # 1. Duplicate Colors
            colors = Color.all_objects.filter(tenant=source_tenant)
            color_count = 0
            for color in colors:
                _, created = Color.all_objects.get_or_create(
                    tenant=target_tenant,
                    name=color.name,
                    defaults={'hex_code': color.hex_code}
                )
                if created:
                    color_count += 1
            self.stdout.write(f"Created {color_count} Color records.")

            # 2. Duplicate Clusters
            clusters = Cluster.all_objects.filter(tenant=source_tenant)
            cluster_count = 0
            for cluster in clusters:
                new_cluster, created = Cluster.all_objects.get_or_create(
                    tenant=target_tenant,
                    name=cluster.name
                )
                if created:
                    new_cluster.towns.set(cluster.towns.all())
                    cluster_count += 1
            self.stdout.write(f"Created {cluster_count} Cluster records (with town associations).")

            # 3. Duplicate ServiceCategories and ServiceChoices (dependencies for Package)
            # These might be strictly unique by name, so we handle potential IntegrityErrors
            category_map = {}
            for sc in ServiceCategory.all_objects.filter(tenant=source_tenant):
                try:
                    new_sc, created = ServiceCategory.all_objects.get_or_create(
                        tenant=target_tenant,
                        name=sc.name
                    )
                    category_map[sc.id] = new_sc
                except IntegrityError:
                    # Fallback to existing if global/unique constraint prevents duplication
                    existing = ServiceCategory.all_objects.filter(name=sc.name).first()
                    category_map[sc.id] = existing
            
            choice_map = {}
            for sc in ServiceChoices.all_objects.filter(tenant=source_tenant):
                try:
                    new_sc, created = ServiceChoices.all_objects.get_or_create(
                        tenant=target_tenant,
                        name=sc.name
                    )
                    choice_map[sc.id] = new_sc
                except IntegrityError:
                    existing = ServiceChoices.all_objects.filter(name=sc.name).first()
                    choice_map[sc.id] = existing

            # 4. Duplicate Packages
            packages = Package.all_objects.filter(tenant=source_tenant)
            package_count = 0
            for pkg in packages:
                target_cat = category_map.get(pkg.category_id)
                target_choice = choice_map.get(pkg.service_type_id)

                if not target_cat:
                    continue # Should not happen with above logic

                try:
                    _, created = Package.all_objects.get_or_create(
                        tenant=target_tenant,
                        category=target_cat,
                        service_type=target_choice,
                        defaults={
                            'price': pkg.price,
                            'delivery_time_days': pkg.delivery_time_days
                        }
                    )
                    if created:
                        package_count += 1
                except IntegrityError:
                    self.stdout.write(self.style.WARNING(f"Could not duplicate Package {pkg}: Unique constraint violation (check models.py unique_together)."))

            self.stdout.write(self.style.SUCCESS(f"Created {package_count} Package records."))

        self.stdout.write(self.style.SUCCESS('Duplication process completed.'))
