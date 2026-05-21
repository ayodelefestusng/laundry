from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        import myapp.signals
        try:
            self.schedule_daily_power_updates()
        except Exception as e:
            logger.warning(f"Could not programmatically schedule daily power updates: {e}", exc_info=True)

    def schedule_daily_power_updates(self):
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        import pytz

        lagos_tz = pytz.timezone("Africa/Lagos")
        
        # Create or retrieve the crontab for 00:01 daily (Lagos time)
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='1',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=lagos_tz
        )
        
        # Create or update the PeriodicTask
        PeriodicTask.objects.update_or_create(
            name="Daily Power Summary Updates",
            defaults={
                'crontab': schedule,
                'task': 'myapp.tasks.send_daily_power_updates',
            }
        )
        logger.info("Programmatically verified/created daily power updates schedule.")
