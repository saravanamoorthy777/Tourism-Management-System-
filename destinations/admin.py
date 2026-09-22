from django.contrib import admin
from .models import DestinationCategory, Destination, TourPackage, PackageItinerary


@admin.register(DestinationCategory)
class DestinationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'get_destination_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    @admin.display(description="Destinations")
    def get_destination_count(self, obj):
        return obj.destinations.count()


class PackageItineraryInline(admin.StackedInline):
    model = PackageItinerary
    extra = 1
    fields = ('day_number', 'title', 'description', 'activities')
    ordering = ('day_number',)


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'location', 'get_package_count', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'location', 'description', 'highlights')
    ordering = ('name',)

    @admin.display(description="Packages")
    def get_package_count(self, obj):
        return obj.packages.count()


@admin.register(TourPackage)
class TourPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'duration', 'base_price', 'is_active', 'created_at')
    list_filter = ('is_active', 'destination__category', 'destination')
    search_fields = ('name', 'destination__name', 'description')
    inlines = [PackageItineraryInline]
    ordering = ('destination', 'base_price')


@admin.register(PackageItinerary)
class PackageItineraryAdmin(admin.ModelAdmin):
    list_display = ('day_number', 'title', 'package', 'get_destination')
    list_filter = ('package__destination', 'package')
    search_fields = ('title', 'description', 'activities', 'package__name')
    ordering = ('package', 'day_number')

    @admin.display(description="Destination")
    def get_destination(self, obj):
        return obj.package.destination.name
