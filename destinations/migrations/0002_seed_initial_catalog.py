from django.db import migrations


def seed_categories_and_catalog(apps, schema_editor):
    DestinationCategory = apps.get_model('destinations', 'DestinationCategory')
    Destination = apps.get_model('destinations', 'Destination')
    TourPackage = apps.get_model('destinations', 'TourPackage')
    PackageItinerary = apps.get_model('destinations', 'PackageItinerary')

    # 1. Create Required Categories
    categories_data = [
        {
            'name': 'Adventure',
            'slug': 'adventure',
            'icon': 'fa-mountain-sun',
            'description': 'High-altitude treks, river rafting expeditions, paragliding, and camping under Himalayan stars.',
        },
        {
            'name': 'Heritage',
            'slug': 'heritage',
            'icon': 'fa-landmark-dome',
            'description': 'Ancient architectural marvels, majestic royal palaces, historic forts, and UNESCO World Heritage sites.',
        },
        {
            'name': 'Beach',
            'slug': 'beach',
            'icon': 'fa-umbrella-beach',
            'description': 'Sun-kissed coastlines, pristine waters, scuba diving adventures, sunset cruises, and vibrant beach culture.',
        },
        {
            'name': 'Wildlife',
            'slug': 'wildlife',
            'icon': 'fa-paw',
            'description': 'Thrilling jungle jeep safaris, protected tiger reserves, exotic birdwatching, and pristine natural habitats.',
        },
    ]

    cat_map = {}
    for data in categories_data:
        cat, _ = DestinationCategory.objects.get_or_create(
            name=data['name'],
            defaults={
                'slug': data['slug'],
                'icon': data['icon'],
                'description': data['description'],
                'is_active': True,
            }
        )
        cat_map[data['name']] = cat

    # 2. Seed Initial Destinations
    destinations_data = [
        {
            'category': 'Adventure',
            'name': 'Manali Valley',
            'location': 'Himachal Pradesh, India',
            'description': 'Nestled in the majestic Pir Panjal and Dhauladhar ranges, Manali is India\'s premier adventure hub offering snow sports in Solang Valley, thrilling treks over Rohtang Pass, and tranquil pine forest trails.',
            'highlights': 'Solang Valley Snow Sports\nRohtang Pass Snow Point\nOld Manali Bohemian Cafes\nJogini Waterfall Trek\nHadimba Devi Wooden Temple',
        },
        {
            'category': 'Adventure',
            'name': 'Rishikesh',
            'location': 'Uttarakhand, India',
            'description': 'The Yoga Capital of the World and heart of white-water rafting on the sacred Ganges river, framed by the lush Himalayan foothills.',
            'highlights': 'White Water River Rafting (Grade IV)\nBungee Jumping from 83m Platform\nEvening Ganga Aarti at Triveni Ghat\nCliff Jumping & Riverside Camping',
        },
        {
            'category': 'Heritage',
            'name': 'Jaipur (Pink City)',
            'location': 'Rajasthan, India',
            'description': 'The crown jewel of Rajasthan royal history, featuring pink sandstone architecture, opulent hilltop forts, astronomical wonders, and centuries-old artisan bazaars.',
            'highlights': 'Amber Fort & Sheesh Mahal\nHawa Mahal (Palace of Winds)\nCity Palace Royal Residence\nJantar Mantar UNESCO Observatory\nTraditional Rajasthani Thali Dining',
        },
        {
            'category': 'Beach',
            'name': 'Goa Coastline',
            'location': 'Goa, India',
            'description': 'A tropical paradise blending Portuguese colonial heritage with sun-drenched golden beaches, water sports, palm groves, and energetic beachside shacks.',
            'highlights': 'Calangute & Baga Watersports\nHistoric Aguada Portuguese Fort\nMandovi River Sunset Cruise\nAnjuna Flea Market\nPalolem Serene Crescent Beach',
        },
        {
            'category': 'Wildlife',
            'name': 'Jim Corbett National Park',
            'location': 'Uttarakhand, India',
            'description': 'India\'s oldest national park and legendary tiger reserve situated along the Ramganga river, home to wild Bengal tigers, Asian elephants, and over 600 bird species.',
            'highlights': 'Open Jeep Safari in Dhikala Zone\nRoyal Bengal Tiger Tracking\nElephant Herd Spotting along Ramganga River\nCorbett Falls & Nature Trails\nLuxury Eco-Resort Jungle Stays',
        },
    ]

    dest_map = {}
    for d_data in destinations_data:
        dest, _ = Destination.objects.get_or_create(
            name=d_data['name'],
            category=cat_map[d_data['category']],
            defaults={
                'location': d_data['location'],
                'description': d_data['description'],
                'highlights': d_data['highlights'],
                'is_active': True,
            }
        )
        dest_map[d_data['name']] = dest

    # 3. Seed Initial Tour Packages
    packages_data = [
        {
            'destination': 'Manali Valley',
            'name': 'Himalayan High Altitude Adventure',
            'description': 'An adrenaline-filled 4-day expedition through the snow peaks of Manali, featuring paragliding, river crossing, and camping in Solang Valley.',
            'duration_days': 4,
            'duration': '4 Days / 3 Nights',
            'base_price': 14999.00,
            'inclusions': 'Accommodation in 3-Star mountain view hotels\nDaily buffet breakfast and dinner\nAll transfers and sightseeing by private cab\nSolang Valley adventure sports pass\nCertified trekking and rafting guides',
            'exclusions': 'Airfare or train tickets to base hub\nPersonal expenses and laundry\nRohtang Pass special green permit fee\nTravel and medical insurance',
            'itineraries': [
                {
                    'day_number': 1,
                    'title': 'Arrival in Manali & Old Manali Stroll',
                    'description': 'Arrive in Manali, check in to your mountain lodge, rest, and spend the afternoon exploring the vibrant cafes and wooden architecture of Old Manali.',
                    'activities': 'Hotel check-in, Old Manali walking tour, Hadimba Devi temple visit',
                },
                {
                    'day_number': 2,
                    'title': 'Solang Valley Adventure & Paragliding',
                    'description': 'Head to the picturesque Solang Valley for tandem paragliding, zorbing, and ropeway cable car rides with panoramic mountain vistas.',
                    'activities': 'Tandem paragliding, Solang ropeway, quad biking, campfire dinner',
                },
                {
                    'day_number': 3,
                    'title': 'Jogini Waterfall Trek & Vashisht Hot Springs',
                    'description': 'Scenic morning hike through apple orchards and pine groves to the cascading Jogini Waterfalls, followed by a dip in natural sulphur hot springs.',
                    'activities': 'Jogini waterfall trek, natural hot spring bath, Mall Road souvenir shopping',
                },
                {
                    'day_number': 4,
                    'title': 'Naggar Castle & Departure',
                    'description': 'Visit the historic medieval Naggar Castle overlooking the Beas valley and conclude the tour with fond memories.',
                    'activities': 'Naggar Castle tour, art gallery visit, return transfer',
                },
            ]
        },
        {
            'destination': 'Jaipur (Pink City)',
            'name': 'Royal Rajasthan Heritage Trail',
            'description': 'Immerse yourself in regal magnificence with guided royal palace tours, elephant hill climbs at Amber Fort, and authentic folk music performances.',
            'duration_days': 3,
            'duration': '3 Days / 2 Nights',
            'base_price': 11499.00,
            'inclusions': 'Heritage hotel stay with royal welcome\nBreakfast and royal Rajasthani banquet\nMonument entry passes and English/Hindi guides\nAir-conditioned private vehicle for all excursions',
            'exclusions': 'Camera and video camera entry tickets\nTips and porterage charges\nPersonal shopping and snacks',
            'itineraries': [
                {
                    'day_number': 1,
                    'title': 'Arrival & The Grand City Palace',
                    'description': 'Check in to a heritage haveli hotel. Explore City Palace, Chandra Mahal, and the astronomical wonders of Jantar Mantar.',
                    'activities': 'Haveli welcome, City Palace tour, Jantar Mantar sundial visit',
                },
                {
                    'day_number': 2,
                    'title': 'Amber Fort & Hawa Mahal Discovery',
                    'description': 'Ascend the rugged hills of Amer to witness the glittering Sheesh Mahal, then photograph the intricate honeycomb facade of Hawa Mahal.',
                    'activities': 'Amber Fort exploration, Sheesh Mahal mirror art, Hawa Mahal photo stop, Chokhi Dhani evening',
                },
                {
                    'day_number': 3,
                    'title': 'Nahargarh Fort & Local Bazaars',
                    'description': 'Catch a breathtaking sunrise panoramic view from Nahargarh Fort, followed by shopping for blue pottery and textiles in Johari Bazaar.',
                    'activities': 'Nahargarh viewpoint, Johari Bazaar shopping, departure transfer',
                },
            ]
        },
        {
            'destination': 'Goa Coastline',
            'name': 'Goa Coastal Cruise & Beach Getaway',
            'description': 'A coastal escape featuring dolphin spotting boat tours, water sports thrills, UNESCO churches of Old Goa, and scenic sunset dinner cruises.',
            'duration_days': 5,
            'duration': '5 Days / 4 Nights',
            'base_price': 18999.00,
            'inclusions': 'Beach resort stay with swimming pool access\nDaily breakfast buffet\nFull-day North Goa and South Goa guided sightseeing\nMandovi River sunset cruise pass with live DJ\nAirport/railway station pickup and drop',
            'exclusions': 'Scuba diving license courses\nAlcoholic beverages and personal club entries\nWatersports optional upgrades',
            'itineraries': [
                {
                    'day_number': 1,
                    'title': 'Arrival in Goa & Beach Relaxation',
                    'description': 'Warm welcome at Goa airport or station, transfer to beach resort, and relax by the golden shores.',
                    'activities': 'Resort check-in, sunset beach walk, beach shack welcome dinner',
                },
                {
                    'day_number': 2,
                    'title': 'North Goa Beaches & Water Sports',
                    'description': 'Thrilling water activities at Baga beach including parasailing, jet skiing, and banana boat rides, followed by sunset at Fort Aguada.',
                    'activities': 'Parasailing, jet ski, Fort Aguada lighthouse, Anjuna beach sunset',
                },
                {
                    'day_number': 3,
                    'title': 'South Goa Heritage & Mandovi Cruise',
                    'description': 'Visit the Basilica of Bom Jesus, Se Cathedral in Old Goa, followed by an evening sunset cruise along the scenic Mandovi river.',
                    'activities': 'Old Goa churches, Mangueshi temple, Mandovi cruise with Goan folk dance',
                },
                {
                    'day_number': 4,
                    'title': 'Dudhsagar Waterfall & Spice Plantation',
                    'description': 'Exciting jeep ride to the four-tiered Dudhsagar waterfall and an aromatic guided walk through an organic spice plantation.',
                    'activities': 'Dudhsagar waterfall trip, spice plantation traditional lunch',
                },
                {
                    'day_number': 5,
                    'title': 'Souvenir Shopping & Farewell',
                    'description': 'Leisurely morning for cashews and feni shopping, followed by scheduled airport transfer.',
                    'activities': 'Panaji local market, departure transfer',
                },
            ]
        },
        {
            'destination': 'Jim Corbett National Park',
            'name': 'Corbett Wilderness Safari Experience',
            'description': 'A wildlife lover\'s dream getaway featuring dawn and dusk open-top 4x4 Gypsy jungle safaris inside protected tiger territory.',
            'duration_days': 3,
            'duration': '3 Days / 2 Nights',
            'base_price': 12999.00,
            'inclusions': 'Luxury jungle cottage stay near Ramganga river\nAll meals (Breakfast, Lunch, Dinner)\n2 Exclusive Jungle Gypsy Safaris with forest permit & naturalist\nEvening wildlife documentary and bonfire',
            'exclusions': 'Video camera charges inside forest reserve\nPersonal tipping to drivers and naturalists\nTransfers from Delhi / Kathgodam',
            'itineraries': [
                {
                    'day_number': 1,
                    'title': 'Welcome to Corbett & Evening Nature Walk',
                    'description': 'Arrive at the jungle resort, lunch by the river, and take a guided nature walk along the Kosi riverbank.',
                    'activities': 'Resort check-in, Kosi riverbank walk, wildlife orientation and bonfire',
                },
                {
                    'day_number': 2,
                    'title': 'Dawn Jungle Safari & Corbett Falls',
                    'description': 'Early morning open 4x4 Gypsy safari into Bijrani or Jhirna zone to track tigers and wild elephants, followed by an afternoon visit to Corbett Falls.',
                    'activities': 'Morning jeep safari, tiger tracking, Corbett Falls visit, evening audio-visual presentation',
                },
                {
                    'day_number': 3,
                    'title': 'Dhangarhi Museum & Departure',
                    'description': 'Visit the Dhangarhi heritage museum showcasing flora and fauna exhibits, followed by checkout and return journey.',
                    'activities': 'Dhangarhi museum tour, souvenir collection, departure',
                },
            ]
        },
    ]

    for p_data in packages_data:
        dest = dest_map[p_data['destination']]
        itins = p_data.pop('itineraries')
        p_name = p_data.pop('name')
        p_data.pop('destination')

        pkg, _ = TourPackage.objects.get_or_create(
            name=p_name,
            destination=dest,
            defaults=p_data
        )

        for itin in itins:
            PackageItinerary.objects.get_or_create(
                package=pkg,
                day_number=itin['day_number'],
                defaults={
                    'title': itin['title'],
                    'description': itin['description'],
                    'activities': itin['activities'],
                }
            )


def remove_seed_data(apps, schema_editor):
    DestinationCategory = apps.get_model('destinations', 'DestinationCategory')
    DestinationCategory.objects.filter(name__in=['Adventure', 'Heritage', 'Beach', 'Wildlife']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_catalog, remove_seed_data),
    ]
