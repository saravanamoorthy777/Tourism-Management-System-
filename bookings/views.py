import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from destinations.models import Destination, TourPackage
from .models import Hotel, Vehicle, SeasonalPricing
from .pricing import calculate_tour_cost

from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .pricing import parse_date
from .models import Booking



def hotel_list(request):
    """
    Catalog view for browsing hotel accommodations across destinations.
    Supports filtering by destination and tier (Standard, Deluxe, Premium), plus keyword search.
    """
    hotels = Hotel.objects.filter(is_active=True).select_related('destination')
    destinations = Destination.objects.filter(is_active=True)
    tiers = Hotel.TIER_CHOICES

    # Search keyword
    query = request.GET.get('q', '').strip()
    if query:
        hotels = hotels.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query) |
            Q(destination__name__icontains=query)
        )

    # Destination filter
    dest_param = request.GET.get('destination', '').strip()
    selected_destination = None
    if dest_param:
        if dest_param.isdigit():
            selected_destination = destinations.filter(id=int(dest_param)).first()
        else:
            selected_destination = destinations.filter(name__iexact=dest_param).first()
        if selected_destination:
            hotels = hotels.filter(destination=selected_destination)

    # Tier filter
    selected_tier = request.GET.get('tier', '').strip().lower()
    if selected_tier in dict(Hotel.TIER_CHOICES):
        hotels = hotels.filter(tier=selected_tier)
    else:
        selected_tier = ''

    context = {
        'hotels': hotels,
        'destinations': destinations,
        'tiers': tiers,
        'selected_destination': selected_destination,
        'selected_tier': selected_tier,
        'query': query,
        'total_count': hotels.count(),
    }
    return render(request, 'bookings/hotel_list.html', context)


def hotel_detail(request, pk):
    """
    Detailed showcase view for a specific hotel, displaying amenities, room inventory,
    and associated tour packages in that destination.
    """
    hotel = get_object_or_404(Hotel.objects.select_related('destination'), pk=pk)
    related_packages = TourPackage.objects.filter(
        destination=hotel.destination,
        is_active=True
    )[:3]

    context = {
        'hotel': hotel,
        'related_packages': related_packages,
    }
    return render(request, 'bookings/hotel_detail.html', context)


def vehicle_list(request):
    """
    Fleet catalog view for browsing transportation options.
    Supports filtering by category (Sedan, SUV, Minibus).
    """
    vehicles = Vehicle.objects.filter(is_available=True)
    types = Vehicle.TYPE_CHOICES

    selected_type = request.GET.get('type', '').strip().lower()
    if selected_type in dict(Vehicle.TYPE_CHOICES):
        vehicles = vehicles.filter(vehicle_type=selected_type)
    else:
        selected_type = ''

    context = {
        'vehicles': vehicles,
        'types': types,
        'selected_type': selected_type,
        'total_count': vehicles.count(),
    }
    return render(request, 'bookings/vehicle_list.html', context)


