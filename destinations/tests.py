from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import admin
from .models import DestinationCategory, Destination, TourPackage, PackageItinerary


class CatalogModelTests(TestCase):
    """
    Tests for DestinationCategory, Destination, TourPackage, and PackageItinerary models.
    """

    def setUp(self):
        self.category = DestinationCategory.objects.create(
            name="Adventure Test",
            description="Adventure travel and trails",
            icon="fa-mountain-sun"
        )
        self.destination = Destination.objects.create(
            category=self.category,
            name="Kullu Valley",
            location="Himachal Pradesh, India",
            description="Picturesque mountain valley known for pine forests and Beas river.",
            highlights="River Rafting\nTrout Fishing\nApple Orchards"
        )
        self.package = TourPackage.objects.create(
            destination=self.destination,
            name="Kullu Weekend Getaway",
            description="A scenic 3-day retreat in Kullu valley.",
            duration_days=3,
            base_price=9999.00,
            inclusions="Deluxe Room\nBreakfast & Dinner\nRiver Rafting Permit",
            exclusions="Airfare\nPersonal Laundry"
        )
        self.itinerary_day1 = PackageItinerary.objects.create(
            package=self.package,
            day_number=1,
            title="Arrival in Kullu",
            description="Check into riverside camp, welcome tea and orientation.",
            activities="Camp Check-in, Riverside Walk, Campfire Dinner"
        )
        self.itinerary_day2 = PackageItinerary.objects.create(
            package=self.package,
            day_number=2,
            title="Beas River Rafting Expedition",
            description="Grade III rafting experience with safety briefing and guide.",
            activities="Beas River Rafting, Picnic Lunch, Local Market Visit"
        )

    def test_category_creation_and_slug(self):
        """Test category creation, automatic slug generation, and string representation."""
        self.assertEqual(self.category.slug, "adventure-test")
        self.assertEqual(str(self.category), "Adventure Test")
        self.assertTrue(self.category.is_active)
        self.assertEqual(self.category.active_destinations_count, 1)

    def test_destination_creation_and_highlights(self):
        """Test destination creation, foreign key to category, and highlight parsing."""
        self.assertEqual(str(self.destination), "Kullu Valley (Himachal Pradesh, India)")
        self.assertEqual(self.destination.category, self.category)
        highlights = self.destination.get_highlights_list()
        self.assertIn("River Rafting", highlights)
        self.assertIn("Trout Fishing", highlights)
        self.assertIn("Apple Orchards", highlights)
        self.assertEqual(self.destination.package_count, 1)
        self.assertEqual(float(self.destination.starting_price), 9999.00)

    def test_package_creation_and_duration_generation(self):
        """Test tour package creation, default duration formatting, and inclusions/exclusions."""
        self.assertEqual(self.package.duration, "3 Days / 2 Nights")
        self.assertEqual(self.package.destination, self.destination)
        self.assertIn("Kullu Weekend Getaway", str(self.package))

        inclusions = self.package.get_inclusions_list()
        self.assertEqual(len(inclusions), 3)
        self.assertIn("Deluxe Room", inclusions)
        self.assertIn("River Rafting Permit", inclusions)

        exclusions = self.package.get_exclusions_list()
        self.assertEqual(len(exclusions), 2)
        self.assertIn("Airfare", exclusions)
        self.assertIn("Personal Laundry", exclusions)

    def test_package_itinerary_creation_and_ordering(self):
        """Test itinerary linked to package, day numbering, and activities parsing."""
        itineraries = list(self.package.itineraries.all())
        self.assertEqual(len(itineraries), 2)
        self.assertEqual(itineraries[0].day_number, 1)
        self.assertEqual(itineraries[1].day_number, 2)
        self.assertIn("Day 1: Arrival in Kullu", str(self.itinerary_day1))

        acts = self.itinerary_day1.get_activities_list()
        self.assertIn("Camp Check-in", acts)
        self.assertIn("Riverside Walk", acts)

    def test_package_destination_cascade_relationship(self):
        """Verify that tour package belongs to destination and is accessed through related name."""
        self.assertIn(self.package, self.destination.packages.all())


