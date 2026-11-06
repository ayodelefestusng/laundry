from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0049_incidentsequence_incident_dailyfeedermetric"),
    ]

    operations = [
        migrations.AddField(
            model_name="feeder",
            name="publication_status",
            field=models.CharField(
                choices=[("publish", "Publish"), ("unpublish", "Unpublish")],
                default="publish",
                help_text="Controls public visibility across dashboards and reporting forms",
                max_length=20,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name="transformer",
            name="publication_status",
            field=models.CharField(
                choices=[("publish", "Publish"), ("unpublish", "Unpublish")],
                default="publish",
                help_text="Controls public visibility across dashboards and reporting forms",
                max_length=20,
                db_index=True,
            ),
        ),
    ]

