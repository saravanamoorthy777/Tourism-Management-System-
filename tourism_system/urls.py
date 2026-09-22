"""
URL configuration for Tourism Management System (TMS).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [
    # Django Built-in Admin
    path('admin/', admin.site.urls),

    # Accounts & User Authentication
    path('accounts/', include('accounts.urls')),

    # Direct Dashboard & Profile Shortcuts
    path('dashboard/', accounts_views.dashboard_view, name='dashboard_shortcut'),
    path('profile/', accounts_views.profile_view, name='profile_shortcut'),

    # Bookings & Cost Engine
    path('bookings/', include('bookings.urls')),

    # Customer Inquiries & Contact
    path('inquiries/', include('inquiries.urls')),

    # Reports & Executive Analytics Dashboard
    path('reports/', include('reports.urls')),

    # Destinations, Catalog & Homepage (Root)
    path('', include('destinations.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
