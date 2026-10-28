"""
Tests for StockFlow inventory management application.

Covers:
- User signup and organization creation
- Login / logout
- Authentication protection on all views
- Product CRUD operations
- SKU uniqueness constraints
- Low-stock logic
- Cross-organization data isolation
- Organization settings update
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import Organization, Product

User = get_user_model()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def create_user_with_org(email, password='TestPass123!', org_name='Test Org', **kwargs):
    """Create a user and their organization."""
    user = User.objects.create_user(email=email, password=password, **kwargs)
    org = Organization.objects.create(owner=user, name=org_name)
    return user, org


def create_product(org, name='Widget', sku='WGT-001', quantity=10, **kwargs):
    """Create a product for the given organization."""
    return Product.objects.create(
        organization=org,
        name=name,
        sku=sku,
        quantity_on_hand=quantity,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 1. Signup Tests
# ---------------------------------------------------------------------------

class SignupTests(TestCase):

    def test_signup_creates_user_and_organization(self):
        """Workflow A: Successful signup creates user + organization and logs in."""
        response = self.client.post(reverse('signup'), {
            'organization_name': 'Acme Corp',
            'email': 'alice@acme.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('dashboard'))

        user = User.objects.get(email='alice@acme.com')
        self.assertTrue(hasattr(user, 'organization'))
        self.assertEqual(user.organization.name, 'Acme Corp')
        self.assertEqual(user.organization.default_low_stock_threshold, 5)

    def test_signup_logs_user_in_automatically(self):
        """After signup the user is authenticated."""
        self.client.post(reverse('signup'), {
            'organization_name': 'My Org',
            'email': 'bob@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_duplicate_email_is_rejected(self):
        """Registration with an already-used email must fail."""
        User.objects.create_user(email='existing@example.com', password='pass')
        response = self.client.post(reverse('signup'), {
            'organization_name': 'New Org',
            'email': 'existing@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)  # Stays on signup page
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch_is_rejected(self):
        """Mismatched passwords must fail validation."""
        response = self.client.post(reverse('signup'), {
            'organization_name': 'Org',
            'email': 'test@example.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_weak_password_is_rejected(self):
        """A too-short or common password must be rejected."""
        response = self.client.post(reverse('signup'), {
            'organization_name': 'Org',
            'email': 'test@example.com',
            'password1': '1234',
            'password2': '1234',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())


# ---------------------------------------------------------------------------
# 2. Login / Logout Tests
# ---------------------------------------------------------------------------

class AuthTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(
            email='user@example.com',
            password='TestPass123!',
        )

    def test_login_with_valid_credentials(self):
        """Valid login redirects to dashboard."""
        response = self.client.post(reverse('login'), {
            'email': 'user@example.com',
            'password': 'TestPass123!',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_with_invalid_credentials(self):
        """Invalid login shows error message, stays on login page."""
        response = self.client.post(reverse('login'), {
            'email': 'user@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertTrue(any('Invalid' in str(m) for m in messages))

    def test_logout_redirects_to_login(self):
        """Logout redirects to login page."""
        self.client.login(username='user@example.com', password='TestPass123!')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_authenticated_user_redirect_from_login(self):
        """Authenticated users accessing login are redirected to dashboard."""
        self.client.login(username='user@example.com', password='TestPass123!')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard'))


# ---------------------------------------------------------------------------
# 3. Access Control Tests
# ---------------------------------------------------------------------------

class AccessControlTests(TestCase):

    def test_anonymous_cannot_access_dashboard(self):
        """Anonymous request to dashboard redirects to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_anonymous_cannot_access_product_list(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_cannot_access_product_add(self):
        response = self.client.get(reverse('product_add'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_cannot_access_settings(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# 4. Product CRUD Tests
# ---------------------------------------------------------------------------

class ProductCRUDTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(email='owner@example.com')
        self.client.login(username='owner@example.com', password='TestPass123!')

    def test_product_creation_works(self):
        """Workflow B: Creating a product via POST works."""
        response = self.client.post(reverse('product_add'), {
            'name': 'Test Widget',
            'sku': 'TW-001',
            'description': '',
            'quantity_on_hand': 20,
            'cost_price': '',
            'selling_price': '',
            'low_stock_threshold': '',
        })
        self.assertRedirects(response, reverse('product_list'))
        self.assertEqual(Product.objects.filter(organization=self.org).count(), 1)
        product = Product.objects.get(organization=self.org)
        self.assertEqual(product.name, 'Test Widget')
        self.assertEqual(product.quantity_on_hand, 20)

    def test_product_appears_in_list_after_creation(self):
        create_product(self.org, name='Widget A', sku='WA-001')
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Widget A')

    def test_product_edit_updates_quantity(self):
        """Workflow C: Editing a product updates the stored quantity."""
        product = create_product(self.org, name='Gadget', sku='G-001', quantity=5)
        response = self.client.post(
            reverse('product_edit', kwargs={'pk': product.pk}),
            {
                'name': 'Gadget',
                'sku': 'G-001',
                'description': '',
                'quantity_on_hand': 50,
                'cost_price': '',
                'selling_price': '',
                'low_stock_threshold': '',
            },
        )
        self.assertRedirects(response, reverse('product_list'))
        product.refresh_from_db()
        self.assertEqual(product.quantity_on_hand, 50)

    def test_product_delete_removes_product(self):
        product = create_product(self.org, name='Doomed', sku='D-001')
        response = self.client.post(reverse('product_delete', kwargs={'pk': product.pk}))
        self.assertRedirects(response, reverse('product_list'))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_delete_requires_post(self):
        """GET to delete view shows confirmation page, does not delete."""
        product = create_product(self.org, name='Safe', sku='S-001')
        response = self.client.get(reverse('product_delete', kwargs={'pk': product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_last_updated_by_is_recorded(self):
        """Edit sets last_updated_by to the requesting user."""
        product = create_product(self.org, name='Track Me', sku='T-001')
        self.client.post(
            reverse('product_edit', kwargs={'pk': product.pk}),
            {
                'name': 'Track Me',
                'sku': 'T-001',
                'description': '',
                'quantity_on_hand': 10,
                'cost_price': '',
                'selling_price': '',
                'low_stock_threshold': '',
            },
        )
        product.refresh_from_db()
        self.assertEqual(product.last_updated_by, self.user)


# ---------------------------------------------------------------------------
# 5. SKU Uniqueness Tests
# ---------------------------------------------------------------------------

class SKUUniquenessTests(TestCase):

    def setUp(self):
        self.user1, self.org1 = create_user_with_org(email='org1@example.com')
        self.user2, self.org2 = create_user_with_org(email='org2@example.com', org_name='Org 2')

    def test_duplicate_sku_is_rejected_within_same_org(self):
        """Two products with same SKU in same org must fail."""
        create_product(self.org1, name='Product A', sku='DUP-001')
        with self.assertRaises(Exception):
            create_product(self.org1, name='Product B', sku='DUP-001')

    def test_same_sku_allowed_in_different_organizations(self):
        """Same SKU can exist across different organizations."""
        create_product(self.org1, name='Org1 Product', sku='SHARED-001')
        product2 = create_product(self.org2, name='Org2 Product', sku='SHARED-001')
        self.assertIsNotNone(product2.pk)

    def test_duplicate_sku_form_error_via_view(self):
        """POST with duplicate SKU shows form error instead of crashing."""
        self.client.login(username='org1@example.com', password='TestPass123!')
        create_product(self.org1, name='Existing', sku='EX-001')
        response = self.client.post(reverse('product_add'), {
            'name': 'New Product',
            'sku': 'EX-001',
            'description': '',
            'quantity_on_hand': 5,
            'cost_price': '',
            'selling_price': '',
            'low_stock_threshold': '',
        })
        self.assertEqual(response.status_code, 200)
        # Product count should still be 1
        self.assertEqual(Product.objects.filter(organization=self.org1).count(), 1)


# ---------------------------------------------------------------------------
# 6. Validation Tests
# ---------------------------------------------------------------------------

class ValidationTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(email='val@example.com')
        self.client.login(username='val@example.com', password='TestPass123!')

    def test_negative_stock_is_rejected(self):
        """Negative quantity_on_hand must be rejected by form."""
        response = self.client.post(reverse('product_add'), {
            'name': 'Negative',
            'sku': 'NEG-001',
            'description': '',
            'quantity_on_hand': -5,
            'cost_price': '',
            'selling_price': '',
            'low_stock_threshold': '',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())

    def test_negative_cost_price_is_rejected(self):
        response = self.client.post(reverse('product_add'), {
            'name': 'Cheap',
            'sku': 'CHEAP-001',
            'description': '',
            'quantity_on_hand': 10,
            'cost_price': '-1.00',
            'selling_price': '',
            'low_stock_threshold': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_required_fields_enforced(self):
        """Name and SKU are required."""
        response = self.client.post(reverse('product_add'), {
            'name': '',
            'sku': '',
            'quantity_on_hand': 0,
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('name', form.errors)
        self.assertIn('sku', form.errors)


# ---------------------------------------------------------------------------
# 7. Low-Stock Logic Tests
# ---------------------------------------------------------------------------

class LowStockLogicTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(email='stock@example.com')
        self.org.default_low_stock_threshold = 10
        self.org.save()

    def test_product_specific_threshold_takes_precedence(self):
        """Product-level threshold overrides the organization default."""
        product = create_product(self.org, sku='P-001', quantity=8, low_stock_threshold=5)
        # quantity (8) > product threshold (5), so NOT low stock
        self.assertFalse(product.is_low_stock())

    def test_organization_default_used_when_product_threshold_absent(self):
        """Product without own threshold uses org default."""
        product = create_product(self.org, sku='P-002', quantity=8)
        # quantity (8) <= org default (10), so IS low stock
        self.assertTrue(product.is_low_stock())

    def test_product_at_threshold_is_low_stock(self):
        """Exactly at threshold is considered low stock."""
        product = create_product(self.org, sku='P-003', quantity=5, low_stock_threshold=5)
        self.assertTrue(product.is_low_stock())

    def test_product_above_threshold_is_not_low_stock(self):
        product = create_product(self.org, sku='P-004', quantity=11)
        # quantity (11) > org default (10)
        self.assertFalse(product.is_low_stock())

    def test_out_of_stock_is_low_stock(self):
        product = create_product(self.org, sku='P-005', quantity=0, low_stock_threshold=5)
        self.assertTrue(product.is_low_stock())

    def test_dashboard_low_stock_count_updates_after_threshold_change(self):
        """Workflow D: Changing org default immediately affects low-stock count."""
        self.client.login(username='stock@example.com', password='TestPass123!')
        create_product(self.org, sku='P-006', quantity=3)  # low under threshold 10

        # Change threshold to 2 (product at 3 is no longer low)
        response = self.client.post(reverse('settings'), {
            'name': self.org.name,
            'default_low_stock_threshold': 2,
        })
        self.assertRedirects(response, reverse('settings'))

        self.org.refresh_from_db()
        self.assertEqual(self.org.default_low_stock_threshold, 2)

        # Product (qty=3) is now above new threshold (2)
        product = Product.objects.get(organization=self.org)
        self.assertFalse(product.is_low_stock())


# ---------------------------------------------------------------------------
# 8. Cross-Organization Security Tests
# ---------------------------------------------------------------------------

class CrossOrgIsolationTests(TestCase):

    def setUp(self):
        self.user1, self.org1 = create_user_with_org(email='user1@example.com', org_name='Org 1')
        self.user2, self.org2 = create_user_with_org(email='user2@example.com', org_name='Org 2')
        self.product1 = create_product(self.org1, name='Org1 Product', sku='O1-001')

    def _login_as_user2(self):
        self.client.login(username='user2@example.com', password='TestPass123!')

    def test_user2_cannot_view_user1_product_detail(self):
        """Workflow E: Other org cannot access product edit."""
        self._login_as_user2()
        response = self.client.get(
            reverse('product_edit', kwargs={'pk': self.product1.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_user2_cannot_edit_user1_product(self):
        self._login_as_user2()
        response = self.client.post(
            reverse('product_edit', kwargs={'pk': self.product1.pk}),
            {
                'name': 'Hijacked',
                'sku': 'H-001',
                'quantity_on_hand': 0,
            },
        )
        self.assertEqual(response.status_code, 404)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Org1 Product')

    def test_user2_cannot_delete_user1_product(self):
        self._login_as_user2()
        response = self.client.post(
            reverse('product_delete', kwargs={'pk': self.product1.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.product1.pk).exists())

    def test_product_list_only_shows_own_org_products(self):
        """User 2's product list must not include user 1's products."""
        create_product(self.org2, name='Org2 Product', sku='O2-001')
        self._login_as_user2()
        response = self.client.get(reverse('product_list'))
        self.assertNotContains(response, 'Org1 Product')
        self.assertContains(response, 'Org2 Product')

    def test_dashboard_totals_scoped_to_own_org(self):
        """Dashboard totals must not include other org's data."""
        create_product(self.org2, name='Org2 Widget', sku='O2-W', quantity=999)
        self._login_as_user2()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['total_products'], 1)
        self.assertEqual(response.context['total_units'], 999)


# ---------------------------------------------------------------------------
# 9. Settings Tests
# ---------------------------------------------------------------------------

class SettingsTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(email='settings@example.com')
        self.client.login(username='settings@example.com', password='TestPass123!')

    def test_settings_page_loads(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)

    def test_org_settings_update_correctly(self):
        response = self.client.post(reverse('settings'), {
            'name': 'New Org Name',
            'default_low_stock_threshold': 15,
        })
        self.assertRedirects(response, reverse('settings'))
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, 'New Org Name')
        self.assertEqual(self.org.default_low_stock_threshold, 15)

    def test_negative_threshold_rejected(self):
        response = self.client.post(reverse('settings'), {
            'name': 'Org',
            'default_low_stock_threshold': -1,
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())


# ---------------------------------------------------------------------------
# 10. Inventory Value Tests
# ---------------------------------------------------------------------------

class InventoryValueTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(email='value@example.com')

    def test_inventory_value_calculated_correctly(self):
        """inventory_value() = quantity * cost_price."""
        product = create_product(
            self.org, sku='V-001', quantity=10,
            cost_price=Decimal('5.50'),
        )
        self.assertEqual(product.inventory_value(), Decimal('55.00'))

    def test_inventory_value_none_when_no_cost_price(self):
        product = create_product(self.org, sku='V-002', quantity=10)
        self.assertIsNone(product.inventory_value())


# ---------------------------------------------------------------------------
# 11. Profile Tests
# ---------------------------------------------------------------------------

class ProfileTests(TestCase):

    def setUp(self):
        self.user, self.org = create_user_with_org(
            email='profiletest@example.com',
            password='OldPassword123!',
            first_name='Original',
            last_name='User',
        )

    def test_profile_page_requires_login(self):
        """Unauthenticated user redirected to login."""
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_profile_page_loads_for_authenticated_user(self):
        """Authenticated user can view profile page."""
        self.client.login(username='profiletest@example.com', password='OldPassword123!')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/profile.html')
        self.assertIn('profile_form', response.context)
        self.assertIn('password_form', response.context)
        self.assertEqual(response.context['total_products'], 0)

    def test_profile_update_successful(self):
        """Updating name and email updates the user record."""
        self.client.login(username='profiletest@example.com', password='OldPassword123!')
        response = self.client.post(reverse('profile'), {
            'action': 'profile',
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'newemail@example.com',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')
        self.assertEqual(self.user.last_name, 'UpdatedLast')
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_profile_duplicate_email_rejected(self):
        """Cannot take an email already used by another user."""
        create_user_with_org(email='otheruser@example.com')
        self.client.login(username='profiletest@example.com', password='OldPassword123!')
        response = self.client.post(reverse('profile'), {
            'action': 'profile',
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'otheruser@example.com',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['profile_form']
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_change_successful(self):
        """Changing password updates user credentials and keeps them logged in."""
        self.client.login(username='profiletest@example.com', password='OldPassword123!')
        response = self.client.post(reverse('profile'), {
            'action': 'password',
            'old_password': 'OldPassword123!',
            'new_password1': 'NewStrongPassword456!',
            'new_password2': 'NewStrongPassword456!',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPassword456!'))

    def test_password_change_invalid_old_password(self):
        """Incorrect old password returns form validation error."""
        self.client.login(username='profiletest@example.com', password='OldPassword123!')
        response = self.client.post(reverse('profile'), {
            'action': 'password',
            'old_password': 'WrongPassword999!',
            'new_password1': 'NewStrongPassword456!',
            'new_password2': 'NewStrongPassword456!',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['password_form']
        self.assertFalse(form.is_valid())
        self.assertIn('old_password', form.errors)
