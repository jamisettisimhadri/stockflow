# StockFlow — SaaS Inventory Management System

A complete, production-ready MVP inventory management web application built with **Django**, **SQLite**, **Bootstrap 5**, and **Vanilla JavaScript**.

## Features

| Feature | Status |
|---|---|
| Email-based authentication (signup / login / logout) | Done |
| Organization-per-user multi-tenancy | Done |
| Full product CRUD (add / edit / delete) | Done |
| Organization-scoped data isolation | Done |
| Dashboard with summary stats | Done |
| Low-stock detection and alerts | Done |
| Searchable, paginated product list | Done |
| Per-product and per-org low-stock thresholds | Done |
| User profile & password change management | Done |
| Organization settings (name + default threshold) | Done |
| CSRF protection on all state-changing forms | Done |
| Server-side validation | Done |
| Responsive Bootstrap 5 UI | Done |
| Automated test suite | Done |

---

## Technology Stack

- **Backend:** Python 3.10+ / Django 5.2 (Python 3.14 compatible)
- **Database:** SQLite (dev) — swap to PostgreSQL for production
- **Frontend:** Bootstrap 5.3, Bootstrap Icons, Vanilla JS
- **Fonts:** Inter (Google Fonts)
- **Auth:** Custom email-based user model

---

## Project Structure

```
stockflow/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3              # created after migrate
├── stockflow/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── inventory/
│   ├── models.py           # User, Organization, Product
│   ├── forms.py            # SignupForm, LoginForm, ProductForm, SettingsForm
│   ├── views.py            # All view functions
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Admin registration
│   ├── apps.py
│   ├── tests.py            # Full test suite
│   └── migrations/
│       └── 0001_initial.py
├── templates/
│   ├── base.html
│   ├── auth_base.html
│   ├── dashboard_base.html
│   ├── registration/
│   │   ├── login.html
│   │   └── signup.html
│   └── inventory/
│       ├── dashboard.html
│       ├── product_list.html
│       ├── product_form.html
│       ├── product_confirm_delete.html
│       └── settings.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

---

## Setup and Installation

### 1. Install Dependencies

```powershell
# Navigate to the project directory
cd path\to\stockflow

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1     # Windows PowerShell

# Install Django
pip install -r requirements.txt
```

### 2. Apply Database Migrations

```powershell
python manage.py migrate
```

### 3. (Optional) Create a Superuser for Admin Access

```powershell
python manage.py createsuperuser
# Enter an email address when prompted
```

### 4. Run the Development Server

```powershell
python manage.py runserver
```

Open your browser: **http://127.0.0.1:8000/**

The root URL redirects to login. Use **http://127.0.0.1:8000/signup/** to create your first account.

### 5. Access the Django Admin

Visit **http://127.0.0.1:8000/admin/** and sign in with your superuser credentials.

---

## Running Tests

```powershell
python manage.py test inventory
```

To run with verbose output:
```powershell
python manage.py test inventory --verbosity=2
```

---

## Key Routes

| URL | Description |
|---|---|
| `/` | Redirects to dashboard or login |
| `/signup/` | Create new account + organization |
| `/login/` | Sign in |
| `/logout/` | Sign out |
| `/dashboard/` | Summary stats + low-stock table |
| `/products/` | Searchable, paginated product list |
| `/products/add/` | Add a new product |
| `/products/id/edit/` | Edit an existing product |
| `/products/id/delete/` | Confirm + delete a product |
| `/profile/` | User profile & password management |
| `/settings/` | Organization settings |
| `/admin/` | Django admin panel |

---

## Security Notes

- Passwords hashed with Django PBKDF2.
- CSRF tokens enforced on all POST forms.
- Every authenticated view protected with `@login_required`.
- All product queries filtered by organization — users cannot access other orgs' data.
- Organization ID assigned server-side, never from user-submitted form data.
- Products from another organization return HTTP 404.
- Django template engine auto-escapes all output.

---

## Completed Features

- Custom email-based user model
- Signup with organization creation (atomic transaction)
- Login / logout
- Dashboard: total products, units, inventory value, low-stock count
- Low-stock table on dashboard with empty states
- Product list with search and pagination
- Add product with full validation
- Edit product, recording last_updated_by
- Delete product with POST-based confirmation page
- Organization settings: name and default low-stock threshold
- Per-product threshold override (falls back to org default)
- Cross-organization data isolation (404 on foreign product access)
- Responsive sidebar layout (desktop + mobile hamburger)
- Bootstrap 5 design with custom CSS design tokens
- Flash messages (auto-dismiss after 5 seconds)
- Full test suite (30+ test cases)

## Known Limitations (Out of Scope for MVP)

- No password reset / forgot-password flow
- No email verification
- No multiple users per organization
- No CSV import/export
- No charts or advanced analytics
- No product images or categories
- No stock movement history
- No multiple warehouses
- SQLite used — replace with PostgreSQL for production
- SECRET_KEY must be moved to environment variables for production

---

## Production Checklist

- Set `DEBUG = False`
- Move `SECRET_KEY` to an environment variable
- Replace SQLite with PostgreSQL
- Configure `ALLOWED_HOSTS` with your domain
- Add `whitenoise` or a CDN for static files
- Set up HTTPS / TLS
- Run `python manage.py collectstatic`
