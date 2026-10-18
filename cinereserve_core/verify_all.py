import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinereserve_core.settings')
import django
django.setup()

from django.test import Client
from accounts.models import User
from movies.models import Movie
from shows.models import Show

def test_endpoints():
    c = Client()
    print("Testing Guest Public Views...")
    public_urls = [
        '/',
        '/movies/',
        '/cinemas/',
        '/recommendations/',
        '/bookings/offers/',
        '/bookings/faq/',
        '/bookings/terms/',
        '/bookings/refund-policy/',
        '/bookings/about/',
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/forgot-password/',
        '/api/movies/',
        '/api/cinemas/',
        '/api/shows/',
        '/api/coupons/',
    ]
    for url in public_urls:
        resp = c.get(url)
        assert resp.status_code == 200, f"Expected 200 for {url}, got {resp.status_code}"
    print(f"  All {len(public_urls)} public endpoints returned 200 OK.")

    # Movie detail view
    movie = Movie.objects.first()
    if movie:
        detail_url = f"/movies/{movie.slug}/"
        resp = c.get(detail_url)
        assert resp.status_code == 200, f"Expected 200 for {detail_url}, got {resp.status_code}"
        print(f"  Movie detail ({detail_url}) returned 200 OK.")

    # Show seat layout view
    show = Show.objects.first()
    if show:
        seat_url = f"/shows/{show.id}/seats/"
        resp = c.get(seat_url)
        assert resp.status_code == 200, f"Expected 200 for {seat_url}, got {resp.status_code}"
        print(f"  Seat layout ({seat_url}) returned 200 OK.")

    # Test Customer Views
    print("\nTesting Customer Views (customer1)...")
    logged_in = c.login(username='customer1', password='Customer@1234')
    assert logged_in, "Failed to login as customer1"

    customer_urls = [
        '/accounts/profile/',
        '/accounts/notifications/',
        '/bookings/my-bookings/',
        '/movies/wishlist/',
        '/recommendations/',
    ]
    for url in customer_urls:
        resp = c.get(url)
        assert resp.status_code == 200, f"Expected 200 for {url}, got {resp.status_code}"
        print(f"  Customer view {url} returned 200 OK.")

    # Test Chatbot API
    chat_resp = c.post(
        '/chatbot/api/message/',
        data=json.dumps({'message': 'recommend a movie'}),
        content_type='application/json'
    )
    assert chat_resp.status_code == 200, f"Chatbot returned {chat_resp.status_code}"
    chat_data = chat_resp.json()
    assert chat_data.get('success'), "Chatbot response success was False"
    print(f"  Chatbot API returned 200 OK: '{chat_data.get('reply')[:55]}...'")

    # Test Admin Dashboard
    print("\nTesting Admin Dashboard (admin)...")
    c.login(username='admin', password='Admin@1234')
    resp = c.get('/dashboard/admin/')
    assert resp.status_code == 200, f"Expected 200 for /dashboard/admin/, got {resp.status_code}"
    print("  Admin dashboard returned 200 OK.")

    # Test Manager Dashboard
    print("\nTesting Cinema Manager Dashboard (manager_pvr)...")
    c.login(username='manager_pvr', password='Manager@1234')
    resp = c.get('/dashboard/manager/')
    assert resp.status_code == 200, f"Expected 200 for /dashboard/manager/, got {resp.status_code}"
    print("  Manager dashboard returned 200 OK.")

    # Test Complete Booking Lifecycle
    print("\nTesting Complete Booking Lifecycle...")
    c.login(username='customer1', password='Customer@1234')
    from django.urls import reverse
    from shows.models import ShowSeat
    from bookings.models import Booking

    active_show = Show.objects.filter(is_active=True).first()
    avail_seats = list(active_show.show_seats.filter(status=ShowSeat.STATUS_AVAILABLE)[:1])
    if avail_seats:
        s_id = avail_seats[0].id
        lock_res = c.post(
            reverse('shows:lock_seats_api'),
            data=json.dumps({'show_id': active_show.id, 'seat_ids': [s_id]}),
            content_type='application/json'
        )
        assert lock_res.status_code == 200, f"Lock seats failed: {lock_res.content}"
        print("  Seats locked successfully (5-min lock).")

        summary_res = c.get(reverse('bookings:booking_summary'))
        assert summary_res.status_code == 200, "Booking summary failed"

        pay_proc_res = c.post(
            reverse('bookings:process_payment'),
            data={'payment_method': 'UPI', 'payment_action': 'SUCCESS'},
            follow=True
        )
        assert pay_proc_res.status_code == 200, "Payment processing failed"
        print("  Payment processed and booking created.")

        latest_booking = Booking.objects.filter(user__username='customer1').order_by('-created_at').first()
        assert latest_booking and hasattr(latest_booking, 'ticket'), "Ticket not created for booking"

        pdf_res = c.get(reverse('bookings:download_ticket_pdf', kwargs={'booking_id': latest_booking.booking_id}))
        assert pdf_res.status_code == 200, "PDF ticket download failed"
        assert pdf_res['Content-Type'] == 'application/pdf', "PDF content type incorrect"
        assert len(pdf_res.content) > 1000, "PDF content too small"
        print(f"  PDF E-Ticket generated & downloaded successfully ({len(pdf_res.content)} bytes).")

    print("\n==========================================")
    print("ALL ENDPOINT & LIFECYCLE VERIFICATIONS PASSED 100%!")
    print("==========================================")

if __name__ == '__main__':
    test_endpoints()
