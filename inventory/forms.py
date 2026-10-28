"""
Django forms for StockFlow inventory management.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Organization, Product

User = get_user_model()


class SignupForm(forms.Form):
    """Form for new user registration with organization creation."""

    organization_name = forms.CharField(
        max_length=255,
        label='Organization Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Acme Corp',
            'autofocus': True,
        }),
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jane',
        }),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Smith',
        }),
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
        }),
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'At least 8 characters',
        }),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                'An account with this email address already exists.'
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        if password1:
            try:
                validate_password(password1)
            except ValidationError as e:
                self.add_error('password1', e)

        return cleaned_data

    @transaction.atomic
    def save(self):
        """Create the user and organization in a single database transaction."""
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        org_name = self.cleaned_data['organization_name']

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        Organization.objects.create(owner=user, name=org_name)
        return user


class LoginForm(forms.Form):
    """Email and password login form."""

    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your password',
        }),
    )


class ProductForm(forms.ModelForm):
    """Form for creating and editing products."""

    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'description',
            'quantity_on_hand',
            'cost_price',
            'selling_price',
            'low_stock_threshold',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Wireless Keyboard',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. WK-001',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional product description',
            }),
            'quantity_on_hand': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '0',
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'e.g. 9.99',
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'e.g. 19.99',
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Leave blank to use organization default',
            }),
        }
        labels = {
            'quantity_on_hand': 'Quantity on Hand',
            'cost_price': 'Cost Price',
            'selling_price': 'Selling Price',
            'low_stock_threshold': 'Low-Stock Threshold (optional)',
        }
        help_texts = {
            'sku': 'Must be unique within your organization.',
            'low_stock_threshold': 'Leave blank to use your organization\'s default threshold.',
            'cost_price': 'Used to calculate total inventory value.',
        }

    def clean_quantity_on_hand(self):
        qty = self.cleaned_data.get('quantity_on_hand')
        if qty is not None and qty < 0:
            raise ValidationError('Quantity cannot be negative.')
        return qty

    def clean_cost_price(self):
        price = self.cleaned_data.get('cost_price')
        if price is not None and price < 0:
            raise ValidationError('Cost price cannot be negative.')
        return price

    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        if price is not None and price < 0:
            raise ValidationError('Selling price cannot be negative.')
        return price

    def clean_low_stock_threshold(self):
        threshold = self.cleaned_data.get('low_stock_threshold')
        if threshold is not None and threshold < 0:
            raise ValidationError('Low-stock threshold cannot be negative.')
        return threshold


class OrganizationSettingsForm(forms.ModelForm):
    """Form for updating organization settings."""

    class Meta:
        model = Organization
        fields = ['name', 'default_low_stock_threshold']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your organization name',
            }),
            'default_low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '5',
            }),
        }
        labels = {
            'name': 'Organization Name',
            'default_low_stock_threshold': 'Default Low-Stock Threshold',
        }
        help_texts = {
            'default_low_stock_threshold': (
                'Products without their own threshold will use this value. '
                'A product is low-stock when quantity ≤ threshold.'
            ),
        }

    def clean_default_low_stock_threshold(self):
        threshold = self.cleaned_data.get('default_low_stock_threshold')
        if threshold is not None and threshold < 0:
            raise ValidationError('Threshold cannot be negative.')
        return threshold


class UserProfileForm(forms.ModelForm):
    """Form for updating user personal profile information."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your first name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'you@example.com',
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if not email:
            raise ValidationError('Email address is required.')
        qs = User.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('A user with this email address already exists.')
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """Password change form styled with Bootstrap 5."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
