# Generated manually to fix varchar(50) DataError on whatsapp_primary and whatsapp_group

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0045_pearl_dt_three_phase_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feeder",
            name="whatsapp_primary",
            field=models.CharField(
                blank=True,
                default="2348021299221, 2348108383472",
                help_text="Comma-separated primary WhatsApp numbers (e.g. 2348021299221, 2348108383472)",
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="feeder",
            name="whatsapp_group",
            field=models.CharField(
                blank=True,
                default="120363410539285836@g.us, 120363429032532411@g.us",
                help_text="Comma-separated WhatsApp group IDs (e.g. 120363410539285836@g.us, 120363429032532411@g.us)",
                max_length=255,
                null=True,
            ),
        ),
    ]
