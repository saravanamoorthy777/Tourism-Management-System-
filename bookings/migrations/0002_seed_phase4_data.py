from decimal import Decimal
from datetime import date
from django.db import migrations


def seed_phase4_inventory(apps, schema_editor):
    Destination = apps.get_model('destinations', 'Destination')
    Hotel = apps.get_model('bookings', 'Hotel')
    Vehicle = apps.get_model('bookings', 'Vehicle')
    SeasonalPricing = apps.get_model('bookings', 'SeasonalPricing')

    # 1. Seed Vehicles
    vehicles_data = [
        {
            'name': 'Maruti Suzuki Dzire',
            'vehicle_type': 'sedan',
            'seating_capacity': 4,
            'rate_per_day': Decimal('2200.00'),
            'description': 'Comfortable 4-seater air-conditioned compact sedan with ample boot space. Ideal for couples and small families.',
            'is_available': True,
        },
        {
            'name': 'Toyota Innova Crysta',
            'vehicle_type': 'suv',
            'seating_capacity': 6,
            'rate_per_day': Decimal('3800.00'),
            'description': 'Premium 6-seater luxury MPV/SUV with captain chairs, dual-zone climate control, and superior highway suspension.',
            'is_available': True,
        },
        {
            'name': 'Mahindra Scorpio-N',
            'vehicle_type': 'suv',
            'seating_capacity': 6,
            'rate_per_day': Decimal('3500.00'),
            'description': 'Rugged 4x4 capable SUV designed for hilly terrains, high-altitude mountain passes, and scenic rough trails.',
            'is_available': True,
        },
        {
            'name': 'Force Urbania Luxury Van',
            'vehicle_type': 'minibus',
            'seating_capacity': 12,
            'rate_per_day': Decimal('6500.00'),
            'description': 'Spacious 12-seater luxury van with individual reclining seats, panoramic windows, ambient cabin lighting, and extensive luggage space.',
            'is_available': True,
        },
        {
            'name': 'Tempo Traveller Executive',
            'vehicle_type': 'minibus',
            'seating_capacity': 16,
            'rate_per_day': Decimal('7500.00'),
            'description': 'Air-conditioned 16-seater executive passenger coach suitable for student groups, corporate outings, and extended family vacations.',
            'is_available': True,
        },
    ]

    for vdata in vehicles_data:
        Vehicle.objects.get_or_create(
            name=vdata['name'],
            defaults=vdata
        )

    # 2. Seed Seasonal Pricing
    current_year = date.today().year
    seasons_data = [
        {
            'name': 'Summer Vacation Peak Season',
            'start_date': date(current_year, 4, 15),
            'end_date': date(current_year, 7, 10),
            'multiplier': Decimal('1.20'),
            'description': 'Peak holiday demand during summer school breaks and high hill station tourism (+20% surcharge).',
            'is_active': True,
        },
        {
            'name': 'Monsoon Saver Season',
            'start_date': date(current_year, 7, 15),
            'end_date': date(current_year, 9, 15),
            'multiplier': Decimal('0.90'),
            'description': 'Special monsoon travel discounts across beach and heritage corridors (-10% discount).',
            'is_active': True,
        },
        {
            'name': 'Diwali & Autumn Festive Season',
            'start_date': date(current_year, 10, 1),
            'end_date': date(current_year, 11, 20),
            'multiplier': Decimal('1.25'),
            'description': 'Festive holiday rush and pleasant autumn weather across North and Western India (+25% surcharge).',
            'is_active': True,
        },
        {
            'name': 'Winter New Year Peak Season',
            'start_date': date(current_year, 12, 15),
            'end_date': date(current_year + 1, 1, 10),
            'multiplier': Decimal('1.30'),
            'description': 'Christmas, New Year celebrations, and snow season peak travel period (+30% surcharge).',
            'is_active': True,
        },
    ]

    for sdata in seasons_data:
        SeasonalPricing.objects.get_or_create(
            name=sdata['name'],
            defaults=sdata
        )

    # 3. Seed Partner Hotels linked to available destinations
    destinations = {d.name: d for d in Destination.objects.all()}

    hotels_catalog = [
        # Manali Valley Hotels
        {
            'destination_name': 'Manali Valley',
            'name': 'Pine Retreat Alpine Resort',
            'location': 'Log Huts Area, Old Manali',
            'tier': 'standard',
            'room_type': 'Standard Pine View Room',
            'price_per_night': Decimal('1800.00'),
            'available_rooms': 8,
            'description': 'Cozy wooden chalets surrounded by deodar pine trees. Offers hot water heating, mountain views, and local Himachali hospitality.',
        },
        {
            'destination_name': 'Manali Valley',
            'name': 'The Himalayan Heights Deluxe Spa Resort',
            'location': 'Near Solang Valley Road, Manali',
            'tier': 'deluxe',
            'room_type': 'Deluxe Valley View Balcony Room',
            'price_per_night': Decimal('3600.00'),
            'available_rooms': 12,
            'description': '4-star luxury property with panoramic views of snow-capped Pir Panjal peaks, in-house heated pool, spa, and buffet dining.',
        },
        {
            'destination_name': 'Manali Valley',
            'name': 'Solang Glamping & Luxury Chalets',
            'location': 'Solang Valley, Manali',
            'tier': 'premium',
            'room_type': 'Premium Luxury Glass Chalet',
            'price_per_night': Decimal('6500.00'),
            'available_rooms': 5,
            'description': 'Exclusive 5-star glass chalets offering 360-degree mountain views, private jacuzzi, personalized chef services, and campfire evenings.',
        },

        # Jaipur Heritage City Hotels
        {
            'destination_name': 'Jaipur Heritage City',
            'name': 'Haveli Rajputana Heritage Inn',
            'location': 'Bani Park, Jaipur',
            'tier': 'standard',
            'room_type': 'Standard Heritage Double Bed',
            'price_per_night': Decimal('1500.00'),
            'available_rooms': 10,
            'description': 'Traditional Rajasthani architecture with hand-painted courtyards, quiet rooftop cafe, and central accessibility.',
        },
        {
            'destination_name': 'Jaipur Heritage City',
            'name': 'Royal Palace Heritage Grand',
            'location': 'Amer Road, Jaipur',
            'tier': 'deluxe',
            'room_type': 'Deluxe Palace View Suite',
            'price_per_night': Decimal('3200.00'),
            'available_rooms': 14,
            'description': '4-star heritage property overlooking Jal Mahal, with traditional puppet shows, royal dining, and manicured gardens.',
        },
        {
            'destination_name': 'Jaipur Heritage City',
            'name': 'The Maharaja Heritage Palace & Spa',
            'location': 'Civil Lines, Jaipur',
            'tier': 'premium',
            'room_type': 'Royal Maharaja Gold Suite',
            'price_per_night': Decimal('7500.00'),
            'available_rooms': 6,
            'description': 'Opulent 5-star royal palace stay with marble interiors, private butler service, peacock gardens, and regal vintage car tours.',
        },

        # South Goa Beaches Hotels
        {
            'destination_name': 'South Goa Beaches',
            'name': 'Palolem Coconut Grove Cabanas',
            'location': 'Palolem Beach, South Goa',
            'tier': 'standard',
            'room_type': 'Standard Beach Cottage',
            'price_per_night': Decimal('2000.00'),
            'available_rooms': 12,
            'description': 'Eco-friendly wooden cottages just 50 meters from Palolem beach sand. Fresh seafood shack and hammocks among coconut groves.',
        },
        {
            'destination_name': 'South Goa Beaches',
            'name': 'Varca Sands Beach Resort',
            'location': 'Varca Beach, South Goa',
            'tier': 'deluxe',
            'room_type': 'Deluxe Sea View Balcony Room',
            'price_per_night': Decimal('4200.00'),
            'available_rooms': 15,
            'description': '4-star beachfront resort with direct beach access, multi-cuisine pool bar, live Goan music, and watersports assistance.',
        },
        {
            'destination_name': 'South Goa Beaches',
            'name': 'The Taj Exotica Coastal Villas',
            'location': 'Benaulim, South Goa',
            'tier': 'premium',
            'room_type': 'Premium Ocean Villa with Plunge Pool',
            'price_per_night': Decimal('9500.00'),
            'available_rooms': 4,
            'description': 'Ultra-luxury 5-star Mediterranean villa property sprawling across 56 landscaped coastal acres. Private plunge pool and world-class culinary excellence.',
        },

        # Munnar Hill Station Hotels
        {
            'destination_name': 'Munnar Hill Station',
            'name': 'Misty Tea Gardens Lodge',
            'location': 'Old Munnar Town',
            'tier': 'standard',
            'room_type': 'Standard Plantation View Room',
            'price_per_night': Decimal('1600.00'),
            'available_rooms': 9,
            'description': 'Warm plantation-style lodge overlooking cascading tea hills, offering estate walks and fresh Nilgiri tea tastings.',
        },
        {
            'destination_name': 'Munnar Hill Station',
            'name': 'Eravikulam Mountain Resort',
            'location': 'Pallivasal, Munnar',
            'tier': 'deluxe',
            'room_type': 'Deluxe Cloud Valley Cottage',
            'price_per_night': Decimal('3400.00'),
            'available_rooms': 11,
            'description': '4-star boutique resort nestled high in the mist clouds with valley-facing private sundecks, indoor games, and Kerala Ayurvedic spa.',
        },
        {
            'destination_name': 'Munnar Hill Station',
            'name': 'The Windermere Estate Luxury Villa',
            'location': 'Pothamedu, Munnar',
            'tier': 'premium',
            'room_type': 'Premium Cedar Estate Villa',
            'price_per_night': Decimal('6800.00'),
            'available_rooms': 5,
            'description': 'High-end tranquil estate villa perched atop a cliff with panoramic valley views, private library, fireplace, and gourmet Kerala cuisine.',
        },
    ]

    for hdata in hotels_catalog:
        dest = destinations.get(hdata['destination_name'])
        if dest:
            Hotel.objects.get_or_create(
                name=hdata['name'],
                destination=dest,
                defaults={
                    'location': hdata['location'],
                    'tier': hdata['tier'],
                    'room_type': hdata['room_type'],
                    'price_per_night': hdata['price_per_night'],
                    'available_rooms': hdata['available_rooms'],
                    'description': hdata['description'],
                    'is_active': True,
                }
            )


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
        ('destinations', '0002_seed_initial_catalog'),
    ]

    operations = [
        migrations.RunPython(seed_phase4_inventory, migrations.RunPython.noop),
    ]
