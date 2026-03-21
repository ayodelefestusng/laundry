from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import WorkflowInstance, WorkflowHistory, OrderItem
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Checks SLA for workflow instances and escalates if necessary.'

    def handle(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(OrderItem)
        active_instances = WorkflowInstance.objects.filter(content_type=ct, completed_at__isnull=True)
        
        escalated_count = 0

        for instance in active_instances:
            item = instance.target
            stage = instance.current_stage
            if not stage:
                continue
                
            turnaround_hours = stage.turnaround_time
            
            last_history = WorkflowHistory.objects.filter(item=item).order_by('-timestamp').first()
            if last_history and last_history.action == "Escalate":
                continue 

            start_time = last_history.timestamp if last_history else instance.created_at
            
            if timezone.now() > start_time + timedelta(hours=turnaround_hours):
                officer = stage.responsible_officer
                if officer:
                    emails = []
                    if officer.user.email:
                        emails.append(officer.user.email)
                    if officer.line_manager and officer.line_manager.user.email:
                        emails.append(officer.line_manager.user.email)
                    if officer.deputy_person and officer.deputy_person.user.email:
                        emails.append(officer.deputy_person.user.email)
                        
                    if emails:
                        send_mail(
                            'SLA Exceeded - Escalation Notice',
                            f'Order Item {item.name} (Order {item.order.order_code if hasattr(item.order, "order_code") else item.order.id}) has exceeded its SLA at stage {stage.sequence}. Please take immediate action.',
                            settings.DEFAULT_FROM_EMAIL,
                            emails,
                            fail_silently=True,
                        )
                    
                    WorkflowHistory.objects.create(
                        item=item,
                        from_stage=stage.service_action.name if stage.service_action else f"Stage {stage.sequence}",
                        to_stage=stage.service_action.name if stage.service_action else f"Stage {stage.sequence} (Escalated)",
                        actor=officer.line_manager or officer,
                        action="Escalate"
                    )
                    escalated_count += 1
                    
        self.stdout.write(self.style.SUCCESS(f"SLA Check complete. Escalated {escalated_count} items."))
