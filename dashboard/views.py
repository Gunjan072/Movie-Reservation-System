from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, date
import json

from accounts.models import User
from movies.models import Movie
from cinemas.models import Cinema, Screen
from shows.models import Show, ShowSeat
from bookings.models import Booking, Refund
from payments.models import Payment
from reviews.models import Review
from chatbot.models import ChatMessage


# ─────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────

@login_required
def admin_dashboard_view(request):
    if not request.user.is_admin_user:
        raise PermissionDenied

    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    last_30 = today - timedelta(days=30)

    # ── Key Metrics ──────────────────────────────────────────
    total_users    = User.objects.filter(role=User.ROLE_CUSTOMER).count()
    new_users_month = User.objects.filter(
        role=User.ROLE_CUSTOMER,
        date_joined__date__gte=start_of_month
    ).count()

    total_bookings    = Booking.objects.filter(booking_status=Booking.STATUS_CONFIRMED).count()
    bookings_today    = Booking.objects.filter(
        booking_status=Booking.STATUS_CONFIRMED,
        created_at__date=today
    ).count()

    total_revenue = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS
    ).aggregate(total=Sum('amount'))['total'] or 0

    revenue_today = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS,
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    revenue_month = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS,
        created_at__date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_movies  = Movie.objects.count()
    now_showing   = Movie.objects.filter(status=Movie.STATUS_NOW_SHOWING).count()
    total_cinemas = Cinema.objects.filter(is_active=True).count()
    avg_rating    = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    total_reviews = Review.objects.count()

    # ── Revenue last 14 days (chart) ─────────────────────────
    revenue_days = []
    revenue_vals = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        amt = Payment.objects.filter(
            status=Payment.STATUS_SUCCESS,
            created_at__date=d
        ).aggregate(total=Sum('amount'))['total'] or 0
        revenue_days.append(d.strftime('%d %b'))
        revenue_vals.append(float(amt))

    # ── Bookings last 14 days (chart) ────────────────────────
    bookings_days = []
    bookings_vals = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        cnt = Booking.objects.filter(
            booking_status=Booking.STATUS_CONFIRMED,
            created_at__date=d
        ).count()
        bookings_days.append(d.strftime('%d %b'))
        bookings_vals.append(cnt)

    # ── Top movies by bookings ────────────────────────────────
    top_movies = (
        Movie.objects
        .annotate(
            total_bookings=Count(
                'shows__bookings',
                filter=Q(shows__bookings__booking_status=Booking.STATUS_CONFIRMED),
                distinct=True
            )
        )
        .order_by('-total_bookings')[:8]
    )

    # ── Genre distribution ────────────────────────────────────
    from movies.models import Genre
    genre_data = []
    for genre in Genre.objects.all():
        cnt = Movie.objects.filter(genres=genre, status=Movie.STATUS_NOW_SHOWING).count()
        if cnt:
            genre_data.append({'name': genre.name, 'count': cnt})
    genre_data.sort(key=lambda x: x['count'], reverse=True)

    # ── Recent bookings ───────────────────────────────────────
    recent_bookings = (
        Booking.objects
        .select_related('user', 'show__movie', 'show__screen__cinema')
        .filter(booking_status=Booking.STATUS_CONFIRMED)
        .order_by('-created_at')[:10]
    )

    # ── Recent refunds ────────────────────────────────────────
    recent_refunds = (
        Refund.objects
        .select_related('booking__user', 'booking__show__movie')
        .order_by('-processed_at')[:5]
    )

    # ── User roles breakdown ──────────────────────────────────
    customers = User.objects.filter(role=User.ROLE_CUSTOMER).count()
    managers  = User.objects.filter(role=User.ROLE_CINEMA_MANAGER).count()
    admins    = User.objects.filter(Q(role=User.ROLE_ADMIN) | Q(is_superuser=True)).count()

    # ── Chatbot intents breakdown ─────────────────────────────
    chatbot_intents = list(
        ChatMessage.objects
        .values('intent')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    for ci in chatbot_intents:
        ci['label'] = ci['intent'].replace('_', ' ').title()

    total_show_seats = ShowSeat.objects.filter(show__date=today).count()
    booked_show_seats = ShowSeat.objects.filter(show__date=today, status=ShowSeat.STATUS_BOOKED).count()
    occupancy_rate = round((booked_show_seats / total_show_seats) * 100, 1) if total_show_seats else 0

    context = {
        # Metrics
        'total_users': total_users,
        'new_users_month': new_users_month,
        'total_bookings': total_bookings,
        'bookings_today': bookings_today,
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'revenue_month': revenue_month,
        'total_movies': total_movies,
        'now_showing': now_showing,
        'total_cinemas': total_cinemas,
        'avg_rating': round(float(avg_rating), 1),
        'total_reviews': total_reviews,
        'occupancy_rate': occupancy_rate,
        # Charts (serialized for Chart.js)
        'revenue_days_json': json.dumps(revenue_days),
        'revenue_vals_json': json.dumps(revenue_vals),
        'bookings_days_json': json.dumps(bookings_days),
        'bookings_vals_json': json.dumps(bookings_vals),
        'genre_labels_json': json.dumps([g['name'] for g in genre_data]),
        'genre_counts_json': json.dumps([g['count'] for g in genre_data]),
        'user_roles_json': json.dumps([customers, managers, admins]),
        # Lists
        'top_movies': top_movies,
        'recent_bookings': recent_bookings,
        'recent_refunds': recent_refunds,
        'chatbot_intents': chatbot_intents,
        # Users panel
        'customers': customers,
        'managers': managers,
        'admins': admins,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


# ─────────────────────────────────────────────────────────────
# CINEMA MANAGER DASHBOARD
# ─────────────────────────────────────────────────────────────

@login_required
def manager_dashboard_view(request):
    if not (request.user.role == User.ROLE_CINEMA_MANAGER or request.user.is_admin_user):
        raise PermissionDenied

    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    if request.user.is_cinema_manager and not request.user.is_admin_user:
        cinemas = Cinema.objects.filter(is_active=True, manager=request.user)
    else:
        cinemas = Cinema.objects.filter(is_active=True)

    # ── Today's shows ─────────────────────────────────────────
    todays_shows = (
        Show.objects
        .filter(date=today, is_active=True, screen__cinema__in=cinemas)
        .select_related('movie', 'screen__cinema')
        .order_by('start_time')
    )

    # ── Show occupancy stats ──────────────────────────────────
    shows_with_stats = []
    for show in todays_shows:
        total_seats  = show.show_seats.count()
        booked_seats = show.show_seats.filter(status=ShowSeat.STATUS_BOOKED).count()
        locked_seats = show.show_seats.filter(
            status=ShowSeat.STATUS_LOCKED,
            locked_until__gte=timezone.now()
        ).count()
        occupancy = round((booked_seats / total_seats * 100), 1) if total_seats else 0
        shows_with_stats.append({
            'show': show,
            'total': total_seats,
            'booked': booked_seats,
            'locked': locked_seats,
            'available': total_seats - booked_seats - locked_seats,
            'occupancy': occupancy,
        })

    # ── Revenue this month per cinema ────────────────────────
    cinema_revenue = []
    for cinema in cinemas:
        rev = Payment.objects.filter(
            status=Payment.STATUS_SUCCESS,
            booking__show__screen__cinema=cinema,
            created_at__date__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        bkgs = Booking.objects.filter(
            booking_status=Booking.STATUS_CONFIRMED,
            show__screen__cinema=cinema,
            created_at__date__gte=start_of_month
        ).count()
        cinema_revenue.append({
            'cinema': cinema,
            'revenue': float(rev),
            'bookings': bkgs,
        })

    movie_filter = (
        Q(shows__screen__cinema=cinema, shows__bookings__booking_status=Booking.STATUS_CONFIRMED)
        if cinema else
        Q(shows__bookings__booking_status=Booking.STATUS_CONFIRMED)
    )
    movie_stats = (
        Movie.objects
        .filter(status=Movie.STATUS_NOW_SHOWING)
        .annotate(
            booking_count=Count(
                'shows__bookings',
                filter=movie_filter,
                distinct=True
            )
        )
        .order_by('-booking_count')[:6]
    )

    # ── Revenue last 7 days (chart) ───────────────────────────
    rev_labels, rev_values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        amt = Payment.objects.filter(
            status=Payment.STATUS_SUCCESS,
            created_at__date=d
        ).aggregate(total=Sum('amount'))['total'] or 0
        rev_labels.append(d.strftime('%a, %d %b'))
        rev_values.append(float(amt))

    # ── Recent bookings for manager's cinemas ─────────────────
    recent_bookings = (
        Booking.objects
        .filter(booking_status=Booking.STATUS_CONFIRMED, show__screen__cinema__in=cinemas)
        .select_related('user', 'show__movie', 'show__screen__cinema')
        .order_by('-created_at')[:8]
    )

    # ── Low-capacity alert shows ──────────────────────────────
    low_fill_shows = [s for s in shows_with_stats if s['occupancy'] < 30]
    high_fill_shows = [s for s in shows_with_stats if s['occupancy'] >= 80]

    context = {
        'cinemas': cinemas,
        'todays_shows': todays_shows,
        'shows_with_stats': shows_with_stats,
        'cinema_revenue': cinema_revenue,
        'movie_stats': movie_stats,
        'recent_bookings': recent_bookings,
        'low_fill_shows': low_fill_shows,
        'high_fill_shows': high_fill_shows,
        # Charts
        'rev_labels_json': json.dumps(rev_labels),
        'rev_values_json': json.dumps(rev_values),
        # Summary
        'total_shows_today': len(shows_with_stats),
        'avg_occupancy': round(
            sum(s['occupancy'] for s in shows_with_stats) / len(shows_with_stats), 1
        ) if shows_with_stats else 0,
    }
    return render(request, 'dashboard/manager_dashboard.html', context)
