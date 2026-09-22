from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import DestinationCategory, Destination, TourPackage, PackageItinerary
from bookings.models import Hotel, Vehicle, SeasonalPricing


def home(request):
    """
    Homepage view for Tourism Management System (TMS).
    Showcases hero search, dynamic categories, featured destinations and popular packages.
    """
    categories = DestinationCategory.objects.filter(is_active=True)
    featured_destinations = Destination.objects.filter(is_active=True)[:6]
    popular_packages = TourPackage.objects.filter(is_active=True).select_related('destination')[:4]

    context = {
        'categories': categories,
        'featured_destinations': featured_destinations,
        'popular_packages': popular_packages,
    }
    return render(request, 'destinations/home.html', context)


def destination_list(request):
    """
    Listing page for destinations with keyword search and category filtering.
    URL: /destinations/
    """
    destinations = Destination.objects.filter(is_active=True).select_related('category')
    categories = DestinationCategory.objects.filter(is_active=True)

    # Search keyword
    query = request.GET.get('q', '').strip()
    if query:
        destinations = destinations.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query) |
            Q(highlights__icontains=query)
        )

    # Category filter (by slug or id)
    category_param = request.GET.get('category', '').strip()
    selected_category = None
    if category_param:
        if category_param.isdigit():
            selected_category = categories.filter(id=int(category_param)).first()
        else:
            selected_category = categories.filter(slug=category_param).first()
        if selected_category:
            destinations = destinations.filter(category=selected_category)

    context = {
        'destinations': destinations,
        'categories': categories,
        'selected_category': selected_category,
        'query': query,
        'total_count': destinations.count(),
    }
    return render(request, 'destinations/destination_list.html', context)


def destination_detail(request, pk):
    """
    Detailed page for an individual destination, displaying its information, highlights,
    and associated active tour packages.
    URL: /destinations/<id>/
    """
    destination = get_object_or_404(
        Destination.objects.select_related('category'),
        pk=pk,
        is_active=True
    )
    packages = destination.packages.filter(is_active=True).order_by('base_price')
    related_destinations = Destination.objects.filter(
        category=destination.category,
        is_active=True
    ).exclude(pk=destination.pk)[:3]

    context = {
        'destination': destination,
        'packages': packages,
        'related_destinations': related_destinations,
    }
    return render(request, 'destinations/destination_detail.html', context)


def package_list(request):
    """
    Listing page for tour packages with search, destination filtering, category filtering,
    and multiple sorting options.
    URL: /packages/
    """
    packages = TourPackage.objects.filter(is_active=True).select_related('destination', 'destination__category')
    categories = DestinationCategory.objects.filter(is_active=True)
    destinations = Destination.objects.filter(is_active=True)

    # Search query
    query = request.GET.get('q', '').strip()
    if query:
        packages = packages.filter(
            Q(name__icontains=query) |
            Q(destination__name__icontains=query) |
            Q(destination__location__icontains=query) |
            Q(description__icontains=query) |
            Q(inclusions__icontains=query)
        )

    # Filter by category
    category_param = request.GET.get('category', '').strip()
    selected_category = None
    if category_param:
        if category_param.isdigit():
            selected_category = categories.filter(id=int(category_param)).first()
        else:
            selected_category = categories.filter(slug=category_param).first()
        if selected_category:
            packages = packages.filter(destination__category=selected_category)

    # Filter by destination
    destination_param = request.GET.get('destination', '').strip()
    selected_destination = None
    if destination_param and destination_param.isdigit():
        selected_destination = destinations.filter(id=int(destination_param)).first()
        if selected_destination:
            packages = packages.filter(destination=selected_destination)

    # Sorting
    sort_option = request.GET.get('sort', 'price_asc').strip()
    if sort_option == 'price_desc':
        packages = packages.order_by('-base_price')
    elif sort_option == 'duration_asc':
        packages = packages.order_by('duration_days', 'base_price')
    elif sort_option == 'duration_desc':
        packages = packages.order_by('-duration_days', 'base_price')
    elif sort_option == 'name_asc':
        packages = packages.order_by('name')
    else:  # Default price_asc
        sort_option = 'price_asc'
        packages = packages.order_by('base_price')

    context = {
        'packages': packages,
        'categories': categories,
        'destinations': destinations,
        'selected_category': selected_category,
        'selected_destination': selected_destination,
        'sort_option': sort_option,
        'query': query,
        'total_count': packages.count(),
    }
    return render(request, 'destinations/package_list.html', context)


def package_detail(request, pk):
    """
    Detailed page for a specific tour package.
    Clearly displays: destination, duration, price per person, description, inclusions,
    exclusions, and day-by-day itinerary.
    URL: /packages/<id>/
    """
    package = get_object_or_404(
        TourPackage.objects.select_related('destination', 'destination__category'),
        pk=pk,
        is_active=True
    )
    itineraries = package.itineraries.all().order_by('day_number')
    other_packages = TourPackage.objects.filter(
        destination=package.destination,
        is_active=True
    ).exclude(pk=package.pk)[:3]

    hotels = Hotel.objects.filter(destination=package.destination, is_active=True).order_by('tier', 'price_per_night')
    vehicles = Vehicle.objects.filter(is_available=True).order_by('seating_capacity', 'rate_per_day')
    seasons = SeasonalPricing.objects.filter(is_active=True).order_by('-start_date')

    # Default travel dates based on package duration
    today = date.today()
    default_start_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    nights_count = max(1, package.duration_days - 1)
    default_end_date = (today + timedelta(days=7 + nights_count)).strftime('%Y-%m-%d')

    context = {
        'package': package,
        'destination': package.destination,
        'itineraries': itineraries,
        'other_packages': other_packages,
        'hotels': hotels,
        'vehicles': vehicles,
        'seasons': seasons,
        'default_start_date': default_start_date,
        'default_end_date': default_end_date,
        'default_nights': nights_count,
    }
    return render(request, 'destinations/package_detail.html', context)