class CatalogViewsAndFilterTests(TestCase):
    """
    Tests for customer-facing pages, search, category filtering, destination filtering,
    and package sorting.
    """

    def setUp(self):
        self.client = Client()

        # Create 2 Categories
        self.cat_beach = DestinationCategory.objects.create(
            name="Beach Vacation",
            slug="beach-vacation",
            icon="fa-umbrella-beach"
        )
        self.cat_heritage = DestinationCategory.objects.create(
            name="Heritage Trail",
            slug="heritage-trail",
            icon="fa-landmark-dome"
        )

        # Create 2 Destinations
        self.dest_goa = Destination.objects.create(
            category=self.cat_beach,
            name="South Goa Beaches",
            location="Goa, India",
            description="Golden sand beaches and quiet coconut groves.",
            highlights="Palolem Beach\nColva Watersports"
        )
        self.dest_hampi = Destination.objects.create(
            category=self.cat_heritage,
            name="Hampi UNESCO Ruins",
            location="Karnataka, India",
            description="Ancient boulder-strewn landscape with 14th-century Vijayanagara ruins.",
            highlights="Virupaksha Temple\nStone Chariot\nTungabhadra River"
        )

        # Create Tour Packages
        self.pkg_goa_budget = TourPackage.objects.create(
            destination=self.dest_goa,
            name="Goa Weekend Chill",
            description="Relaxing 3-day coastal holiday with beach resort stay.",
            duration_days=3,
            duration="3 Days / 2 Nights",
            base_price=8000.00,
            inclusions="Resort Stay\nBreakfast Buffet",
            exclusions="Flights\nDrinks"
        )
        self.pkg_goa_luxury = TourPackage.objects.create(
            destination=self.dest_goa,
            name="Goa Luxury Cruise Holiday",
            description="Premium 5-day escape with luxury yacht and private villa.",
            duration_days=5,
            duration="5 Days / 4 Nights",
            base_price=25000.00,
            inclusions="Private Villa\nSunset Yacht Cruise\nAll Meals",
            exclusions="Flights"
        )
        self.pkg_hampi = TourPackage.objects.create(
            destination=self.dest_hampi,
            name="Hampi Heritage Expedition",
            description="4-day archaeological tour of imperial ruins.",
            duration_days=4,
            duration="4 Days / 3 Nights",
            base_price=12000.00,
            inclusions="Heritage Hotel\nExpert Historian Guide\nMonument Passes",
            exclusions="Travel to Hospet"
        )

        # Itinerary for Goa Budget
        PackageItinerary.objects.create(
            package=self.pkg_goa_budget,
            day_number=1,
            title="Check-in & Sunset at Palolem",
            description="Arrive at resort, stroll down to Palolem beach for sunset.",
            activities="Beach walk, Sunset cocktails"
        )
        PackageItinerary.objects.create(
            package=self.pkg_goa_budget,
            day_number=2,
            title="Watersports at Colva",
            description="Jet ski and banana boat rides followed by Goan seafood lunch.",
            activities="Jet Ski, Banana Boat, Seafood lunch"
        )

    def test_homepage_view_renders_catalog_elements(self):
        """Test homepage displays categories and featured items."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beach Vacation")
        self.assertContains(response, "Heritage Trail")
        self.assertContains(response, "South Goa Beaches")

    def test_destination_listing_page(self):
        """Test /destinations/ loads with all destinations."""
        response = self.client.get(reverse('destination_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "South Goa Beaches")
        self.assertContains(response, "Hampi UNESCO Ruins")
        self.assertGreaterEqual(response.context['total_count'], 2)

    def test_destination_category_filtering(self):
        """Test filtering destinations by category slug."""
        response = self.client.get(reverse('destination_list'), {'category': 'beach-vacation'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "South Goa Beaches")
        self.assertNotContains(response, "Hampi UNESCO Ruins")
        self.assertEqual(response.context['total_count'], 1)

    def test_destination_search(self):
        """Test searching destinations by keyword."""
        response = self.client.get(reverse('destination_list'), {'q': 'Hampi'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hampi UNESCO Ruins")
        self.assertNotContains(response, "South Goa Beaches")

    def test_destination_detail_page(self):
        """Test /destinations/<id>/ displays destination details and associated packages."""
        url = reverse('destination_detail', args=[self.dest_goa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "South Goa Beaches")
        self.assertContains(response, "Goa Weekend Chill")
        self.assertContains(response, "Goa Luxury Cruise Holiday")
        self.assertNotContains(response, "Hampi Heritage Expedition")

    def test_destination_detail_404_for_invalid_id(self):
        """Test 404 response for nonexistent destination."""
        url = reverse('destination_detail', args=[999999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_package_listing_page(self):
        """Test /packages/ displays all active packages."""
        response = self.client.get(reverse('package_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Goa Weekend Chill")
        self.assertContains(response, "Goa Luxury Cruise Holiday")
        self.assertContains(response, "Hampi Heritage Expedition")
        self.assertGreaterEqual(response.context['total_count'], 3)

    def test_package_destination_filtering(self):
        """Test filtering tour packages by destination ID."""
        response = self.client.get(reverse('package_list'), {'destination': self.dest_hampi.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hampi Heritage Expedition")
        self.assertNotContains(response, "Goa Weekend Chill")
        self.assertEqual(response.context['total_count'], 1)

    def test_package_category_filtering(self):
        """Test filtering tour packages by category slug."""
        response = self.client.get(reverse('package_list'), {'category': 'heritage-trail'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hampi Heritage Expedition")
        self.assertNotContains(response, "Goa Weekend Chill")

    def test_package_search(self):
        """Test searching tour packages by text in title or description."""
        response = self.client.get(reverse('package_list'), {'q': 'Cruise'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Goa Luxury Cruise Holiday")
        self.assertNotContains(response, "Goa Weekend Chill")

    def test_package_sorting_by_price(self):
        """Test sorting tour packages by price ascending and descending."""
        # Price Ascending (default)
        res_asc = self.client.get(reverse('package_list'), {'sort': 'price_asc'})
        pkgs_asc = list(res_asc.context['packages'])
        self.assertEqual(pkgs_asc[0].base_price, 8000.00)
        self.assertEqual(pkgs_asc[-1].base_price, 25000.00)

        # Price Descending
        res_desc = self.client.get(reverse('package_list'), {'sort': 'price_desc'})
        pkgs_desc = list(res_desc.context['packages'])
        self.assertEqual(pkgs_desc[0].base_price, 25000.00)
        self.assertEqual(pkgs_desc[-1].base_price, 8000.00)

    def test_package_sorting_by_duration(self):
        """Test sorting tour packages by duration."""
        # Shortest first
        res_dur = self.client.get(reverse('package_list'), {'sort': 'duration_asc'})
        pkgs_dur = list(res_dur.context['packages'])
        self.assertEqual(pkgs_dur[0].duration_days, 3)
        self.assertEqual(pkgs_dur[-1].duration_days, 5)

    def test_package_detail_page(self):
        """Test /packages/<id>/ displays all package details, inclusions, exclusions, and itinerary."""
        url = reverse('package_detail', args=[self.pkg_goa_budget.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Goa Weekend Chill")
        self.assertContains(response, "South Goa Beaches")
        self.assertContains(response, "3 Days / 2 Nights")
        self.assertContains(response, "8000")
        self.assertContains(response, "Resort Stay")
        self.assertContains(response, "Flights")
        self.assertContains(response, "Day 1: Check-in &amp; Sunset at Palolem")
        self.assertContains(response, "Day 2: Watersports at Colva")

    def test_package_detail_404_for_invalid_id(self):
        """Test 404 response for nonexistent tour package."""
        url = reverse('package_detail', args=[999999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class CatalogAdminTests(TestCase):
    """
    Tests ensuring all models are properly registered with the Django Admin site.
    """

    def test_admin_registration(self):
        """Verify DestinationCategory, Destination, TourPackage, and PackageItinerary are registered in admin."""
        self.assertTrue(admin.site.is_registered(DestinationCategory))
        self.assertTrue(admin.site.is_registered(Destination))
        self.assertTrue(admin.site.is_registered(TourPackage))
        self.assertTrue(admin.site.is_registered(PackageItinerary))
