"""
Views for StockFlow inventory management.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import (
    SignupForm, LoginForm, ProductForm, OrganizationSettingsForm,
    UserProfileForm, CustomPasswordChangeForm
)
from .models import Organization, Product

User = get_user_model()


# ---------------------------------------------------------------------------
# Authentication views
# ---------------------------------------------------------------------------

def signup_view(request):
    """New user registration with organization creation."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome to StockFlow! Your organization has been created.',
            )
            return redirect('dashboard')
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    """Email/password authentication."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                # Generic error — do not reveal whether email exists
                messages.error(
                    request,
                    'Invalid email or password. Please try again.',
                )
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """Log out the current user."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    """Main dashboard with summary statistics and low-stock table."""
    org = get_object_or_404(Organization, owner=request.user)
    products = org.products.all()

    total_products = products.count()
    total_units = products.aggregate(total=Sum('quantity_on_hand'))['total'] or 0

    # Total inventory cost value (quantity * cost_price, only for priced products)
    total_value = 0
    for p in products:
        val = p.inventory_value()
        if val is not None:
            total_value += val

    # Low-stock products
    low_stock_products = [p for p in products if p.is_low_stock()]
    low_stock_count = len(low_stock_products)

    context = {
        'org': org,
        'total_products': total_products,
        'total_units': total_units,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'low_stock_products': low_stock_products,
        'page_title': 'Dashboard',
    }
    return render(request, 'inventory/dashboard.html', context)


# ---------------------------------------------------------------------------
# Product List
# ---------------------------------------------------------------------------

@login_required
def product_list_view(request):
    """Searchable, paginated list of all products in the user's organization."""
    org = get_object_or_404(Organization, owner=request.user)
    query = request.GET.get('q', '').strip()

    products = org.products.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Annotate each product page with low-stock status
    products_with_status = []
    for p in page_obj:
        products_with_status.append({
            'product': p,
            'is_low_stock': p.is_low_stock(),
            'effective_threshold': p.get_effective_threshold(),
        })

    context = {
        'org': org,
        'page_obj': page_obj,
        'products_with_status': products_with_status,
        'query': query,
        'total_count': org.products.count(),
        'filtered_count': products.count(),
        'page_title': 'Products',
    }
    return render(request, 'inventory/product_list.html', context)


# ---------------------------------------------------------------------------
# Add Product
# ---------------------------------------------------------------------------

@login_required
def product_add_view(request):
    """Create a new product for the user's organization."""
    org = get_object_or_404(Organization, owner=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.organization = org  # Always assign from server, never from user input
            product.last_updated_by = request.user
            if Product.objects.filter(organization=org, sku=product.sku).exists():
                form.add_error(
                    'sku',
                    f'SKU "{product.sku}" already exists in your organization.',
                )
            else:
                try:
                    with transaction.atomic():
                        product.save()
                    messages.success(
                        request,
                        f'Product "{product.name}" was added successfully.',
                    )
                    return redirect('product_list')
                except IntegrityError:
                    form.add_error(
                        'sku',
                        f'SKU "{product.sku}" already exists in your organization.',
                    )
    else:
        form = ProductForm()

    context = {
        'org': org,
        'form': form,
        'page_title': 'Add Product',
        'action_label': 'Add Product',
        'is_edit': False,
    }
    return render(request, 'inventory/product_form.html', context)


# ---------------------------------------------------------------------------
# Edit Product
# ---------------------------------------------------------------------------

@login_required
def product_edit_view(request, pk):
    """Edit an existing product. Returns 404 for products in other organizations."""
    org = get_object_or_404(Organization, owner=request.user)
    product = get_object_or_404(Product, pk=pk, organization=org)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.last_updated_by = request.user
            if Product.objects.filter(organization=org, sku=updated.sku).exclude(pk=product.pk).exists():
                form.add_error(
                    'sku',
                    f'SKU "{updated.sku}" already exists in your organization.',
                )
            else:
                try:
                    with transaction.atomic():
                        updated.save()
                    messages.success(
                        request,
                        f'Product "{product.name}" was updated successfully.',
                    )
                    return redirect('product_list')
                except IntegrityError:
                    form.add_error(
                        'sku',
                        f'SKU "{updated.sku}" already exists in your organization.',
                    )
    else:
        form = ProductForm(instance=product)

    context = {
        'org': org,
        'form': form,
        'product': product,
        'page_title': f'Edit: {product.name}',
        'action_label': 'Save Changes',
        'is_edit': True,
    }
    return render(request, 'inventory/product_form.html', context)


# ---------------------------------------------------------------------------
# Delete Product
# ---------------------------------------------------------------------------

@login_required
def product_delete_view(request, pk):
    """Confirm and delete a product. GET shows confirmation, POST deletes."""
    org = get_object_or_404(Organization, owner=request.user)
    product = get_object_or_404(Product, pk=pk, organization=org)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(
            request,
            f'Product "{product_name}" was deleted successfully.',
        )
        return redirect('product_list')

    context = {
        'org': org,
        'product': product,
        'page_title': f'Delete: {product.name}',
    }
    return render(request, 'inventory/product_confirm_delete.html', context)



# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@login_required
def profile_view(request):
    """User profile view for viewing and updating personal details and password."""
    org = get_object_or_404(Organization, owner=request.user)
    active_tab = 'profile'

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            profile_form = UserProfileForm(request.POST, instance=request.user)
            password_form = CustomPasswordChangeForm(user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile details have been updated successfully.')
                return redirect('profile')
            active_tab = 'profile'

        elif action == 'password':
            profile_form = UserProfileForm(instance=request.user)
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been changed successfully.')
                return redirect('profile')
            active_tab = 'password'

        else:
            profile_form = UserProfileForm(instance=request.user)
            password_form = CustomPasswordChangeForm(user=request.user)
    else:
        profile_form = UserProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    total_products = Product.objects.filter(organization=org).count()

    context = {
        'org': org,
        'profile_form': profile_form,
        'password_form': password_form,
        'active_tab': active_tab,
        'total_products': total_products,
        'page_title': 'My Profile',
    }
    return render(request, 'inventory/profile.html', context)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@login_required
def settings_view(request):
    """Organization settings — default low-stock threshold."""
    org = get_object_or_404(Organization, owner=request.user)

    if request.method == 'POST':
        form = OrganizationSettingsForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('settings')
    else:
        form = OrganizationSettingsForm(instance=org)

    context = {
        'org': org,
        'form': form,
        'page_title': 'Settings',
    }
    return render(request, 'inventory/settings.html', context)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

def index_redirect(request):
    """Redirect root URL to dashboard or login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
