import json
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone

from destinations.models import DestinationCategory, Destination, TourPackage, PackageItinerary
from .models import Hotel, Vehicle, SeasonalPricing, Booking
from .pricing import calculate_rooms_needed, get_active_season_for_dates, calculate_tour_cost


class Phase4BaseTestCase(TestCase):
    """Base setup for Phase 4 testing with categories, destinations, packages, hotels, and fleet."""

    def setUp(self):
        self.client = Client()

        # Ensure test isolation by clearing existing records in test database
        SeasonalPricing.objects.all().delete()
        Hotel.objects.all().delete()
        Vehicle.objects.all().delete()

        # Destination Category
        self.category = DestinationCategory.objects.create(
            name="Hill Stations",
            slug="hill-stations",
            icon="fa-mountain"
        )

        # Destinations
        self.dest_shimla = Destination.objects.create(
            category=self.category,
            name="Shimla Hills",
            location="Himachal Pradesh, India",
            description="Queen of the Hills with colonial architecture and pine ridges.",
            highlights="Mall Road\nJakhu Temple\nKalka Toy Train"
        )
        self.dest_manali = Destination.objects.create(
            category=self.category,
            name="Manali Sanctuary",
            location="Himachal Pradesh, India",
            description="Snow peaks and adventure capital.",
            highlights="Solang Valley\nRohtang Pass"
        )

        # Tour Package
        self.package = TourPackage.objects.create(
            destination=self.dest_shimla,
            name="Shimla Colonial Splendor",
            description="A majestic 4-day retreat in the summer capital.",
            duration_days=4,
            base_price=Decimal('10000.00'),
            inclusions="Heritage Walking Tour\nBreakfast\nToy Train Ride",
            exclusions="Airfare\nPersonal Laundry"
        )

        # Package Itineraries
        PackageItinerary.objects.create(
            package=self.package,
            day_number=1,
            title="Arrival in Shimla",
            description="Check-in and evening stroll on Mall Road."
        )
        PackageItinerary.objects.create(
            package=self.package,
            day_number=2,
            title="Kufri Excursion",
            description="Visit Himalayan nature park in Kufri."
        )

        # Hotels in Shimla
        self.hotel_standard = Hotel.objects.create(
            destination=self.dest_shimla,
            name="Pine View Residency",
            tier='standard',
            room_type='Standard Double Room',
            price_per_night=Decimal('1500.00'),
            available_rooms=10,
            description="Comfortable lodge near ridge.",
            is_active=True
        )
        self.hotel_deluxe = Hotel.objects.create(
            destination=self.dest_shimla,
            name="Grand Shimla Regency",
            tier='deluxe',
            room_type='Deluxe Valley Balcony Room',
            price_per_night=Decimal('3500.00'),
            available_rooms=5,
            description="4-star valley facing resort.",
            is_active=True
        )
        self.hotel_premium = Hotel.objects.create(
            destination=self.dest_shimla,
            name="Oberoi Heritage Manor",
            tier='premium',
            room_type='Royal Cedar Suite',
            price_per_night=Decimal('8000.00'),
            available_rooms=2,
            description="5-star heritage luxury suites.",
            is_active=True
        )

        # Hotel in Manali (for destination mismatch testing)
        self.hotel_manali = Hotel.objects.create(
            destination=self.dest_manali,
            name="Manali River Lodge",
            tier='deluxe',
            room_type='Deluxe Riverfront Room',
            price_per_night=Decimal('3000.00'),
            available_rooms=8,
            is_active=True
        )

        # Vehicles
        self.vehicle_sedan = Vehicle.objects.create(
            name="Maruti Suzuki Dzire",
            vehicle_type='sedan',
            seating_capacity=4,
            rate_per_day=Decimal('2000.00'),
            description="Air-conditioned compact sedan.",
            is_available=True
        )
        self.vehicle_suv = Vehicle.objects.create(
            name="Toyota Innova Crysta",
            vehicle_type='suv',
            seating_capacity=6,
            rate_per_day=Decimal('3500.00'),
            description="Spacious luxury SUV.",
            is_available=True
        )
        self.vehicle_minibus = Vehicle.objects.create(
            name="Force Urbania 12-Seater",
            vehicle_type='minibus',
            seating_capacity=12,
            rate_per_day=Decimal('6000.00'),
            description="Luxury tourist mini coach.",
            is_available=True
        )

        # Seasonal Pricing Rules
        self.season_peak = SeasonalPricing.objects.create(
            name="Himalayan Peak Summer",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 6, 30),
            multiplier=Decimal('1.20'),
            is_active=True,
            description="Peak summer tourist influx (+20%)."
        )
        self.season_monsoon = SeasonalPricing.objects.create(
            name="Monsoon Green Saver",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 8, 31),
            multiplier=Decimal('0.90'),
            is_active=True,
            description="Monsoon season discount (-10%)."
        )


