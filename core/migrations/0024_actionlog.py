from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_update_sms_unique_constraint'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('action_id', models.AutoField(primary_key=True, serialize=False)),
                ('role', models.CharField(blank=True, max_length=20)),
                ('action', models.CharField(max_length=150)),
                ('details', models.TextField(blank=True)),
                ('ip_address', models.CharField(blank=True, max_length=45)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.appuser')),
            ],
            options={
                'db_table': 'action_logs',
                'ordering': ('-created_at',),
            },
        ),
    ]

