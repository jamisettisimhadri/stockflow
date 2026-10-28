"""
URL configuration for the inventory app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Root
    path('', views.index_redirect, name='index'),

    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Products
    path('products/', views.product_list_view, name='product_list'),
    path('products/add/', views.product_add_view, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit_view, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='product_delete'),

    # Account / Profile / Settings
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
]
