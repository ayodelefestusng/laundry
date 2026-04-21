
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import Order, Cluster, Town, State

order_id = '2809394e-eec0-4a24-9301-48beb2e92d10'
try:
    order = Order.objects.get(id=order_id)
    tenant = order.tenant
    print(f"Order Tenant: {tenant}")
    
    clusters = Cluster.objects.filter(tenant=tenant)
    print(f"Clusters count: {clusters.count()}")
    
    towns_in_clusters = Town.objects.filter(clusters__in=clusters).distinct()
    print(f"Towns in clusters count: {towns_in_clusters.count()}")
    
    states = State.objects.filter(towns__in=towns_in_clusters).distinct().order_by("name")
    print(f"States count: {states.count()}")
    for s in states:
        print(f"- {s.name}")

except Exception as e:
    print(f"Error: {e}")