def vehicle_detail(request, pk):
    """
    Detailed view for a specific vehicle model.
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'bookings/vehicle_detail.html', {'vehicle': vehicle})


@require_http_methods(["GET", "POST"])
def calculate_price_api(request):
    """
    AJAX endpoint for the live dynamic cost calculator.
    Calculates cost breakdown and returns JSON formatted response.
    """
    params = request.GET if request.method == "GET" else request.POST

    # If JSON payload in body
    if not params and request.body:
        try:
            params = json.loads(request.body)
        except Exception:
            params = {}

    package_id = params.get('package_id')
    persons = params.get('persons', 2)
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    hotel_id = params.get('hotel_id')
    vehicle_id = params.get('vehicle_id')

    if not package_id:
        return JsonResponse({'success': False, 'error': "Tour package ID is required."}, status=400)

    try:
        package = TourPackage.objects.get(pk=int(package_id))
    except (TourPackage.DoesNotExist, ValueError):
        return JsonResponse({'success': False, 'error': "Invalid or non-existent tour package."}, status=400)

    try:
        breakdown = calculate_tour_cost(
            package=package,
            persons=persons,
            start_date=start_date,
            end_date=end_date,
            hotel=hotel_id,
            vehicle=vehicle_id
        )
        # Exclude internal Decimal objects from JSON serialization
        breakdown.pop('decimal', None)
        return JsonResponse(breakdown)
    except ValidationError as ve:
        return JsonResponse({'success': False, 'error': ve.message if hasattr(ve, 'message') else str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@login_required
@require_http_methods(["POST"])
def booking_review(request):
    """
    Validates form input from package detail and presents a booking summary for final confirmation.
    """
    package_id = request.POST.get('package_id')
    persons = request.POST.get('persons', 1)
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    hotel_id = request.POST.get('hotel_id')
    vehicle_id = request.POST.get('vehicle_id')

    package = get_object_or_404(TourPackage, pk=package_id)

    try:
        persons = int(persons)
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        
        breakdown = calculate_tour_cost(
            package=package,
            persons=persons,
            start_date=start_date_obj,
            end_date=end_date_obj,
            hotel=hotel_id,
            vehicle=vehicle_id
        )
    except Exception as e:
        messages.error(request, f"Cannot process booking: {str(e)}")
        return redirect('package_detail', pk=package.id)

    hotel = None
    if hotel_id:
        hotel = Hotel.objects.filter(id=hotel_id).first()
    
    vehicle = None
    if vehicle_id:
        vehicle = Vehicle.objects.filter(id=vehicle_id).first()

    context = {
        'package': package,
        'persons': persons,
        'start_date': start_date,
        'end_date': end_date,
        'hotel': hotel,
        'vehicle': vehicle,
        'breakdown': breakdown,
    }
    return render(request, 'bookings/booking_review.html', context)


@login_required
@require_http_methods(["POST"])
def booking_create(request):
    """
    Finalizes the booking, recalculates price to ensure validity, decrements inventory, and saves.
    """
    package_id = request.POST.get('package_id')
    persons = request.POST.get('persons', 1)
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    hotel_id = request.POST.get('hotel_id')
    vehicle_id = request.POST.get('vehicle_id')

    package = get_object_or_404(TourPackage, pk=package_id)

    try:
        persons = int(persons)
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        
        breakdown = calculate_tour_cost(
            package=package,
            persons=persons,
            start_date=start_date_obj,
            end_date=end_date_obj,
            hotel=hotel_id,
            vehicle=vehicle_id
        )
    except Exception as e:
        messages.error(request, f"Booking validation failed: {str(e)}")
        return redirect('package_detail', pk=package.id)

    try:
        with transaction.atomic():
            hotel = None
            if hotel_id:
                hotel = Hotel.objects.select_for_update().filter(id=hotel_id).first()
            
            vehicle = None
            if vehicle_id:
                vehicle = Vehicle.objects.filter(id=vehicle_id).first()

            # Decrement hotel inventory if applicable
            if hotel:
                rooms_needed = breakdown.get('rooms_needed', 1)
                if hotel.available_rooms < rooms_needed:
                    messages.error(request, "Not enough rooms available for the selected hotel.")
                    return redirect('package_detail', pk=package.id)
                hotel.available_rooms -= rooms_needed
                hotel.save()

            # Generate unique reference
            prefix = "BKG"
            date_str = timezone.now().strftime("%Y%m%d")
            random_str = get_random_string(6).upper()
            reference = f"{prefix}-{date_str}-{random_str}"

            decimal_vals = breakdown.get('decimal', {})

            booking = Booking.objects.create(
                booking_reference=reference,
                customer=request.user,
                package=package,
                start_date=start_date_obj,
                end_date=end_date_obj,
                persons=persons,
                rooms_required=breakdown.get('rooms_needed', 1),
                hotel=hotel,
                vehicle=vehicle,
                package_amount=decimal_vals.get('package_base', 0),
                hotel_amount=decimal_vals.get('hotel_cost', 0),
                vehicle_amount=decimal_vals.get('vehicle_cost', 0),
                seasonal_adjustment=decimal_vals.get('seasonal_adjustment', 0),
                subtotal=decimal_vals.get('subtotal', 0),
                gst_amount=decimal_vals.get('gst', 0),
                grand_total=decimal_vals.get('total', 0),
                status='confirmed'
            )
    except Exception as e:
        messages.error(request, f"Booking creation failed: {str(e)}")
        return redirect('package_detail', pk=package.id)

    messages.success(request, f"Booking created successfully! Reference: {reference}")
    return redirect('booking_confirmation', ref=booking.booking_reference)


@login_required
def booking_confirmation(request, ref):
    booking = get_object_or_404(
        Booking.objects.select_related('package', 'package__destination', 'hotel', 'vehicle'),
        booking_reference=ref, customer=request.user
    )
    return render(request, 'bookings/booking_confirmation.html', {'booking': booking})


@login_required
def my_bookings(request):
    today = timezone.now().date()
    bookings = Booking.objects.filter(customer=request.user).select_related(
        'package', 'package__destination', 'hotel', 'vehicle'
    ).order_by('-created_at')
    
    active_filter = request.GET.get('filter', 'all')
    
    if active_filter == 'upcoming':
        bookings = bookings.filter(end_date__gte=today).exclude(status='cancelled').order_by('start_date')
    elif active_filter == 'past':
        bookings = bookings.filter(end_date__lt=today).exclude(status='cancelled')
    elif active_filter == 'confirmed':
        bookings = bookings.filter(status='confirmed')
    elif active_filter == 'completed':
        bookings = bookings.filter(status='completed')
    elif active_filter == 'cancelled':
        bookings = bookings.filter(status='cancelled')
        
    context = {
        'bookings': bookings,
        'active_filter': active_filter,
    }
        
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def booking_detail(request, ref):
    booking = get_object_or_404(
        Booking.objects.select_related('package', 'package__destination', 'hotel', 'vehicle'),
        booking_reference=ref, customer=request.user
    )
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
@require_http_methods(["POST"])
def booking_cancel(request, ref):
    booking = get_object_or_404(Booking, booking_reference=ref, customer=request.user)
    if booking.status in ['pending', 'confirmed']:
        try:
            with transaction.atomic():
                # Lock the booking record
                booking = Booking.objects.select_for_update().get(id=booking.id)
                
                # Check status again within lock
                if booking.status not in ['pending', 'confirmed']:
                    messages.error(request, "This booking cannot be cancelled.")
                    return redirect('booking_detail', ref=ref)
                    
                booking.status = 'cancelled'
                booking.save()
                
                # Restore inventory safely
                if booking.hotel:
                    hotel = Hotel.objects.select_for_update().get(id=booking.hotel.id)
                    hotel.available_rooms += booking.rooms_required
                    hotel.save()
                    
            messages.success(request, f"Booking {ref} has been cancelled successfully.")
        except Exception as e:
            messages.error(request, f"Could not cancel booking: {str(e)}")
    else:
        messages.error(request, "This booking cannot be cancelled.")
        
    return redirect('booking_detail', ref=ref)
