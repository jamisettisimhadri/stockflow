# Generated migration for StockFlow inventory models

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import inventory.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
            managers=[
                ('objects', inventory.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('default_low_stock_threshold', models.PositiveIntegerField(
                    default=5,
                    help_text="Default threshold applied to products without their own threshold.",
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='organization',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Organization',
                'verbose_name_plural': 'Organizations',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('quantity_on_hand', models.IntegerField(
                    default=0,
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('cost_price', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=12,
                    null=True,
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('selling_price', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=12,
                    null=True,
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('low_stock_threshold', models.PositiveIntegerField(
                    blank=True,
                    help_text='If blank, uses the organization default threshold.',
                    null=True,
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_updated_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='updated_products',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='products',
                    to='inventory.organization',
                )),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'ordering': ['name'],
                'unique_together': {('organization', 'sku')},
            },
        ),
    ]
