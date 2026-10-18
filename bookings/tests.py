from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from movies.models import Genre, Movie
from cinemas.models import Cinema, Screen, Seat
from shows.models import Show, ShowSeat
from bookings.models import Coupon, Booking, Refund
from payments.models import Payment

User = get_user_model()


def build_show_fixture():
    genre = Genre.objects.create(name='Action')
    movie = Movie.objects.create(
        title='Test Odyssey',
        synopsis='A test film.',
        duration=120,
        language='English',
        release_date=date.today(),
        director='Test Director',
        status=Movie.STATUS_NOW_SHOWING,
        rating=8.0,
    )
    movie.genres.add(genre)
    cinema = Cinema.objects.create(
        name='Testplex',
        address='1 Test Street',
        city='Mumbai',
        contact_number='9999999999',
    )
    screen = Screen.objects.create(cinema=cinema, name='Audi 1', total_rows=2, seats_per_row=4)
    for row in ['A', 'B']:
        for num in range(1, 5):
            Seat.objects.create(screen=screen, row=row, number=num)
    tomorrow = date.today() + timedelta(days=2)
    show = Show.objects.create(
        movie=movie,
        screen=screen,
        date=tomorrow,
        start_time=time(18, 0),
        end_time=time(20, 15),
        base_price=Decimal('200.00'),
    )
    return movie, show


class AccountsTests(TestCase):
    def test_registration_and_login(self):
        resp = self.client.post(reverse('accounts:register'), {
            'first_name': 'Aarav',
            'last_name': 'Patel',
            'username': 'aaravtest',
            'email': 'aarav@example.com',
            'phone_number': '9876543210',
            'password': 'StrongPass1',
            'confirm_password': 'StrongPass1',
            'agree_terms': True,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='aaravtest').exists())
        user = User.objects.get(username='aaravtest')
        self.assertTrue(user.check_password('StrongPass1'))
        login_resp = self.client.post(reverse('accounts:login'), {
            'login_id': 'aaravtest',
            'password': 'StrongPass1',
        })
        self.assertEqual(login_resp.status_code, 302)

    def test_invalid_login(self):
        resp = self.client.post(reverse('accounts:login'), {
            'login_id': 'nobody',
            'password': 'wrong',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid')


class MovieSearchTests(TestCase):
    def setUp(self):
        Movie.objects.create(
            title='Quantum Odyssey',
            synopsis='Heroes assemble.',
            duration=150,
            language='English',
            release_date=date.today(),
            director='Russo',
            status=Movie.STATUS_NOW_SHOWING,
        )

    def test_movie_search(self):
        resp = self.client.get(reverse('movies:movie_list'), {'q': 'Quantum'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Quantum Odyssey')


class SeatLockingTests(TestCase):
    def setUp(self):
        self.movie, self.show = build_show_fixture()
        self.user1 = User.objects.create_user(username='u1', password='Pass12345', email='u1@x.com')
        self.user2 = User.objects.create_user(username='u2', password='Pass12345', email='u2@x.com')
        self.seat = ShowSeat.objects.filter(show=self.show).first()

    def test_lock_and_prevent_double_booking(self):
        self.client.login(username='u1', password='Pass12345')
        resp = self.client.post(
            reverse('shows:lock_seats_api'),
            data={'show_id': self.show.id, 'seat_ids': [self.seat.id]},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.seat.refresh_from_db()
        self.assertEqual(self.seat.status, ShowSeat.STATUS_LOCKED)

        other = Client()
        other.login(username='u2', password='Pass12345')
        resp2 = other.post(
            reverse('shows:lock_seats_api'),
            data={'show_id': self.show.id, 'seat_ids': [self.seat.id]},
            content_type='application/json',
        )
        self.assertEqual(resp2.status_code, 409)


class BookingPaymentTests(TestCase):
    def setUp(self):
        self.movie, self.show = build_show_fixture()
        self.user = User.objects.create_user(
            username='buyer', password='Pass12345', email='buyer@x.com', first_name='Buyer'
        )
        self.seats = list(ShowSeat.objects.filter(show=self.show)[:2])
        Coupon.objects.create(
            code='MOVIE50',
            discount_type=Coupon.TYPE_FLAT,
            discount_value=Decimal('50.00'),
            min_amount=Decimal('10.00'),
            valid_until=timezone.now() + timedelta(days=10),
            usage_limit=10,
        )

    def _lock(self):
        self.client.login(username='buyer', password='Pass12345')
        self.client.post(
            reverse('shows:lock_seats_api'),
            data={'show_id': self.show.id, 'seat_ids': [s.id for s in self.seats]},
            content_type='application/json',
        )

    def test_coupon_validation(self):
        coupon = Coupon.objects.get(code='MOVIE50')
        valid, _ = coupon.is_valid(Decimal('100.00'))
        self.assertTrue(valid)
        invalid, msg = coupon.is_valid(Decimal('5.00'))
        self.assertFalse(invalid)

    def test_payment_success_creates_booking(self):
        self._lock()
        resp = self.client.post(reverse('bookings:process_payment'), {
            'payment_action': 'SUCCESS',
            'payment_method': Payment.METHOD_UPI,
        })
        self.assertEqual(resp.status_code, 302)
        booking = Booking.objects.get(user=self.user)
        self.assertEqual(booking.booking_status, Booking.STATUS_CONFIRMED)
        self.assertTrue(hasattr(booking, 'ticket'))
        self.assertTrue(hasattr(booking, 'payment'))
        for s in self.seats:
            s.refresh_from_db()
            self.assertEqual(s.status, ShowSeat.STATUS_BOOKED)

    def test_payment_failure_releases_seats(self):
        self._lock()
        resp = self.client.post(reverse('bookings:process_payment'), {
            'payment_action': 'FAILED',
            'payment_method': Payment.METHOD_UPI,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Booking.objects.filter(user=self.user, booking_status=Booking.STATUS_CONFIRMED).exists())
        for s in self.seats:
            s.refresh_from_db()
            self.assertEqual(s.status, ShowSeat.STATUS_AVAILABLE)

    def test_cancellation_refund(self):
        self._lock()
        self.client.post(reverse('bookings:process_payment'), {
            'payment_action': 'SUCCESS',
            'payment_method': Payment.METHOD_UPI,
        })
        booking = Booking.objects.get(user=self.user)
        self.assertEqual(booking.refund_percentage_eligibility(), 100)
        resp = self.client.post(reverse('bookings:cancel_booking', args=[booking.booking_id]), {'reason': 'Plans changed'})
        self.assertEqual(resp.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, Booking.STATUS_CANCELLED)
        self.assertTrue(Refund.objects.filter(booking=booking, refund_percentage=100).exists())


class AdminAuthzTests(TestCase):
    def test_customer_cannot_open_admin_dashboard(self):
        User.objects.create_user(username='cust', password='Pass12345', role=User.ROLE_CUSTOMER)
        self.client.login(username='cust', password='Pass12345')
        resp = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(resp.status_code, 403)