class HotelModelTests(Phase4BaseTestCase):
    """Tests for the Hotel model and availability tracking."""

    def test_hotel_creation_and_str(self):
        self.assertEqual(str(self.hotel_standard), "Pine View Residency (Standard - Shimla Hills)")
        self.assertEqual(self.hotel_standard.tier, 'standard')
        self.assertEqual(self.hotel_standard.price_per_night, Decimal('1500.00'))
        self.assertEqual(self.hotel_standard.available_rooms, 10)
        self.assertTrue(self.hotel_standard.is_in_stock)

    def test_hotel_is_in_stock_property(self):
        # 0 rooms -> not in stock
        self.hotel_standard.available_rooms = 0
        self.hotel_standard.save()
        self.assertFalse(self.hotel_standard.is_in_stock)

        # inactive -> not in stock
        self.hotel_standard.available_rooms = 5
        self.hotel_standard.is_active = False
        self.hotel_standard.save()
        self.assertFalse(self.hotel_standard.is_in_stock)

    def test_hotel_destination_relationship(self):
        self.assertEqual(self.hotel_standard.destination, self.dest_shimla)
        self.assertIn(self.hotel_standard, self.dest_shimla.hotels.all())
        self.assertEqual(self.dest_shimla.hotels.count(), 3)


class VehicleModelTests(Phase4BaseTestCase):
    """Tests for the Vehicle model, categories, and fleet availability."""

    def test_vehicle_creation_and_str(self):
        self.assertEqual(str(self.vehicle_sedan), "Maruti Suzuki Dzire (Sedan - 4 Seats)")
        self.assertEqual(self.vehicle_suv.vehicle_type, 'suv')
        self.assertEqual(self.vehicle_suv.seating_capacity, 6)
        self.assertEqual(self.vehicle_suv.rate_per_day, Decimal('3500.00'))
        self.assertTrue(self.vehicle_suv.is_available)

    def test_vehicle_ordering(self):
        vehicles = list(Vehicle.objects.all())
        # Alphabetical by vehicle_type ('minibus', 'sedan', 'suv')
        self.assertEqual(vehicles[0].vehicle_type, 'minibus')
        self.assertEqual(vehicles[1].vehicle_type, 'sedan')
        self.assertEqual(vehicles[2].vehicle_type, 'suv')


class SeasonalPricingTests(Phase4BaseTestCase):
    """Tests for SeasonalPricing model and date range overlap resolution."""

    def test_season_str_representation(self):
        self.assertIn("+20%", str(self.season_peak))
        self.assertIn("-10%", str(self.season_monsoon))

    def test_season_date_overlap_detection(self):
        # Dates inside peak
        self.assertTrue(self.season_peak.covers_dates(date(2026, 5, 10), date(2026, 5, 14)))
        # Dates spanning into peak
        self.assertTrue(self.season_peak.covers_dates(date(2026, 4, 28), date(2026, 5, 5)))
        # Dates completely outside
        self.assertFalse(self.season_peak.covers_dates(date(2026, 3, 1), date(2026, 3, 5)))

    def test_get_active_season_for_dates_function(self):
        # Peak season match
        s = get_active_season_for_dates(date(2026, 5, 10), date(2026, 5, 15))
        self.assertIsNotNone(s)
        self.assertEqual(s.name, "Himalayan Peak Summer")
        self.assertEqual(s.multiplier, Decimal('1.20'))

        # Monsoon season match
        s_monsoon = get_active_season_for_dates(date(2026, 7, 10), date(2026, 7, 15))
        self.assertIsNotNone(s_monsoon)
        self.assertEqual(s_monsoon.multiplier, Decimal('0.90'))

        # Standard non-seasonal period
        s_none = get_active_season_for_dates(date(2026, 11, 1), date(2026, 11, 5))
        self.assertIsNone(s_none)


