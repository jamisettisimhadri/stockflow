"""
Django models for StockFlow inventory management.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager using email as the unique identifier."""
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as the primary identifier."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]


class Organization(models.Model):
    """An organization that owns inventory and belongs to one user."""

    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='organization',
    )
    name = models.CharField(max_length=255)
    default_low_stock_threshold = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        help_text='Default threshold applied to products without their own threshold.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name


class Product(models.Model):
    """A product belonging to an organization's inventory."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products',
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity_on_hand = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    low_stock_threshold = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='If blank, uses the organization default threshold.',
    )
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_products',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        unique_together = [('organization', 'sku')]
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def get_effective_threshold(self):
        """Return the applicable low-stock threshold for this product."""
        if self.low_stock_threshold is not None:
            return self.low_stock_threshold
        return self.organization.default_low_stock_threshold

    def is_low_stock(self):
        """Return True if this product's quantity is at or below its threshold."""
        return self.quantity_on_hand <= self.get_effective_threshold()

    def inventory_value(self):
        """Return the total inventory value (quantity * cost_price) if cost is set."""
        if self.cost_price is not None:
            return self.quantity_on_hand * self.cost_price
        return None
