import math
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from destinations.models import TourPackage
from .models import Hotel, Vehicle, SeasonalPricing


def parse_date(value):
    """Safely parse a date instance, date string (YYYY-MM-DD), or return None."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        value = value.strip()
        for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValidationError(f"Invalid date format: '{value}'. Expected YYYY-MM-DD.")
    raise ValidationError("Date value must be a string or date object.")


def calculate_rooms_needed(persons):
    """
    Calculate number of hotel rooms needed based on standard double occupancy:
    Rooms Needed = ceil(number of persons / 2)
    """
    if not isinstance(persons, int) or persons <= 0:
        raise ValidationError("Number of persons must be an integer of at least 1.")
    return math.ceil(persons / 2)


def get_active_season_for_dates(start_date, end_date):
    """
    Find the applicable active SeasonalPricing rule for the specified travel dates.
    If multiple seasons match, returns the active season with the highest multiplier.
    """
    matching_seasons = SeasonalPricing.objects.filter(
        is_active=True,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).order_by('-multiplier', 'start_date')
    return matching_seasons.first()


def calculate_tour_cost(package, persons, start_date, end_date, hotel=None, vehicle=None):
    """
    Core Dynamic Pricing Engine for the Tourism Management System.

    Formulas:
        Rooms Needed = ceil(number of persons / 2)
        Package Base = package price per person * number of persons
        Hotel Cost = hotel surcharge/night * number of nights * rooms required
        Vehicle Cost = vehicle rate/day * number of days
        Subtotal = Package Base + Hotel Cost + Vehicle Cost
        Apply the applicable seasonal pricing factor.
        GST = 5% of the applicable subtotal.
        Total = adjusted subtotal + GST

    Returns:
        dict: Detailed breakdown with all line items.
    """
    # 1. Validate Tour Package
    if not isinstance(package, TourPackage):
        if isinstance(package, (int, str)):
            try:
                package = TourPackage.objects.get(pk=int(package))
            except (TourPackage.DoesNotExist, ValueError):
                raise ValidationError("Specified tour package does not exist.")
        else:
            raise ValidationError("A valid TourPackage object or package ID is required.")

    if not package.is_active:
        raise ValidationError(f"Package '{package.name}' is currently not active.")

    # 2. Validate Persons
    try:
        persons = int(persons)
    except (ValueError, TypeError):
        raise ValidationError("Number of persons must be an integer.")

    if persons <= 0:
        raise ValidationError("Number of persons must be at least 1.")

    # 3. Validate and Parse Dates
    start_d = parse_date(start_date)
    end_d = parse_date(end_date)

    if not start_d:
        raise ValidationError("Travel start date is required.")
    if not end_d:
        raise ValidationError("Travel end date is required.")

    if end_d < start_d:
        raise ValidationError("Travel end date cannot be before travel start date.")

    # Calculate days and nights
    calendar_diff = (end_d - start_d).days
    if calendar_diff == 0:
        # Same day tour
        nights = 0
        days = 1
    else:
        nights = calendar_diff
        days = calendar_diff + 1

    # Ensure minimum nights for packages with multi-day durations if hotel is booked
    if nights == 0 and hotel and package.duration_days > 1:
        nights = max(1, package.duration_days - 1)
        days = package.duration_days

    # 4. Validate Hotel
    rooms_needed = calculate_rooms_needed(persons)
    hotel_obj = None

    if hotel:
        if isinstance(hotel, Hotel):
            hotel_obj = hotel
        elif isinstance(hotel, (int, str)) and str(hotel).strip() and str(hotel).strip().lower() not in ('none', '0', ''):
            try:
                hotel_obj = Hotel.objects.select_related('destination').get(pk=int(hotel))
            except (Hotel.DoesNotExist, ValueError):
                raise ValidationError("Specified hotel does not exist.")

    if hotel_obj:
        if not hotel_obj.is_active:
            raise ValidationError(f"Hotel '{hotel_obj.name}' is currently unavailable.")
        if hotel_obj.available_rooms < rooms_needed:
            raise ValidationError(
                f"Hotel '{hotel_obj.name}' has only {hotel_obj.available_rooms} room(s) available, "
                f"but {rooms_needed} room(s) are required for {persons} person(s)."
            )
        if hotel_obj.destination_id != package.destination_id:
            raise ValidationError(
                f"Hotel '{hotel_obj.name}' is located in {hotel_obj.destination.name}, "
                f"which does not match package destination {package.destination.name}."
            )

    # 5. Validate Vehicle
    vehicle_obj = None
    if vehicle:
        if isinstance(vehicle, Vehicle):
            vehicle_obj = vehicle
        elif isinstance(vehicle, (int, str)) and str(vehicle).strip() and str(vehicle).strip().lower() not in ('none', '0', ''):
            try:
                vehicle_obj = Vehicle.objects.get(pk=int(vehicle))
            except (Vehicle.DoesNotExist, ValueError):
                raise ValidationError("Specified vehicle does not exist.")

    if vehicle_obj:
        if not vehicle_obj.is_available:
            raise ValidationError(f"Vehicle '{vehicle_obj.name}' is currently unavailable.")
        if vehicle_obj.seating_capacity < persons:
            raise ValidationError(
                f"Vehicle '{vehicle_obj.name}' can seat up to {vehicle_obj.seating_capacity} passengers, "
                f"which is insufficient for {persons} person(s)."
            )

    # 6. Base Calculations
    # Package Base = package price per person * number of persons
    package_price = Decimal(str(package.base_price))
    package_base = (package_price * Decimal(persons)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Hotel Cost = hotel surcharge/night * number of nights * rooms required
    if hotel_obj and nights > 0:
        hotel_nightly = Decimal(str(hotel_obj.price_per_night))
        hotel_cost = (hotel_nightly * Decimal(nights) * Decimal(rooms_needed)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        hotel_cost = Decimal('0.00')

    # Vehicle Cost = vehicle rate/day * number of days
    if vehicle_obj and days > 0:
        vehicle_daily = Decimal(str(vehicle_obj.rate_per_day))
        vehicle_cost = (vehicle_daily * Decimal(days)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        vehicle_cost = Decimal('0.00')

    # Subtotal = Package Base + Hotel Cost + Vehicle Cost
    raw_subtotal = (package_base + hotel_cost + vehicle_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # 7. Seasonal Adjustment
    active_season = get_active_season_for_dates(start_d, end_d)
    if active_season:
        seasonal_multiplier = Decimal(str(active_season.multiplier))
        season_name = active_season.name
    else:
        seasonal_multiplier = Decimal('1.00')
        season_name = "Standard Regular Season"

    # Adjusted Subtotal = raw_subtotal * seasonal_multiplier
    adjusted_subtotal = (raw_subtotal * seasonal_multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    seasonal_adjustment = (adjusted_subtotal - raw_subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # 8. GST (5% of applicable subtotal)
    gst = (adjusted_subtotal * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # 9. Grand Total = adjusted subtotal + GST
    total = (adjusted_subtotal + gst).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        'success': True,
        'package_id': package.id,
        'package_name': package.name,
        'package_base_price': float(package.base_price),
        'persons': persons,
        'rooms_needed': rooms_needed,
        'start_date': start_d.strftime('%Y-%m-%d'),
        'end_date': end_d.strftime('%Y-%m-%d'),
        'days': days,
        'nights': nights,
        'hotel_id': hotel_obj.id if hotel_obj else None,
        'hotel_name': hotel_obj.name if hotel_obj else None,
        'hotel_tier': hotel_obj.tier if hotel_obj else None,
        'hotel_tier_display': hotel_obj.get_tier_display() if hotel_obj else None,
        'hotel_price_per_night': float(hotel_obj.price_per_night) if hotel_obj else 0.0,
        'vehicle_id': vehicle_obj.id if vehicle_obj else None,
        'vehicle_name': vehicle_obj.name if vehicle_obj else None,
        'vehicle_type': vehicle_obj.vehicle_type if vehicle_obj else None,
        'vehicle_type_display': vehicle_obj.get_vehicle_type_display() if vehicle_obj else None,
        'vehicle_rate_per_day': float(vehicle_obj.rate_per_day) if vehicle_obj else 0.0,
        'season_id': active_season.id if active_season else None,
        'season_name': season_name,
        'seasonal_multiplier': float(seasonal_multiplier),
        'package_base': float(package_base),
        'hotel_cost': float(hotel_cost),
        'vehicle_cost': float(vehicle_cost),
        'raw_subtotal': float(raw_subtotal),
        'seasonal_adjustment': float(seasonal_adjustment),
        'subtotal': float(adjusted_subtotal),
        'gst': float(gst),
        'total': float(total),
        'decimal': {
            'package_base': package_base,
            'hotel_cost': hotel_cost,
            'vehicle_cost': vehicle_cost,
            'raw_subtotal': raw_subtotal,
            'seasonal_adjustment': seasonal_adjustment,
            'subtotal': adjusted_subtotal,
            'gst': gst,
            'total': total,
        }
    }
