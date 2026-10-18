from decimal import Decimal
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, UserProfile
from movies.models import Genre, Actor, Movie
from cinemas.models import Cinema, Screen, Seat
from shows.models import Show, ShowSeat
from bookings.models import Coupon, Booking, BookingSeat
from payments.models import Payment
from tickets.models import Ticket
from accounts.models import Notification
from movies.models import Wishlist
from reviews.models import Review


class Command(BaseCommand):
    help = 'Seeds database with realistic cinemas, screens, movies, shows, seats, coupons, and test users.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting database seeding for CineReserve..."))

        # 1. Create Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@cinereserve.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '9876543210',
            }
        )
        admin_user.set_password('Admin@1234')
        admin_user.save()

        manager_user, _ = User.objects.get_or_create(
            username='manager_pvr',
            defaults={
                'email': 'manager@pvr.com',
                'first_name': 'Rajesh',
                'last_name': 'Sharma',
                'role': User.ROLE_CINEMA_MANAGER,
                'is_staff': True,
                'phone_number': '9876543211',
            }
        )
        manager_user.set_password('Manager@1234')
        manager_user.save()

        customer1, _ = User.objects.get_or_create(
            username='customer1',
            defaults={
                'email': 'customer1@cinereserve.com',
                'first_name': 'Aarav',
                'last_name': 'Patel',
                'role': User.ROLE_CUSTOMER,
                'phone_number': '9876543212',
                'date_of_birth': datetime.date(2001, 5, 14),
            }
        )
        customer1.set_password('Customer@1234')
        customer1.save()

        customer2, _ = User.objects.get_or_create(
            username='customer2',
            defaults={
                'email': 'customer2@cinereserve.com',
                'first_name': 'Ananya',
                'last_name': 'Iyer',
                'role': User.ROLE_CUSTOMER,
                'phone_number': '9876543213',
                'date_of_birth': datetime.date(2002, 8, 22),
            }
        )
        customer2.set_password('Customer@1234')
        customer2.save()

        self.stdout.write(self.style.SUCCESS("[OK] Test users created (admin, manager_pvr, customer1, customer2)"))

        # 2. Create Genres
        genre_data = [
            ("Action", "High-octane sequences, combat, and thrill."),
            ("Sci-Fi", "Futuristic technology, space exploration, and cybernetic realities."),
            ("Adventure", "Epic journeys, exploration, and heroic quests."),
            ("Comedy", "Humor, satire, and lighthearted narratives."),
            ("Horror", "Psychological thrills, paranormal horrors, and eerie suspense."),
            ("Romance", "Love stories, emotional depth, and romantic relationships."),
            ("Animation", "Visually breathtaking CGI and heartwarming tales for all ages."),
            ("Drama", "Compelling human conflict, emotional journeys, and drama."),
            ("Thriller", "Edge-of-the-seat mysteries, mind-bending twists, and suspense."),
        ]
        genres = {}
        for name, desc in genre_data:
            g, _ = Genre.objects.get_or_create(name=name, defaults={'description': desc})
            genres[name] = g

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(genres)} Genres created"))

        # 3. Create Actors
        actors_data = [
            "Robert Downey Jr.", "Chris Evans", "Scarlett Johansson", "Ryan Reynolds",
            "Leonardo DiCaprio", "Emma Stone", "Cillian Murphy", "Zendaya", "Margot Robbie"
        ]
        actors = {}
        for act_name in actors_data:
            act, _ = Actor.objects.get_or_create(name=act_name)
            actors[act_name] = act

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(actors)} Actors created"))

        # 4. Create Movies
        movies_info = [
            {
                "title": "Avengers: Quantum Odyssey",
                "synopsis": "When a multiversal anomaly threatens spacetime itself, the world's greatest heroes reunite to navigate quantum dimensions and battle a temporal warlord.",
                "duration": 156,
                "genres": ["Action", "Sci-Fi", "Adventure"],
                "language": "English",
                "release_date": timezone.now().date() - datetime.timedelta(days=10),
                "director": "The Russo Brothers",
                "cast": ["Robert Downey Jr.", "Chris Evans", "Scarlett Johansson"],
                "certification": Movie.CERT_UA,
                "rating": 8.9,
                "votes_count": 4820,
                "trailer_url": "https://www.youtube.com/watch?v=TcMBFSGVi1c",
                "status": Movie.STATUS_NOW_SHOWING,
                "is_featured": True
            },
            {
                "title": "Cyberpunk: Neon Horizon",
                "synopsis": "In a rain-drenched megacity controlled by mega-corporations, an augmented rogue agent uncovers a neural virus capable of enslaving human consciousness.",
                "duration": 138,
                "genres": ["Sci-Fi", "Action", "Thriller"],
                "language": "English",
                "release_date": timezone.now().date() - datetime.timedelta(days=5),
                "director": "Denis Villeneuve",
                "cast": ["Ryan Reynolds", "Zendaya", "Cillian Murphy"],
                "certification": Movie.CERT_A,
                "rating": 8.5,
                "votes_count": 3100,
                "trailer_url": "https://www.youtube.com/watch?v=d9MyW72ELq0",
                "status": Movie.STATUS_NOW_SHOWING,
                "is_featured": True
            },
            {
                "title": "Laughter Therapy: Vacation Chaos",
                "synopsis": "A group of mismatched coworkers book what they thought was a luxury corporate retreat, only to find themselves stranded on an island run by eccentric locals.",
                "duration": 112,
                "genres": ["Comedy", "Romance"],
                "language": "Hindi",
                "release_date": timezone.now().date() - datetime.timedelta(days=8),
                "director": "Taika Waititi",
                "cast": ["Ryan Reynolds", "Emma Stone"],
                "certification": Movie.CERT_U,
                "rating": 7.6,
                "votes_count": 1850,
                "trailer_url": "https://www.youtube.com/watch?v=f_vWzO1p28A",
                "status": Movie.STATUS_NOW_SHOWING,
                "is_featured": False
            },
            {
                "title": "Shadows in the Mist",
                "synopsis": "A team of folklore researchers enter an isolated Victorian manor enveloped by an eternal mist, only to awaken spirits that feast on suppressed guilt.",
                "duration": 105,
                "genres": ["Horror", "Thriller"],
                "language": "English",
                "release_date": timezone.now().date() - datetime.timedelta(days=12),
                "director": "James Wan",
                "cast": ["Scarlett Johansson", "Cillian Murphy"],
                "certification": Movie.CERT_A,
                "rating": 7.4,
                "votes_count": 1290,
                "trailer_url": "https://www.youtube.com/watch?v=k10ETZ41q5o",
                "status": Movie.STATUS_NOW_SHOWING,
                "is_featured": False
            },
            {
                "title": "Heartstrings & Horizons",
                "synopsis": "Two jazz musicians meet on a rainy night in Paris, inspiring each other to pursue their artistic dreams while wrestling with the sacrifices of love.",
                "duration": 128,
                "genres": ["Romance", "Drama"],
                "language": "English",
                "release_date": timezone.now().date() - datetime.timedelta(days=15),
                "director": "Damien Chazelle",
                "cast": ["Emma Stone", "Ryan Reynolds"],
                "certification": Movie.CERT_UA,
                "rating": 8.3,
                "votes_count": 2400,
                "trailer_url": "https://www.youtube.com/watch?v=0pdqf4P9MB8",
                "status": Movie.STATUS_NOW_SHOWING,
                "is_featured": True
            },
            {
                "title": "Chronicles of Starlight",
                "synopsis": "A young celestial explorer and her robotic companion embark on an intergalactic voyage across nebulae to reignite the fading Heart Star of the galaxy.",
                "duration": 98,
                "genres": ["Animation", "Adventure", "Sci-Fi"],
                "language": "English",
                "release_date": timezone.now().date() - datetime.timedelta(days=3),
                "director": "Pete Docter",
                "cast": ["Zendaya", "Robert Downey Jr."],
                "certification": Movie.CERT_U,
                "rating": 8.8,
                "votes_count": 3950,
                "trailer_url": "https://www.youtube.com/watch?v=1g3_CFmnU7k",
                "status": Movie.STATUS_NOW_SHOWING,
                "is_featured": True
            },
            {
                "title": "The Martian Genesis",
                "synopsis": "Colony Omega discovers an alien artifact beneath the red sands of Mars that challenges humanity's origin story.",
                "duration": 145,
                "genres": ["Sci-Fi", "Drama"],
                "language": "English",
                "release_date": timezone.now().date() + datetime.timedelta(days=14),
                "director": "Christopher Nolan",
                "cast": ["Cillian Murphy", "Leonardo DiCaprio"],
                "certification": Movie.CERT_UA,
                "rating": 9.2,
                "votes_count": 150,
                "trailer_url": "https://www.youtube.com/watch?v=zSWdZVtXT7E",
                "status": Movie.STATUS_COMING_SOON,
                "is_featured": True
            },
            {
                "title": "Spies in Venice",
                "synopsis": "An undercover intelligence agent must safeguard a billionaire art collector in Venice while navigating romantic tension and rival assassins.",
                "duration": 120,
                "genres": ["Action", "Comedy", "Thriller"],
                "language": "English",
                "release_date": timezone.now().date() + datetime.timedelta(days=21),
                "director": "Matthew Vaughn",
                "cast": ["Chris Evans", "Margot Robbie"],
                "certification": Movie.CERT_UA,
                "rating": 8.0,
                "votes_count": 80,
                "trailer_url": "https://www.youtube.com/watch?v=TcMBFSGVi1c",
                "status": Movie.STATUS_COMING_SOON,
                "is_featured": False
            }
        ]

        poster_map = {
            "Avengers: Quantum Odyssey": "posters/avengers-quantum-odyssey.jpg",
            "Cyberpunk: Neon Horizon": "posters/cyberpunk-neon-horizon.jpg",
            "Chronicles of Starlight": "posters/chronicles-of-starlight.jpg",
            "Heartstrings & Horizons": "posters/heartstrings-and-horizons.jpg",
            "Shadows in the Mist": "posters/shadows-in-the-mist.jpg",
            "Laughter Therapy: Vacation Chaos": "posters/laughter-therapy-vacation-chaos.jpg",
            "The Martian Genesis": "posters/the-martian-genesis.jpg",
            "Spies in Venice": "posters/spies-in-venice.jpg",
        }

        created_movies = []
        for m_data in movies_info:
            p_val = poster_map.get(m_data["title"])
            movie, created = Movie.objects.get_or_create(
                title=m_data["title"],
                defaults={
                    "synopsis": m_data["synopsis"],
                    "duration": m_data["duration"],
                    "language": m_data["language"],
                    "release_date": m_data["release_date"],
                    "director": m_data["director"],
                    "certification": m_data["certification"],
                    "rating": m_data["rating"],
                    "votes_count": m_data["votes_count"],
                    "trailer_url": m_data["trailer_url"],
                    "status": m_data["status"],
                    "is_featured": m_data["is_featured"],
                    "poster": p_val,
                }
            )
            if not movie.poster and p_val:
                movie.poster = p_val
            for g_name in m_data["genres"]:
                movie.genres.add(genres[g_name])
            for act_name in m_data["cast"]:
                movie.cast.add(actors[act_name])
            movie.save()
            created_movies.append(movie)

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_movies)} Movies created"))

        # 5. Create Cinemas
        cinemas_data = [
            {
                "name": "CineReserve IMAX Grand",
                "address": "Linking Road, Bandra West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400050",
                "contact_number": "+91 22 2640 1122",
                "email": "bandra@cinereserve.com",
                "manager": manager_user,
                "facilities": "IMAX with Laser, Dolby Atmos, Luxury Recliners, Gourmet Food Court, Valet Parking, Wheelchair Access"
            },
            {
                "name": "PVR Phoenix Palladium",
                "address": "High Street Phoenix, 462 Senapati Bapat Marg, Lower Parel",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400013",
                "contact_number": "+91 22 4333 9999",
                "email": "palladium@cinereserve.com",
                "manager": manager_user,
                "facilities": "4DX Motion, Dolby 7.1, Premium Lounges, Food Court, Parking, Wheelchair Access"
            },
            {
                "name": "INOX Megaplex Inorbit",
                "address": "Inorbit Mall, Link Road, Malad West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400064",
                "contact_number": "+91 22 6677 8899",
                "email": "inorbit@cinereserve.com",
                "manager": None,
                "facilities": "Dolby Atmos, Digital 3D, Gourmet Bites, Multi-level Parking, Wheelchair Access"
            }
        ]

        created_cinemas = []
        for c_data in cinemas_data:
            cin, _ = Cinema.objects.get_or_create(
                name=c_data["name"],
                defaults={
                    "address": c_data["address"],
                    "city": c_data["city"],
                    "state": c_data["state"],
                    "postal_code": c_data["postal_code"],
                    "contact_number": c_data["contact_number"],
                    "email": c_data["email"],
                    "manager": c_data["manager"],
                    "facilities": c_data["facilities"],
                }
            )
            created_cinemas.append(cin)

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_cinemas)} Cinemas created"))

        # 6. Create Screens and Seats for each cinema
        screen_templates = [
            ("Audi 1 - IMAX Laser", Screen.TYPE_IMAX, 7, 10), # 70 seats (Rows A to G, 1 to 10)
            ("Audi 2 - Dolby Atmos 3D", Screen.TYPE_3D, 6, 10), # 60 seats (Rows A to F, 1 to 10)
            ("Audi 3 - Classic 2D", Screen.TYPE_2D, 6, 10),     # 60 seats (Rows A to F, 1 to 10)
        ]

        created_screens = []
        for cinema in created_cinemas:
            for s_name, s_type, rows, cols in screen_templates:
                screen, s_created = Screen.objects.get_or_create(
                    cinema=cinema,
                    name=s_name,
                    defaults={
                        'screen_type': s_type,
                        'total_rows': rows,
                        'seats_per_row': cols,
                        'total_capacity': rows * cols
                    }
                )
                created_screens.append(screen)

                # Generate seats if screen is freshly created
                if s_created:
                    row_letters = ["A", "B", "C", "D", "E", "F", "G"][:rows]
                    seats_to_create = []
                    for row_idx, r_letter in enumerate(row_letters):
                        # Designate tiers:
                        # Front rows A, B: Regular (1.0x)
                        # Middle rows C, D: Premium (1.25x)
                        # Back rows E, F: VIP (1.5x)
                        # Last row G (if exists): Luxury Recliner (2.0x)
                        if r_letter == "G":
                            tier = Seat.TYPE_RECLINER
                            multiplier = 2.00
                        elif r_letter in ["E", "F"]:
                            tier = Seat.TYPE_VIP
                            multiplier = 1.50
                        elif r_letter in ["C", "D"]:
                            tier = Seat.TYPE_PREMIUM
                            multiplier = 1.25
                        else:
                            tier = Seat.TYPE_REGULAR
                            multiplier = 1.00

                        for num in range(1, cols + 1):
                            seats_to_create.append(
                                Seat(
                                    screen=screen,
                                    row=r_letter,
                                    number=num,
                                    seat_type=tier,
                                    price_multiplier=multiplier
                                )
                            )
                    Seat.objects.bulk_create(seats_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_screens)} Screens and ~600 Seats created across 3 cinemas"))

        # 7. Create Shows for Today, Tomorrow, and Next 3 Days
        now_movies = [m for m in created_movies if m.status == Movie.STATUS_NOW_SHOWING]
        today = timezone.now().date()
        show_times = [
            (datetime.time(10, 0), datetime.time(12, 45)),
            (datetime.time(13, 30), datetime.time(16, 15)),
            (datetime.time(17, 0), datetime.time(19, 45)),
            (datetime.time(20, 30), datetime.time(23, 15)),
        ]

        shows_count = 0
        for day_offset in range(4):
            show_date = today + datetime.timedelta(days=day_offset)
            for idx, screen in enumerate(created_screens):
                # Pick a movie deterministically based on screen index & day offset
                movie = now_movies[(idx + day_offset) % len(now_movies)]
                base_price = Decimal('350.00') if screen.screen_type == Screen.TYPE_IMAX else Decimal('260.00')

                for st_time, end_time in show_times:
                    show, created = Show.objects.get_or_create(
                        movie=movie,
                        screen=screen,
                        date=show_date,
                        start_time=st_time,
                        defaults={
                            'end_time': end_time,
                            'format': screen.screen_type,
                            'language': movie.language,
                            'base_price': base_price,
                        }
                    )
                    if created:
                        shows_count += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] {shows_count} Shows scheduled with automated ShowSeat generation"))

        # 8. Create Discount Coupons
        coupons = [
            ("WELCOME100", Coupon.TYPE_FLAT, 100.00, 300.00, None),
            ("MOVIE50", Coupon.TYPE_FLAT, 50.00, 200.00, None),
            ("CINEPROMO20", Coupon.TYPE_PERCENTAGE, 20.00, 400.00, 150.00),
            ("FIRSTBOOKING", Coupon.TYPE_FLAT, 75.00, 250.00, None),
        ]
        for code, dtype, val, min_amt, max_disc in coupons:
            Coupon.objects.get_or_create(
                code=code,
                defaults={
                    'discount_type': dtype,
                    'discount_value': val,
                    'min_amount': min_amt,
                    'max_discount': max_disc,
                    'valid_until': timezone.now() + datetime.timedelta(days=60),
                    'usage_limit': 500,
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] Promotional Coupons created (WELCOME100, MOVIE50, CINEPROMO20, FIRSTBOOKING)"))

        # 9. Create Sample Reviews
        sample_reviews = [
            (customer1, created_movies[0], 5, "Unbelievable cinematic masterpiece!", "The visual effects in IMAX are completely otherworldly. Must watch on the big screen!"),
            (customer2, created_movies[0], 5, "Mind-blowing spectacle", "The quantum realm sequences set a new benchmark for CGI storytelling."),
            (customer1, created_movies[1], 4, "Brilliant cyberpunk neo-noir", "Great synth soundtrack and Villeneuve's direction is impeccable."),
            (customer2, created_movies[4], 5, "Pure romantic magic", "Emma Stone and Ryan Reynolds have electrifying chemistry. Tears in the end."),
        ]
        for u, m, r, head, cmt in sample_reviews:
            Review.objects.get_or_create(
                user=u,
                movie=m,
                defaults={
                    'rating': r,
                    'headline': head,
                    'comment': cmt,
                    'is_verified_buyer': True
                }
            )

        # 10. Create Sample Wishlist & Demo Bookings
        if created_movies:
            Wishlist.objects.get_or_create(user=customer1, movie=created_movies[0])
            Wishlist.objects.get_or_create(user=customer1, movie=created_movies[1])
            Wishlist.objects.get_or_create(user=customer2, movie=created_movies[2])

        if hasattr(customer1, 'profile'):
            customer1.profile.favorite_genre = "Action"
            customer1.profile.loyalty_points = 85
            customer1.profile.save()

        if hasattr(customer2, 'profile'):
            customer2.profile.favorite_genre = "Sci-Fi"
            customer2.profile.loyalty_points = 40
            customer2.profile.save()

        if Booking.objects.count() == 0:
            today_date = timezone.now().date()
            sample_show = Show.objects.filter(date__gte=today_date, is_active=True).first()
            if sample_show:
                seats_to_book = list(sample_show.show_seats.filter(status=ShowSeat.STATUS_AVAILABLE)[:2])
                if len(seats_to_book) == 2:
                    t_total = sum(s.price for s in seats_to_book)
                    conv = Decimal('30.00')
                    tax = round((t_total + conv) * Decimal('0.18'), 2)
                    f_amt = t_total + conv + tax

                    b = Booking.objects.create(
                        user=customer1,
                        show=sample_show,
                        total_ticket_price=t_total,
                        convenience_fee=conv,
                        tax_amount=tax,
                        discount_amount=Decimal('0.00'),
                        final_amount=f_amt,
                        booking_status=Booking.STATUS_CONFIRMED
                    )
                    for s in seats_to_book:
                        BookingSeat.objects.create(booking=b, show_seat=s, seat_price=s.price)
                        s.status = ShowSeat.STATUS_BOOKED
                        s.save(update_fields=['status'])
                    Payment.objects.create(
                        booking=b,
                        payment_method=Payment.METHOD_UPI,
                        amount=f_amt,
                        status=Payment.STATUS_SUCCESS
                    )
                    Ticket.objects.create(booking=b)

        self.stdout.write(self.style.SUCCESS("[OK] Demo bookings, wishlists, and user profiles configured"))
        self.stdout.write(self.style.SUCCESS("\n======================================================="))
        self.stdout.write(self.style.SUCCESS("DATABASE SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("======================================================="))
