# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_add_last_pricing_action_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Backup',
            fields=[
                ('backup_id', models.AutoField(primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=500)),
                ('file_size', models.BigIntegerField(help_text='File size in bytes')),
                ('backup_type', models.CharField(choices=[('full', 'Full Backup'), ('database', 'Database Only'), ('media', 'Media Only')], default='full', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('is_verified', models.BooleanField(default=False, help_text='Whether backup file still exists and is valid')),
            ],
            options={
                'verbose_name': 'Backup',
                'verbose_name_plural': 'Backups',
                'db_table': 'backups',
                'ordering': ['-created_at'],
            },
        ),
    ]

