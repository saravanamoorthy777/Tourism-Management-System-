from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from destinations.models import Destination, DestinationCategory, TourPackage
from bookings.models import Booking
from decimal import Decimal
from datetime import date, timedelta


class ReportsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Standard customer
        self.user = User.objects.create_user(
            username='testuser_p7', password='password123', email='test_p7@example.com'
        )
        # Staff user
        self.staff_user = User.objects.create_user(
            username='staffuser_p7', password='password123', is_staff=True
        )

        # Minimal catalog objects
        self.category = DestinationCategory.objects.create(name='Test Category P7')
        self.destination = Destination.objects.create(
            name='Test Dest P7', category=self.category, location='Test Loc'
        )
        self.package = TourPackage.objects.create(
            name='Test Pkg P7', destination=self.destination, base_price=Decimal('1000.00')
        )

        # Two test bookings
        self.booking1 = Booking.objects.create(
            booking_reference='BKG-P7-TEST-1',
            customer=self.user,
            package=self.package,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            persons=2,
            status='confirmed',
            grand_total=Decimal('2000.00'),
        )
        self.booking2 = Booking.objects.create(
            booking_reference='BKG-P7-TEST-2',
            customer=self.user,
            package=self.package,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            persons=1,
            status='pending',
            grand_total=Decimal('1000.00'),
        )

    # ------------------------------------------------------------------
    # Access control
    # ------------------------------------------------------------------

    def test_dashboard_access_denied_for_normal_user(self):
        """Normal customers cannot access the admin dashboard (redirected)."""
        self.client.login(username='testuser_p7', password='password123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())

    def test_bookings_access_denied_for_normal_user(self):
        """Normal customers cannot access booking management."""
        self.client.login(username='testuser_p7', password='password123')
        response = self.client.get(reverse('reports:manage_bookings'))
        self.assertEqual(response.status_code, 302)

    def test_customers_access_denied_for_normal_user(self):
        """Normal customers cannot access customer management."""
        self.client.login(username='testuser_p7', password='password123')
        response = self.client.get(reverse('reports:manage_customers'))
        self.assertEqual(response.status_code, 302)

    def test_analytics_access_denied_for_normal_user(self):
        """Normal customers cannot access analytics."""
        self.client.login(username='testuser_p7', password='password123')
        response = self.client.get(reverse('reports:analytics'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_user_denied(self):
        """Unauthenticated users are redirected from admin pages."""
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 302)

    # ------------------------------------------------------------------
    # Dashboard stats
    # ------------------------------------------------------------------

    def test_dashboard_access_allowed_for_staff(self):
        """Staff users can access the dashboard and stats match live DB counts."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/dashboard.html')

        # Compare context values against live ORM queries (DB-state-agnostic)
        self.assertEqual(
            response.context['total_customers'],
            User.objects.filter(is_staff=False).count(),
        )
        self.assertEqual(
            response.context['total_destinations'],
            Destination.objects.count(),
        )
        self.assertEqual(
            response.context['total_bookings'],
            Booking.objects.count(),
        )
        self.assertEqual(
            response.context['confirmed_bookings'],
            Booking.objects.filter(status='confirmed').count(),
        )
        # Revenue must be a non-negative number
        self.assertGreaterEqual(response.context['total_revenue'], 0)

    def test_dashboard_contains_our_booking_in_total(self):
        """Dashboard confirmed count includes the confirmed booking we created."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:dashboard'))
        self.assertGreaterEqual(response.context['confirmed_bookings'], 1)

    # ------------------------------------------------------------------
    # Booking management
    # ------------------------------------------------------------------

    def test_booking_management_view(self):
        """Booking management page loads for staff and lists bookings."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:manage_bookings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/booking_management.html')
        # The two test bookings must appear
        refs = [b.booking_reference for b in response.context['bookings']]
        self.assertIn('BKG-P7-TEST-1', refs)
        self.assertIn('BKG-P7-TEST-2', refs)

    def test_booking_management_search_by_reference(self):
        """Searching by reference narrows results to just that booking."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(
            reverse('reports:manage_bookings'), {'q': 'BKG-P7-TEST-1'}
        )
        self.assertEqual(response.status_code, 200)
        refs = [b.booking_reference for b in response.context['bookings']]
        self.assertIn('BKG-P7-TEST-1', refs)
        self.assertNotIn('BKG-P7-TEST-2', refs)

    def test_booking_management_filter_by_status(self):
        """Filtering by status=confirmed returns only confirmed bookings."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(
            reverse('reports:manage_bookings'), {'status': 'confirmed'}
        )
        self.assertEqual(response.status_code, 200)
        for booking in response.context['bookings']:
            self.assertEqual(booking.status, 'confirmed')

    def test_update_booking_status(self):
        """Staff can POST a new status and it is persisted."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.post(
            reverse('reports:update_booking_status', args=[self.booking2.id]),
            {'status': 'completed'},
        )
        self.assertRedirects(response, reverse('reports:manage_bookings'))
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking2.status, 'completed')

    def test_update_booking_status_invalid(self):
        """Submitting an invalid status leaves the booking unchanged."""
        self.client.login(username='staffuser_p7', password='password123')
        self.client.post(
            reverse('reports:update_booking_status', args=[self.booking1.id]),
            {'status': 'INVALID_STATUS'},
        )
        self.booking1.refresh_from_db()
        self.assertEqual(self.booking1.status, 'confirmed')

    # ------------------------------------------------------------------
    # Customer management
    # ------------------------------------------------------------------

    def test_customer_management_view(self):
        """Customer management page loads and includes our test customer."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:manage_customers'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/customer_management.html')
        usernames = [c.username for c in response.context['customers']]
        self.assertIn('testuser_p7', usernames)
        # Staff users must NOT appear in customer list
        self.assertNotIn('staffuser_p7', usernames)

    def test_customer_management_booking_count_annotation(self):
        """Customers are annotated with correct booking count."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(
            reverse('reports:manage_customers'), {'q': 'testuser_p7'}
        )
        customers = list(response.context['customers'])
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0].booking_count, 2)

    def test_customer_management_search(self):
        """Customer search returns matching customers only."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(
            reverse('reports:manage_customers'), {'q': 'testuser_p7'}
        )
        self.assertEqual(response.status_code, 200)
        usernames = [c.username for c in response.context['customers']]
        self.assertIn('testuser_p7', usernames)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def test_analytics_reports_view(self):
        """Analytics page loads with all expected context keys."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/analytics.html')
        for key in ('booking_summary', 'revenue_summary', 'popular_packages',
                    'popular_destinations', 'hotel_usage', 'vehicle_usage'):
            self.assertIn(key, response.context)

    def test_analytics_booking_summary_correct(self):
        """Booking summary totals match live DB aggregate."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:analytics'))
        summary = response.context['booking_summary']
        self.assertEqual(summary['total'], Booking.objects.count())
        self.assertEqual(
            summary['confirmed'], Booking.objects.filter(status='confirmed').count()
        )
        self.assertEqual(
            summary['pending'], Booking.objects.filter(status='pending').count()
        )

    def test_analytics_revenue_is_non_negative(self):
        """Revenue summary returns a non-negative value."""
        self.client.login(username='staffuser_p7', password='password123')
        response = self.client.get(reverse('reports:analytics'))
        total = response.context['revenue_summary']['total'] or Decimal('0.00')
        self.assertGreaterEqual(total, Decimal('0.00'))
