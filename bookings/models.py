from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from destinations.models import Destination, TourPackage


class Hotel(models.Model):
    """
    Hotel accommodation model linked to a tourist destination.
    Offers tiered lodging options (Standard, Deluxe, Premium) with nightly surcharges.
    """
    TIER_CHOICES = [
        ('standard', 'Standard'),
        ('deluxe', 'Deluxe'),
        ('premium', 'Premium'),
    ]

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='hotels',
        help_text="Tourist destination where this hotel is located"
    )
    name = models.CharField(max_length=200, verbose_name="Hotel Name")
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Detailed address/area (e.g., Near Mall Road, Manali)"
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='standard',
        verbose_name="Hotel Tier"
    )
    description = models.TextField(help_text="Overview of hotel features and hospitality services")
    room_type = models.CharField(
        max_length=100,
        default='Standard Double Room',
        help_text="e.g. Deluxe Double Room, Premium View Suite, Executive Twin"
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Surcharge or price per room per night in INR"
    )
    available_rooms = models.PositiveIntegerField(
        default=10,
        help_text="Current available inventory of rooms"
    )
    image = models.ImageField(upload_to='hotels/', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hotels"
        ordering = ['destination', 'price_per_night']

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()} - {self.destination.name})"

    @property
    def is_in_stock(self):
        return self.is_active and self.available_rooms > 0


class Vehicle(models.Model):
    """
    Vehicle fleet model for package transportation and local sightseeing.
    Supports sedans, SUVs, and minibuses with daily rental rates.
    """
    TYPE_CHOICES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('minibus', 'Minibus'),
    ]

    name = models.CharField(
        max_length=150,
        verbose_name="Vehicle Name/Model",
        help_text="e.g. Maruti Suzuki Dzire, Toyota Innova Crysta, Force Urbania"
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='sedan',
        verbose_name="Vehicle Category"
    )
    seating_capacity = models.PositiveIntegerField(
        default=4,
        help_text="Maximum passenger capacity excluding driver"
    )
    rate_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Daily rental charge in INR"
    )
    description = models.TextField(
        blank=True,
        help_text="Vehicle specifications, air conditioning, luggage capacity, etc."
    )
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    is_available = models.BooleanField(default=True, verbose_name="Available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ['vehicle_type', 'rate_per_day']

    def __str__(self):
        return f"{self.name} ({self.get_vehicle_type_display()} - {self.seating_capacity} Seats)"


class SeasonalPricing(models.Model):
    """
    Seasonal pricing rules specifying date ranges and price multipliers.
    Applied to the base package, hotel, and vehicle subtotal during pricing calculation.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Season Name",
        help_text="e.g. Peak Summer Season, Festive Diwali Season, Monsoon Saver"
    )
    start_date = models.DateField(help_text="Season start date (YYYY-MM-DD)")
    end_date = models.DateField(help_text="Season end date (YYYY-MM-DD)")
    multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Multiplier applied to subtotal (e.g. 1.20 for +20% peak, 0.90 for -10% discount)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    description = models.TextField(
        blank=True,
        help_text="Details about seasonality reasons (holidays, weather, peak demand)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Seasonal Pricing Rule"
        verbose_name_plural = "Seasonal Pricing Rules"
        ordering = ['-start_date']

    def __str__(self):
        percentage = int((self.multiplier - Decimal('1.00')) * 100)
        prefix = "+" if percentage > 0 else ""
        factor_str = f"{prefix}{percentage}%" if percentage != 0 else "Base (1.0x)"
        return f"{self.name} ({factor_str}: {self.start_date} to {self.end_date})"

    def covers_dates(self, travel_start, travel_end):
        """Check whether the given travel date range overlaps with this season."""
        return self.is_active and (travel_start <= self.end_date and travel_end >= self.start_date)


class Booking(models.Model):
    """
    Customer booking model.
    Stores the final pricing breakdown from the pricing engine to ensure immutability.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    booking_reference = models.CharField(max_length=50, unique=True, help_text="Unique booking reference ID (e.g. BKG-YYYYMMDD-XXXX)")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    package = models.ForeignKey(TourPackage, on_delete=models.PROTECT, related_name='bookings')
    
    # Selected options
    start_date = models.DateField()
    end_date = models.DateField()
    persons = models.PositiveIntegerField()
    rooms_required = models.PositiveIntegerField(default=1)
    
    # Optional selections
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    # Pricing Breakdown (Snapshot at booking time)
    package_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    hotel_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vehicle_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    seasonal_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking_reference} - {self.customer.username} ({self.get_status_display()})"
