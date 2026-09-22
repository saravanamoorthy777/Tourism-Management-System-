from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile

class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('dashboard')
        self.profile_url = reverse('profile')

        self.user_data = {
            'username': 'traveler_sam',
            'first_name': 'Sameer',
            'last_name': 'Verma',
            'email': 'sameer.verma@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
        }

    def test_customer_registration_success(self):
        """Test successful registration and automatic profile creation."""
        response = self.client.post(self.register_url, data=self.user_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.dashboard_url)

        # Verify user created in DB
        user = User.objects.filter(username='traveler_sam').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Sameer')
        self.assertEqual(user.email, 'sameer.verma@example.com')
        self.assertTrue(user.check_password('StrongPassword123!'))

        # Verify Profile created via post_save signal
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.full_name, 'Sameer Verma')

    def test_registration_password_mismatch(self):
        """Test registration rejection when passwords do not match."""
        invalid_data = self.user_data.copy()
        invalid_data['confirm_password'] = 'MismatchPassword999'
        response = self.client.post(self.register_url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='traveler_sam').exists())
        self.assertContains(response, "Passwords do not match")

    def test_registration_duplicate_username_and_email(self):
        """Test rejection of duplicate usernames and emails."""
        self.client.post(self.register_url, data=self.user_data)
        self.client.logout()

        # Duplicate username
        dup_user = self.user_data.copy()
        dup_user['email'] = 'unique.email@example.com'
        response = self.client.post(self.register_url, data=dup_user)
        self.assertContains(response, "already taken")

        # Duplicate email
        dup_email = self.user_data.copy()
        dup_email['username'] = 'unique_username'
        response = self.client.post(self.register_url, data=dup_email)
        self.assertContains(response, "email address already exists")

    def test_login_with_username_and_email(self):
        """Test dual-mode authentication via both username and email."""
        # Create user
        self.client.post(self.register_url, data=self.user_data)
        self.client.logout()

        # Login using username
        res1 = self.client.post(self.login_url, {
            'username_or_email': 'traveler_sam',
            'password': 'StrongPassword123!',
            'remember_me': True
        }, follow=True)
        self.assertEqual(res1.status_code, 200)
        self.assertRedirects(res1, self.dashboard_url)
        self.client.logout()

        # Login using email address
        res2 = self.client.post(self.login_url, {
            'username_or_email': 'sameer.verma@example.com',
            'password': 'StrongPassword123!',
            'remember_me': True
        }, follow=True)
        self.assertEqual(res2.status_code, 200)
        self.assertRedirects(res2, self.dashboard_url)

    def test_login_invalid_credentials(self):
        """Test rejection with invalid password."""
        self.client.post(self.register_url, data=self.user_data)
        self.client.logout()

        response = self.client.post(self.login_url, {
            'username_or_email': 'traveler_sam',
            'password': 'WrongPasswordXYZ'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid credentials")

    def test_protected_dashboard_redirects_unauthenticated(self):
        """Test unauthenticated access to dashboard redirects to login."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_profile_update(self):
        """Test customer updating their personal and profile details."""
        # Register and log in
        self.client.post(self.register_url, data=self.user_data)

        # Update profile
        update_data = {
            'first_name': 'Sameer Kumar',
            'last_name': 'Verma',
            'email': 'sameer.verma@example.com',
            'phone_number': '+91 9876543210',
            'city': 'Jaipur',
            'state': 'Rajasthan',
            'pincode': '302001',
            'address': 'Plot 42, Civil Lines',
        }
        response = self.client.post(self.profile_url, data=update_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your profile details have been updated successfully")

        # Verify DB changes
        user = User.objects.get(username='traveler_sam')
        self.assertEqual(user.first_name, 'Sameer Kumar')
        self.assertEqual(user.profile.city, 'Jaipur')
        self.assertEqual(user.profile.phone_number, '+91 9876543210')

    def test_logout(self):
        """Test customer logout clears session."""
        self.client.post(self.register_url, data=self.user_data)
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "logged out successfully")
        
        # Verify access to dashboard is now blocked
        res_dash = self.client.get(self.dashboard_url)
        self.assertEqual(res_dash.status_code, 302)
