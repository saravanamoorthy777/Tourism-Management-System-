from django.urls import path
from . import views

urlpatterns = [
    # Hotel Management & Browsing
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/<int:pk>/', views.hotel_detail, name='hotel_detail'),

    # Vehicle Management & Fleet Browsing
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),

    # Dynamic Cost Calculation API
    path('api/calculate-price/', views.calculate_price_api, name='calculate_price_api'),

    # Phase 5: Booking Workflow
    path('review/', views.booking_review, name='booking_review'),
    path('create/', views.booking_create, name='booking_create'),
    path('confirmation/<str:ref>/', views.booking_confirmation, name='booking_confirmation'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('my-bookings/<str:ref>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/<str:ref>/cancel/', views.booking_cancel, name='booking_cancel'),
]
