from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    CustomerRegistrationForm,
    CustomerLoginForm,
    UserUpdateForm,
    ProfileDetailsUpdateForm,
)
from .models import Profile

def register_view(request):
    """
    Handles new customer registration with full name, email, username, and password verification.
    Automatically logs the user in upon successful registration and redirects to the customer dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # The post_save signal creates the Profile automatically; ensure profile exists
            Profile.objects.get_or_create(user=user)

            # Log the user in
            login(request, user)
            display_name = user.first_name or user.username
            messages.success(request, f"Welcome to TourismMS, {display_name}! Your account has been registered successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handles customer and administrative staff login with dual username or email support.
    Supports session persistence (Remember Me).
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Remember me logic
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Session expires when the browser is closed
            else:
                request.session.set_expiry(1209600)  # 2 weeks session

            display_name = user.first_name or user.username
            messages.success(request, f"Welcome back, {display_name}!")

            # Redirect to next URL or customer dashboard
            next_url = request.GET.get('next') or request.POST.get('next')
            # Validate next_url is a safe relative path to prevent open redirect
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password. Please try again.")
    else:
        form = CustomerLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Logs out the user, clears active sessions, and redirects to the homepage with a confirmation toast.
    """
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been logged out successfully. Have a safe journey!")
    return redirect('home')


@login_required
def dashboard_view(request):
    """
    Customer portal dashboard displaying account overview, profile summary,
    and upcoming trips and booking history.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    from bookings.models import Booking
    from django.utils import timezone

    today = timezone.now().date()
    all_bookings = Booking.objects.filter(customer=request.user).select_related(
        'package', 'package__destination'
    ).order_by('-created_at')
    
    upcoming_trips = all_bookings.filter(end_date__gte=today).exclude(status='cancelled').order_by('start_date')
    past_bookings = all_bookings.exclude(id__in=upcoming_trips.values('id'))
    
    context = {
        'profile': profile,
        'upcoming_trips': upcoming_trips,
        'past_bookings': past_bookings,
        'total_bookings_count': all_bookings.count(),
        'upcoming_trips_count': upcoming_trips.count(),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """
    Allows customers to view and update their personal information and contact details.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileDetailsUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile details have been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileDetailsUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)