class PricingEngineCalculationTests(Phase4BaseTestCase):
    """
    Unit tests for the mathematical accuracy of the Dynamic Pricing Engine:
    - Rooms Needed = ceil(persons / 2)
    - Package Base = price * persons
    - Hotel Cost = surcharge/night * nights * rooms
    - Vehicle Cost = rate/day * days
    - Subtotal = Package Base + Hotel Cost + Vehicle Cost
    - Adjusted Subtotal = Subtotal * Seasonal Multiplier
    - GST = 5% of Adjusted Subtotal
    - Grand Total = Adjusted Subtotal + GST
    """

    def test_room_calculation_ceil_rule(self):
        """Test rooms needed = ceil(persons / 2)."""
        self.assertEqual(calculate_rooms_needed(1), 1)
        self.assertEqual(calculate_rooms_needed(2), 1)
        self.assertEqual(calculate_rooms_needed(3), 2)
        self.assertEqual(calculate_rooms_needed(4), 2)
        self.assertEqual(calculate_rooms_needed(5), 3)
        self.assertEqual(calculate_rooms_needed(10), 5)
        self.assertEqual(calculate_rooms_needed(11), 6)

    def test_package_base_calculation(self):
        """Package Base = package.base_price * persons."""
        # 10,000 * 3 persons = 30,000.00
        cost = calculate_tour_cost(
            package=self.package,
            persons=3,
            start_date="2026-11-01",
            end_date="2026-11-04"
        )
        self.assertEqual(cost['package_base'], 30000.00)
        self.assertEqual(cost['hotel_cost'], 0.00)
        self.assertEqual(cost['vehicle_cost'], 0.00)

    def test_hotel_cost_calculation(self):
        """Hotel Cost = hotel.price_per_night * nights * rooms_needed."""
        # Dates: 2026-11-01 to 2026-11-04 -> 3 nights
        # Persons: 3 -> 2 rooms
        # Hotel Deluxe: 3,500/night
        # Expected Hotel Cost = 3500 * 3 * 2 = 21,000.00
        cost = calculate_tour_cost(
            package=self.package,
            persons=3,
            start_date="2026-11-01",
            end_date="2026-11-04",
            hotel=self.hotel_deluxe
        )
        self.assertEqual(cost['rooms_needed'], 2)
        self.assertEqual(cost['nights'], 3)
        self.assertEqual(cost['hotel_cost'], 21000.00)

    def test_vehicle_cost_calculation(self):
        """Vehicle Cost = vehicle.rate_per_day * days."""
        # Dates: 2026-11-01 to 2026-11-04 -> 4 days
        # Vehicle SUV: 3,500/day
        # Expected Vehicle Cost = 3500 * 4 = 14,000.00
        cost = calculate_tour_cost(
            package=self.package,
            persons=3,
            start_date="2026-11-01",
            end_date="2026-11-04",
            vehicle=self.vehicle_suv
        )
        self.assertEqual(cost['days'], 4)
        self.assertEqual(cost['vehicle_cost'], 14000.00)

    def test_full_pipeline_with_peak_season_and_gst(self):
        """
        Full dynamic pricing pipeline under Peak Season (+20%):
        Persons: 2 (1 room)
        Dates: 2026-05-10 to 2026-05-13 (3 nights, 4 days) -> Himalayan Peak Summer (1.20x)
        Package Base: 10,000 * 2 = 20,000.00
        Hotel (Deluxe): 3,500 * 3 nights * 1 room = 10,500.00
        Vehicle (Sedan): 2,000 * 4 days = 8,000.00
        Raw Subtotal: 20,000 + 10,500 + 8,000 = 38,500.00
        Seasonal Adjustment (+20%): 38,500 * 0.20 = 7,700.00
        Adjusted Subtotal: 38,500 * 1.20 = 46,200.00
        GST (5%): 46,200 * 0.05 = 2,310.00
        Grand Total: 46,200 + 2,310 = 48,510.00
        """
        cost = calculate_tour_cost(
            package=self.package,
            persons=2,
            start_date="2026-05-10",
            end_date="2026-05-13",
            hotel=self.hotel_deluxe,
            vehicle=self.vehicle_sedan
        )

        self.assertEqual(cost['package_base'], 20000.00)
        self.assertEqual(cost['hotel_cost'], 10500.00)
        self.assertEqual(cost['vehicle_cost'], 8000.00)
        self.assertEqual(cost['raw_subtotal'], 38500.00)
        self.assertEqual(cost['seasonal_multiplier'], 1.20)
        self.assertEqual(cost['seasonal_adjustment'], 7700.00)
        self.assertEqual(cost['subtotal'], 46200.00)
        self.assertEqual(cost['gst'], 2310.00)
        self.assertEqual(cost['total'], 48510.00)

    def test_full_pipeline_with_monsoon_discount_and_gst(self):
        """
        Full dynamic pricing pipeline under Monsoon Discount (-10%):
        Persons: 4 (2 rooms)
        Dates: 2026-07-10 to 2026-07-13 (3 nights, 4 days) -> Monsoon (0.90x)
        Package Base: 10,000 * 4 = 40,000.00
        Hotel (Standard): 1,500 * 3 nights * 2 rooms = 9,000.00
        Vehicle (SUV): 3,500 * 4 days = 14,000.00
        Raw Subtotal: 40,000 + 9,000 + 14,000 = 63,000.00
        Adjusted Subtotal (-10%): 63,000 * 0.90 = 56,700.00
        Seasonal Adjustment: 56,700 - 63,000 = -6,300.00
        GST (5%): 56,700 * 0.05 = 2,835.00
        Grand Total: 56,700 + 2,835 = 59,535.00
        """
        cost = calculate_tour_cost(
            package=self.package,
            persons=4,
            start_date="2026-07-10",
            end_date="2026-07-13",
            hotel=self.hotel_standard,
            vehicle=self.vehicle_suv
        )

        self.assertEqual(cost['package_base'], 40000.00)
        self.assertEqual(cost['hotel_cost'], 9000.00)
        self.assertEqual(cost['vehicle_cost'], 14000.00)
        self.assertEqual(cost['raw_subtotal'], 63000.00)
        self.assertEqual(cost['seasonal_multiplier'], 0.90)
        self.assertEqual(cost['seasonal_adjustment'], -6300.00)
        self.assertEqual(cost['subtotal'], 56700.00)
        self.assertEqual(cost['gst'], 2835.00)
        self.assertEqual(cost['total'], 59535.00)


