from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
try:
    from myapp.models import TenantAttribute, Cluster, DeliveryPricing, ServiceCategory, Package, ServiceChoices, CustomUser, Employee
except ImportError:
    pass

class Command(BaseCommand):
    help = 'Create Partner group and assign standard permissions'

    def handle(self, *args, **kwargs):
        group, created = Group.objects.get_or_create(name='Partner')
        
        models_to_permit = [
            TenantAttribute, Cluster, DeliveryPricing, 
            ServiceCategory, Package, ServiceChoices, Employee, CustomUser
        ]
        
        for model in models_to_permit:
            try:
                content_type = ContentType.objects.get_for_model(model)
                permissions = Permission.objects.filter(content_type=content_type)
                for p in permissions:
                    # Filter out delete permission for CustomUser to prevent them from deleting other partners
                    if model == CustomUser and p.codename.startswith('delete'):
                        continue
                    group.permissions.add(p)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not assign permission for {model.__name__}: {e}"))
                
        self.stdout.write(self.style.SUCCESS("Partner group created and permissions seeded successfully."))
