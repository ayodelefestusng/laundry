# Generated manually for Feeder to Transformer migration

import django.db.models.deletion
from django.db import migrations, models


def move_feeder_transformers_forward(apps, schema_editor):
    """
    Data migration: Copies transformer_name and transformer_code from myapp_feeder
    into the new myapp_transformer table, linking each transformer to its feeder.
    """
    connection = schema_editor.connection
    Transformer = apps.get_model('myapp', 'Transformer')

    with connection.cursor() as cursor:
        columns = [
            col.name.lower()
            for col in connection.introspection.get_table_description(cursor, 'myapp_feeder')
        ]
        has_tf_name = 'transformer_name' in columns
        has_tf_code = 'transformer_code' in columns

        if has_tf_name or has_tf_code:
            name_expr = "transformer_name" if has_tf_name else "name"
            code_expr = "transformer_code" if has_tf_code else "name"
            cursor.execute(f"SELECT id, name, {name_expr}, {code_expr} FROM myapp_feeder")
            rows = cursor.fetchall()

            for feeder_id, f_name, tf_name, tf_code in rows:
                resolved_name = (tf_name or f_name or "UNKNOWN_TRANSFORMER").strip()
                resolved_code = (tf_code or "UNKNOWN_TRANSFORMER").strip()

                if not Transformer.objects.filter(feeder_id=feeder_id, transformer_code=resolved_code).exists():
                    Transformer.objects.create(
                        feeder_id=feeder_id,
                        name=resolved_name,
                        transformer_code=resolved_code,
                        is_active=True,
                    )


def move_feeder_transformers_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0047_powerstatus_event_id_powerstatus_whatsapp_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transformer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('transformer_code', models.CharField(help_text='e.g., DT01', max_length=100)),
                ('admin_main', models.EmailField(blank=True, max_length=254, null=True)),
                ('admin_secondary', models.EmailField(blank=True, max_length=254, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('feeder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transformers', to='myapp.feeder')),
            ],
            options={
                'unique_together': {('feeder', 'transformer_code')},
            },
        ),
        migrations.RunPython(
            move_feeder_transformers_forward,
            reverse_code=move_feeder_transformers_reverse,
        ),
        migrations.RemoveField(
            model_name='feeder',
            name='transformer_name',
        ),
        migrations.RemoveField(
            model_name='feeder',
            name='transformer_code',
        ),
    ]