class PricingEngineValidationTests(Phase4BaseTestCase):
    """Tests ensuring robust validation against invalid inputs."""

    def test_invalid_persons_validation(self):
        """Rejects zero, negative, or non-integer persons."""
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(self.package, 0, "2026-11-01", "2026-11-04")
        self.assertIn("at least 1", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(self.package, -3, "2026-11-01", "2026-11-04")
        self.assertIn("at least 1", str(ctx.exception))

    def test_invalid_dates_validation(self):
        """Rejects end date earlier than start date."""
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(self.package, 2, "2026-11-10", "2026-11-05")
        self.assertIn("cannot be before", str(ctx.exception))

    def test_hotel_availability_validation(self):
        """Rejects hotel if rooms needed exceed available inventory."""
        # hotel_premium only has 2 rooms available
        # 5 persons require ceil(5/2) = 3 rooms -> exceeds 2 available
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(
                self.package,
                persons=5,
                start_date="2026-11-01",
                end_date="2026-11-04",
                hotel=self.hotel_premium
            )
        self.assertIn("has only 2 room(s) available", str(ctx.exception))

    def test_inactive_hotel_validation(self):
        """Rejects deactivated hotel."""
        self.hotel_standard.is_active = False
        self.hotel_standard.save()
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(
                self.package,
                persons=2,
                start_date="2026-11-01",
                end_date="2026-11-04",
                hotel=self.hotel_standard
            )
        self.assertIn("currently unavailable", str(ctx.exception))

    def test_hotel_destination_mismatch_validation(self):
        """Rejects hotel belonging to another destination."""
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(
                self.package,
                persons=2,
                start_date="2026-11-01",
                end_date="2026-11-04",
                hotel=self.hotel_manali
            )
        self.assertIn("does not match package destination", str(ctx.exception))

    def test_vehicle_capacity_validation(self):
        """Rejects vehicle if passenger group exceeds seating capacity."""
        # Sedan seats 4. Group is 5 persons.
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(
                self.package,
                persons=5,
                start_date="2026-11-01",
                end_date="2026-11-04",
                vehicle=self.vehicle_sedan
            )
        self.assertIn("insufficient for 5 person(s)", str(ctx.exception))

    def test_inactive_vehicle_validation(self):
        """Rejects unavailable vehicle."""
        self.vehicle_suv.is_available = False
        self.vehicle_suv.save()
        with self.assertRaises(ValidationError) as ctx:
            calculate_tour_cost(
                self.package,
                persons=2,
                start_date="2026-11-01",
                end_date="2026-11-04",
                vehicle=self.vehicle_suv
            )
        self.assertIn("currently unavailable", str(ctx.exception))


class PricingApiAndCustomerViewsTests(Phase4BaseTestCase):
    """Tests for customer-facing views and the live calculation JSON API."""

    def test_calculate_price_api_success(self):
        """Test /bookings/api/calculate-price/ returns valid calculation JSON."""
        response = self.client.get(reverse('calculate_price_api'), {
            'package_id': self.package.id,
            'persons': 2,
            'start_date': '2026-05-10',
            'end_date': '2026-05-13',
            'hotel_id': self.hotel_deluxe.id,
            'vehicle_id': self.vehicle_sedan.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['package_base'], 20000.00)
        self.assertEqual(data['hotel_cost'], 10500.00)
        self.assertEqual(data['vehicle_cost'], 8000.00)
        self.assertEqual(data['subtotal'], 46200.00)
        self.assertEqual(data['gst'], 2310.00)
        self.assertEqual(data['total'], 48510.00)

    def test_calculate_price_api_validation_error_returns_400(self):
        """Test API returns 400 when invalid persons or dates are provided."""
        response = self.client.get(reverse('calculate_price_api'), {
            'package_id': self.package.id,
            'persons': 0,
            'start_date': '2026-05-10',
            'end_date': '2026-05-13'
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("error", data)

    def test_hotel_list_view(self):
        """Test /bookings/hotels/ renders hotel catalog and filters."""
        response = self.client.get(reverse('hotel_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pine View Residency")
        self.assertContains(response, "Grand Shimla Regency")
        self.assertContains(response, "Oberoi Heritage Manor")

        # Filter by tier
        res_deluxe = self.client.get(reverse('hotel_list'), {'tier': 'deluxe'})
        self.assertEqual(res_deluxe.status_code, 200)
        self.assertContains(res_deluxe, "Grand Shimla Regency")
        self.assertNotContains(res_deluxe, "Oberoi Heritage Manor")

    def test_hotel_detail_view(self):
        """Test /bookings/hotels/<pk>/ renders hotel details and related package."""
        url = reverse('hotel_detail', args=[self.hotel_deluxe.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Grand Shimla Regency")
        self.assertContains(response, "Deluxe Valley Balcony Room")
        self.assertContains(response, "Shimla Colonial Splendor")

    def test_vehicle_list_view(self):
        """Test /bookings/vehicles/ renders fleet catalog and filters."""
        response = self.client.get(reverse('vehicle_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maruti Suzuki Dzire")
        self.assertContains(response, "Toyota Innova Crysta")
        self.assertContains(response, "Force Urbania")

        # Filter by category
        res_suv = self.client.get(reverse('vehicle_list'), {'type': 'suv'})
        self.assertEqual(res_suv.status_code, 200)
        self.assertContains(res_suv, "Toyota Innova Crysta")
        self.assertNotContains(res_suv, "Maruti Suzuki Dzire")

    def test_vehicle_detail_view(self):
        """Test /bookings/vehicles/<pk>/ renders vehicle details."""
        url = reverse('vehicle_detail', args=[self.vehicle_suv.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toyota Innova Crysta")
        self.assertContains(response, "6 Persons Max")

    def test_package_detail_has_live_calculator(self):
        """Verify the package detail page provides the dynamic cost calculator and inventory."""
        url = reverse('package_detail', args=[self.package.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cost Calculator")
        self.assertContains(response, "id=\"calcPersons\"", html=False)
        self.assertContains(response, "id=\"calcHotel\"", html=False)
        self.assertContains(response, "id=\"calcVehicle\"", html=False)
        self.assertContains(response, "Grand Shimla Regency")
        self.assertContains(response, "Toyota Innova Crysta")


class Phase4AdminTests(Phase4BaseTestCase):
    """Verify admin registration for Phase 4 models."""

    def test_admin_registration(self):
        self.assertTrue(admin.site.is_registered(Hotel))
        self.assertTrue(admin.site.is_registered(Vehicle))
        self.assertTrue(admin.site.is_registered(SeasonalPricing))


class Phase5BookingTests(TestCase):
    def setUp(self):
        # Create a test customer
        self.customer = User.objects.create_user(username='customer1', password='testpassword123', email='c1@test.com')
        self.staff = User.objects.create_user(username='admin1', password='testpassword123', is_staff=True)
        
        # Create package and dependencies
        self.category = DestinationCategory.objects.create(name="Phase 5 Category", slug="phase-5-category", icon="fa-mountain")
        self.destination = Destination.objects.create(category=self.category, name="Test Dest Phase5", is_active=True)
        self.package = TourPackage.objects.create(
            destination=self.destination,
            name="Test Package Phase5",
            base_price=Decimal('10000.00'),
            duration_days=3,
            is_active=True
        )
        self.hotel = Hotel.objects.create(
            destination=self.destination,
            name="Test Hotel",
            price_per_night=Decimal('1000.00'),
            available_rooms=5,
            is_active=True
        )
        self.vehicle = Vehicle.objects.create(
            name="Test Vehicle",
            seating_capacity=4,
            rate_per_day=Decimal('2000.00'),
            is_available=True
        )
        
        self.start_date = timezone.now().date() + timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=2)

    def test_guest_cannot_book(self):
        url = reverse('booking_review')
        data = {
            'package_id': self.package.id,
            'persons': 2,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_customer_can_review_booking(self):
        self.client.login(username='customer1', password='testpassword123')
        url = reverse('booking_review')
        data = {
            'package_id': self.package.id,
            'persons': 2,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'hotel_id': self.hotel.id,
            'vehicle_id': self.vehicle.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review Your Booking")
        self.assertContains(response, self.package.name)
        self.assertContains(response, self.hotel.name)
        self.assertContains(response, self.vehicle.name)

    def test_booking_creation_and_inventory_decrement(self):
        self.client.login(username='customer1', password='testpassword123')
        url = reverse('booking_create')
        initial_rooms = self.hotel.available_rooms
        data = {
            'package_id': self.package.id,
            'persons': 3, # 2 rooms needed
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'hotel_id': self.hotel.id,
            'vehicle_id': self.vehicle.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check booking exists
        booking = Booking.objects.first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(booking.rooms_required, 2)
        
        # Check inventory decremented
        self.hotel.refresh_from_db()
        self.assertEqual(self.hotel.available_rooms, initial_rooms - 2)

    def test_booking_cancellation_restores_inventory(self):
        # Create a booking directly
        booking = Booking.objects.create(
            booking_reference="BKG-TEST-1234",
            customer=self.customer,
            package=self.package,
            start_date=self.start_date,
            end_date=self.end_date,
            persons=3,
            rooms_required=2,
            hotel=self.hotel,
            status='confirmed'
        )
        
        initial_rooms = self.hotel.available_rooms
        
        self.client.login(username='customer1', password='testpassword123')
        url = reverse('booking_cancel', args=[booking.booking_reference])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        
        self.hotel.refresh_from_db()
        self.assertEqual(self.hotel.available_rooms, initial_rooms + 2)

    def test_customer_cannot_see_others_booking(self):
        other_customer = User.objects.create_user(username='customer2', password='testpassword123')
        booking = Booking.objects.create(
            booking_reference="BKG-TEST-5678",
            customer=other_customer,
            package=self.package,
            start_date=self.start_date,
            end_date=self.end_date,
            persons=2,
            rooms_required=1,
            status='confirmed'
        )
        
        self.client.login(username='customer1', password='testpassword123')
        url = reverse('booking_detail', args=[booking.booking_reference])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_my_bookings_list(self):
        Booking.objects.create(
            booking_reference="BKG-MINE-1",
            customer=self.customer,
            package=self.package,
            start_date=self.start_date,
            end_date=self.end_date,
            persons=2,
            rooms_required=1,
            status='confirmed'
        )
        self.client.login(username='customer1', password='testpassword123')
        url = reverse('my_bookings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BKG-MINE-1")

class Phase6DashboardAndBookingTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='customer_phase6', password='testpassword123', email='c6@test.com')
        self.category = DestinationCategory.objects.create(name="Phase 6 Category", slug="phase-6-category", icon="fa-mountain")
        self.destination = Destination.objects.create(category=self.category, name="Test Dest Phase6", is_active=True)
        self.package = TourPackage.objects.create(
            destination=self.destination,
            name="Test Package Phase6",
            base_price=Decimal('10000.00'),
            duration_days=3,
            is_active=True
        )
        
        today = timezone.now().date()
        
        # Upcoming booking
        self.b_upcoming = Booking.objects.create(
            booking_reference="BKG-UPCOMING",
            customer=self.customer,
            package=self.package,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
            persons=2,
            rooms_required=1,
            status='confirmed',
            grand_total=Decimal('10000.00')
        )
        
        # Past booking
        self.b_past = Booking.objects.create(
            booking_reference="BKG-PAST",
            customer=self.customer,
            package=self.package,
            start_date=today - timedelta(days=12),
            end_date=today - timedelta(days=10),
            persons=2,
            rooms_required=1,
            status='completed',
            grand_total=Decimal('10000.00')
        )
        
        # Cancelled booking
        self.b_cancelled = Booking.objects.create(
            booking_reference="BKG-CANCELLED",
            customer=self.customer,
            package=self.package,
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=22),
            persons=2,
            rooms_required=1,
            status='cancelled',
            grand_total=Decimal('10000.00')
        )

    def test_dashboard_shows_upcoming_and_past(self):
        self.client.login(username='customer_phase6', password='testpassword123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Upcoming should show BKG-UPCOMING
        self.assertContains(response, "BKG-UPCOMING")
        
        # Past should show BKG-PAST and BKG-CANCELLED
        self.assertContains(response, "BKG-PAST")
        self.assertContains(response, "BKG-CANCELLED")

    def test_my_bookings_filters(self):
        self.client.login(username='customer_phase6', password='testpassword123')
        
        # Upcoming filter
        res_upcoming = self.client.get(reverse('my_bookings') + '?filter=upcoming')
        self.assertContains(res_upcoming, "BKG-UPCOMING")
        self.assertNotContains(res_upcoming, "BKG-PAST")
        
        # Past filter
        res_past = self.client.get(reverse('my_bookings') + '?filter=past')
        self.assertContains(res_past, "BKG-PAST")
        self.assertNotContains(res_past, "BKG-UPCOMING")
        
        # Cancelled filter
        res_cancel = self.client.get(reverse('my_bookings') + '?filter=cancelled')
        self.assertContains(res_cancel, "BKG-CANCELLED")
        self.assertNotContains(res_cancel, "BKG-UPCOMING")

    def test_dashboard_unauthenticated_access(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)



class Phase8RegressionTests(TestCase):
    """Phase 8: financial integrity, inventory safety, security edge cases."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer_p8', password='testpassword123', email='p8@test.com'
        )
        self.category = DestinationCategory.objects.create(
            name='P8 Category', slug='p8-category', icon='fa-mountain'
        )
        self.destination = Destination.objects.create(
            category=self.category, name='P8 Destination', is_active=True
        )
        self.package = TourPackage.objects.create(
            destination=self.destination,
            name='P8 Package',
            base_price=Decimal('5000.00'),
            duration_days=3,
            is_active=True,
        )
        self.hotel = Hotel.objects.create(
            destination=self.destination,
            name='P8 Hotel',
            price_per_night=Decimal('1000.00'),
            available_rooms=5,
            is_active=True,
        )
        self.vehicle = Vehicle.objects.create(
            name='P8 Vehicle',
            seating_capacity=4,
            rate_per_day=Decimal('1000.00'),
            is_available=True,
        )
        self.start_date = (date.today() + timedelta(days=10)).isoformat()
        self.end_date = (date.today() + timedelta(days=12)).isoformat()

    def test_booking_create_stores_correct_financial_amounts(self):
        """
        Regression test: booking_create must store correct non-zero financial
        amounts. Catches the decimal key-name mismatch bug fixed in Phase 8:
        package_base_cost->package_base, gst_amount->gst, grand_total->total.
        """
        self.client.login(username='customer_p8', password='testpassword123')
        self.client.post(reverse('booking_create'), {
            'package_id': self.package.id,
            'persons': 2,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'hotel_id': self.hotel.id,
            'vehicle_id': self.vehicle.id,
        })
        booking = Booking.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(booking)
        # package_amount: 5000 * 2 = 10000.00
        self.assertGreater(booking.package_amount, Decimal('0.00'),
                           'package_amount must be non-zero (Phase 8 decimal key bug fix)')
        # gst_amount must be positive (5% of subtotal)
        self.assertGreater(booking.gst_amount, Decimal('0.00'),
                           'gst_amount must be non-zero (Phase 8 decimal key bug fix)')
        # grand_total must be positive
        self.assertGreater(booking.grand_total, Decimal('0.00'),
                           'grand_total must be non-zero (Phase 8 decimal key bug fix)')

    def test_repeated_cancellation_does_not_double_restore_inventory(self):
        """
        Safety test: cancelling an already-cancelled booking must not restore
        hotel inventory a second time (idempotency of cancellation).
        """
        booking = Booking.objects.create(
            booking_reference='BKG-P8-CANCEL-TEST',
            customer=self.customer,
            package=self.package,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            persons=2,
            rooms_required=1,
            hotel=self.hotel,
            status='confirmed',
        )
        original_rooms = self.hotel.available_rooms
        self.client.login(username='customer_p8', password='testpassword123')
        url = reverse('booking_cancel', args=[booking.booking_reference])

        # First cancellation — should succeed and restore 1 room
        self.client.post(url)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.hotel.refresh_from_db()
        rooms_after_first = self.hotel.available_rooms
        self.assertEqual(rooms_after_first, original_rooms + 1)

        # Second cancellation — booking is already cancelled, inventory must not change
        self.client.post(url)
        self.hotel.refresh_from_db()
        self.assertEqual(
            self.hotel.available_rooms, rooms_after_first,
            'Repeated cancellation must not restore inventory twice'
        )

    def test_login_open_redirect_blocked(self):
        """
        Security test: the login view must not redirect to external URLs
        passed via the ?next= query parameter.
        """
        self.client.logout()
        response = self.client.post(
            reverse('login') + '?next=http://evil.example.com',
            {'username': 'customer_p8', 'password': 'testpassword123'},
        )
        location = response.get('Location', '')
        self.assertNotIn('evil.example.com', location,
                         'Login must not redirect to external URL (open redirect)')
