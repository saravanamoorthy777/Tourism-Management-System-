from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.contrib import messages
from django.contrib.auth.models import User
from bookings.models import Booking, Hotel, Vehicle
from destinations.models import Destination, TourPackage

@staff_member_required
def admin_dashboard(request):
    """Main dashboard view for staff with summary statistics."""
    total_customers = User.objects.filter(is_staff=False).count()
    total_destinations = Destination.objects.count()
    total_packages = TourPackage.objects.count()
    total_hotels = Hotel.objects.count()
    total_vehicles = Vehicle.objects.count()
    
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    
    # Revenue is usually calculated from confirmed/completed bookings
    revenue_agg = Booking.objects.filter(status__in=['confirmed', 'completed']).aggregate(total=Sum('grand_total'))
    total_revenue = revenue_agg['total'] or 0.00
    
    context = {
        'total_customers': total_customers,
        'total_destinations': total_destinations,
        'total_packages': total_packages,
        'total_hotels': total_hotels,
        'total_vehicles': total_vehicles,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'completed_bookings': completed_bookings,
        'total_revenue': total_revenue,
    }
    return render(request, 'reports/dashboard.html', context)

@staff_member_required
def manage_bookings(request):
    """View to list and filter bookings."""
    bookings = Booking.objects.select_related('customer', 'package', 'package__destination').order_by('-created_at')
    
    # Simple search & filter
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    if query:
        bookings = bookings.filter(
            Q(booking_reference__icontains=query) |
            Q(customer__username__icontains=query) |
            Q(customer__first_name__icontains=query) |
            Q(customer__last_name__icontains=query) |
            Q(package__name__icontains=query)
        )
    
    if status:
        bookings = bookings.filter(status=status)
        
    context = {
        'bookings': bookings,
        'search_query': query,
        'current_status': status,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'reports/booking_management.html', context)

@staff_member_required
def update_booking_status(request, booking_id):
    """POST endpoint to update booking status safely."""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        new_status = request.POST.get('status')
        if new_status in dict(Booking.STATUS_CHOICES).keys():
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking {booking.booking_reference} updated to {booking.get_status_display()}.")
        else:
            messages.error(request, "Invalid status selected.")
    return redirect('reports:manage_bookings')

@staff_member_required
def manage_customers(request):
    """View to list customers and their booking counts."""
    # Filter to non-staff to focus on real customers, annotate with booking count
    customers = User.objects.filter(is_staff=False).annotate(
        booking_count=Count('bookings')
    ).order_by('-date_joined')
    
    query = request.GET.get('q', '')
    if query:
        customers = customers.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
        
    context = {
        'customers': customers,
        'search_query': query,
    }
    return render(request, 'reports/customer_management.html', context)

@staff_member_required
def analytics_reports(request):
    """Detailed analytics and reporting."""
    # Booking Summary
    booking_summary = Booking.objects.aggregate(
        total=Count('id'),
        confirmed=Count('id', filter=Q(status='confirmed')),
        pending=Count('id', filter=Q(status='pending')),
        cancelled=Count('id', filter=Q(status='cancelled')),
        completed=Count('id', filter=Q(status='completed')),
    )
    
    # Revenue Summary
    revenue_summary = Booking.objects.filter(status__in=['confirmed', 'completed']).aggregate(
        total=Sum('grand_total')
    )
    
    # Popular Packages
    popular_packages = TourPackage.objects.annotate(
        booking_count=Count('bookings'),
        revenue=Sum('bookings__grand_total', filter=Q(bookings__status__in=['confirmed', 'completed']))
    ).order_by('-booking_count')[:10]
    
    # Popular Destinations
    popular_destinations = Destination.objects.annotate(
        booking_count=Count('packages__bookings'),
        revenue=Sum('packages__bookings__grand_total', filter=Q(packages__bookings__status__in=['confirmed', 'completed']))
    ).order_by('-booking_count')[:10]
    
    # Hotel Usage
    hotel_usage = Hotel.objects.annotate(
        usage_count=Count('bookings')
    ).filter(usage_count__gt=0).order_by('-usage_count')
    
    # Vehicle Usage
    vehicle_usage = Vehicle.objects.annotate(
        usage_count=Count('bookings')
    ).filter(usage_count__gt=0).order_by('-usage_count')
    
    context = {
        'booking_summary': booking_summary,
        'revenue_summary': revenue_summary,
        'popular_packages': popular_packages,
        'popular_destinations': popular_destinations,
        'hotel_usage': hotel_usage,
        'vehicle_usage': vehicle_usage,
    }
    return render(request, 'reports/analytics.html', context)
