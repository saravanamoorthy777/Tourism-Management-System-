from django.db import models
from django.utils.text import slugify


class DestinationCategory(models.Model):
    """
    Categories for grouping travel destinations (e.g. Adventure, Heritage, Beach, Wildlife).
    Managed by administrator.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        default='fa-mountain-sun',
        help_text="FontAwesome icon class (e.g., fa-mountain-sun, fa-landmark-dome, fa-umbrella-beach, fa-paw)"
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Destination Category"
        verbose_name_plural = "Destination Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def active_destinations_count(self):
        return self.destinations.filter(is_active=True).count()


class Destination(models.Model):
    """
    Travel destination model representing geographical locations/tourist spots.
    """
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        DestinationCategory,
        on_delete=models.CASCADE,
        related_name='destinations'
    )
    location = models.CharField(
        max_length=200,
        help_text="City, State / Country (e.g., Manali, Himachal Pradesh)"
    )
    description = models.TextField()
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    highlights = models.TextField(
        help_text="Key highlights/attractions (one per line or comma-separated)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Destination"
        verbose_name_plural = "Destinations"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.location})"

    def get_highlights_list(self):
        """Return highlights as a clean list of strings for template rendering."""
        if not self.highlights:
            return []
        raw_items = self.highlights.replace('\r\n', '\n').split('\n')
        items = []
        for raw in raw_items:
            for sub in raw.split(','):
                cleaned = sub.strip()
                if cleaned:
                    items.append(cleaned)
        return items

    @property
    def active_packages(self):
        return self.packages.filter(is_active=True)

    @property
    def package_count(self):
        return self.packages.filter(is_active=True).count()

    @property
    def starting_price(self):
        cheapest = self.packages.filter(is_active=True).order_by('base_price').first()
        return cheapest.base_price if cheapest else None


class TourPackage(models.Model):
    """
    Tour package linked to a destination. Includes pricing, duration, inclusions and exclusions.
    """
    name = models.CharField(max_length=200, verbose_name="Package Name")
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='packages'
    )
    description = models.TextField()
    duration_days = models.PositiveIntegerField(
        default=3,
        help_text="Duration in days (used for numeric filtering and sorting)"
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        help_text="Display duration text (e.g., '4 Days / 3 Nights')"
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base price per person in INR"
    )
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    inclusions = models.TextField(
        blank=True,
        help_text="Items included in this package (enter one per line)"
    )
    exclusions = models.TextField(
        blank=True,
        help_text="Items excluded from this package (enter one per line)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tour Package"
        verbose_name_plural = "Tour Packages"
        ordering = ['base_price']

    def save(self, *args, **kwargs):
        if not self.duration:
            nights = max(1, self.duration_days - 1)
            self.duration = f"{self.duration_days} Days / {nights} Nights"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.destination.name}"

    def get_inclusions_list(self):
        """Return inclusions as a clean list of lines."""
        if not self.inclusions:
            return []
        lines = [line.strip() for line in self.inclusions.replace('\r\n', '\n').split('\n') if line.strip()]
        return lines

    def get_exclusions_list(self):
        """Return exclusions as a clean list of lines."""
        if not self.exclusions:
            return []
        lines = [line.strip() for line in self.exclusions.replace('\r\n', '\n').split('\n') if line.strip()]
        return lines


class PackageItinerary(models.Model):
    """
    Day-by-day itinerary breakdown for a TourPackage.
    """
    package = models.ForeignKey(
        TourPackage,
        on_delete=models.CASCADE,
        related_name='itineraries'
    )
    day_number = models.PositiveIntegerField(default=1, verbose_name="Day Number")
    title = models.CharField(max_length=200, help_text="e.g., Arrival in Manali & Local Acclimatization")
    description = models.TextField()
    activities = models.TextField(
        blank=True,
        help_text="Key activities/sites visited on this day (enter one per line or comma-separated)"
    )

    class Meta:
        verbose_name = "Package Itinerary"
        verbose_name_plural = "Package Itineraries"
        ordering = ['day_number']
        unique_together = ('package', 'day_number')

    def __str__(self):
        return f"Day {self.day_number}: {self.title} ({self.package.name})"

    def get_activities_list(self):
        """Return activities as a clean list of strings."""
        if not self.activities:
            return []
        raw_items = self.activities.replace('\r\n', '\n').split('\n')
        items = []
        for raw in raw_items:
            for sub in raw.split(','):
                cleaned = sub.strip()
                if cleaned:
                    items.append(cleaned)
        return items
