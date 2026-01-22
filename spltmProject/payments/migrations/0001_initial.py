# Generated migration for EventCollectionTransaction model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
        ('accounts', '0002_alter_user_full_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventCollectionTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(1)])),
                ('transaction_type', models.CharField(choices=[('contribution', 'Contribution'), ('refund', 'Refund'), ('settlement', 'Settlement')], default='contribution', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('description', models.TextField(blank=True, null=True)),
                ('payment_method', models.CharField(blank=True, help_text='e.g., Cash, Card, UPI, Bank Transfer', max_length=50, null=True)),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'event_collection_transactions',
                'ordering': ['-transaction_date'],
            },
        ),
        migrations.AddIndex(
            model_name='eventcollectiontransaction',
            index=models.Index(fields=['event', 'status'], name='event_colle_event_status_idx'),
        ),
        migrations.AddIndex(
            model_name='eventcollectiontransaction',
            index=models.Index(fields=['user', 'status'], name='event_colle_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='eventcollectiontransaction',
            index=models.Index(fields=['event', 'user'], name='event_colle_event_user_idx'),
        ),
    ]
