from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('bookings/', views.manage_bookings, name='manage_bookings'),
    path('bookings/<int:booking_id>/update-status/', views.update_booking_status, name='update_booking_status'),
    path('customers/', views.manage_customers, name='manage_customers'),
    path('analytics/', views.analytics_reports, name='analytics'),
]
