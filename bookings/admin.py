from django.contrib import admin
from .models import Hotel, Vehicle, SeasonalPricing, Booking


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'destination',
        'tier',
        'room_type',
        'price_per_night',
        'available_rooms',
        'is_active',
        'created_at'
    )
    list_filter = ('tier', 'is_active', 'destination')
    search_fields = ('name', 'destination__name', 'location', 'description', 'room_type')
    list_editable = ('price_per_night', 'available_rooms', 'is_active')
    ordering = ('destination', 'tier', 'price_per_night')
    autocomplete_fields = ('destination',)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'vehicle_type',
        'seating_capacity',
        'rate_per_day',
        'is_available',
        'created_at'
    )
    list_filter = ('vehicle_type', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('rate_per_day', 'is_available')
    ordering = ('vehicle_type', 'rate_per_day')


@admin.register(SeasonalPricing)
class SeasonalPricingAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'start_date',
        'end_date',
        'multiplier',
        'is_active',
        'created_at'
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('multiplier', 'is_active')
    ordering = ('-start_date',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_reference',
        'customer',
        'package',
        'start_date',
        'grand_total',
        'status',
        'created_at'
    )
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = (
        'booking_reference',
        'customer__username',
        'customer__first_name',
        'customer__last_name',
        'package__name'
    )
    list_editable = ('status',)
    readonly_fields = (
        'booking_reference',
        'package_amount',
        'hotel_amount',
        'vehicle_amount',
        'seasonal_adjustment',
        'subtotal',
        'gst_amount',
        'grand_total',
    )
    ordering = ('-created_at',)
