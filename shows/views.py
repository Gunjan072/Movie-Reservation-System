import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.urls import reverse
from .models import Show, ShowSeat


def seat_layout_view(request, show_id):
    show = get_object_or_404(
        Show.objects.select_related('movie', 'screen__cinema'),
        id=show_id,
        is_active=True
    )
    now = timezone.now()

    # Auto-release expired locks for this show
    ShowSeat.objects.filter(
        show=show,
        status=ShowSeat.STATUS_LOCKED,
        locked_until__lte=now
    ).update(status=ShowSeat.STATUS_AVAILABLE, locked_by=None, locked_until=None)

    # Fetch all seats ordered by row and number
    show_seats = show.show_seats.select_related('seat').order_by('seat__row', 'seat__number')

    # Group seats by row
    rows_dict = {}
    for ss in show_seats:
        row_letter = ss.seat.row
        if row_letter not in rows_dict:
            rows_dict[row_letter] = []
        
        # Determine effective status for display
        status = ss.status
        is_user_locked = False
        if ss.status == ShowSeat.STATUS_LOCKED:
            if ss.locked_by == request.user and ss.locked_until and ss.locked_until > now:
                status = 'SELECTED'
                is_user_locked = True
            elif ss.locked_until and ss.locked_until <= now:
                status = ShowSeat.STATUS_AVAILABLE
            else:
                status = 'LOCKED'

        rows_dict[row_letter].append({
            'show_seat_id': ss.id,
            'seat_id': ss.seat.id,
            'seat_label': ss.seat.label,
            'row': ss.seat.row,
            'number': ss.seat.number,
            'tier': ss.seat.seat_type,
            'tier_display': ss.seat.get_seat_type_display(),
            'price': float(ss.price),
            'status': status,
            'is_user_locked': is_user_locked,
        })

    # Unique seat tiers present in this auditorium for legend
    seat_tiers = []
    seen_tiers = set()
    for ss in show_seats:
        t = ss.seat.seat_type
        if t not in seen_tiers:
            seen_tiers.add(t)
            seat_tiers.append({
                'type': t,
                'name': ss.seat.get_seat_type_display(),
                'price': float(ss.price),
            })

    context = {
        'show': show,
        'rows_dict': rows_dict,
        'seat_tiers': seat_tiers,
    }
    return render(request, 'shows/seat_layout.html', context)


def lock_seats_api(request):
    """
    Real-world concurrency protection using select_for_update() and transaction.atomic().
    Locks the selected seats for 5 minutes (300 seconds).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Please log in to reserve seats.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        show_id = data.get('show_id')
        seat_ids = data.get('seat_ids', [])

        if not show_id or not seat_ids:
            return JsonResponse({'success': False, 'error': 'Please select at least one seat.'}, status=400)

        if len(seat_ids) > 10:
            return JsonResponse({'success': False, 'error': 'You can select a maximum of 10 seats per booking.'}, status=400)

        now = timezone.now()
        lock_duration = timedelta(minutes=5)
        lock_until = now + lock_duration

        # Begin ACID Transaction with Row-Level Locking
        with transaction.atomic():
            # select_for_update locks the matching database rows during this transaction
            show_seats = list(
                ShowSeat.objects.select_for_update().filter(
                    show_id=show_id,
                    id__in=seat_ids
                )
            )

            if len(show_seats) != len(seat_ids):
                return JsonResponse({'success': False, 'error': 'One or more selected seats could not be found.'}, status=404)

            conflicted_seats = []
            for ss in show_seats:
                # If already booked
                if ss.status == ShowSeat.STATUS_BOOKED:
                    conflicted_seats.append(ss.seat.label)
                # If locked by another user and lock has not expired
                elif ss.status == ShowSeat.STATUS_LOCKED and ss.locked_by != request.user and ss.locked_until and ss.locked_until > now:
                    conflicted_seats.append(ss.seat.label)

            if conflicted_seats:
                conflict_str = ", ".join(conflicted_seats)
                return JsonResponse({
                    'success': False,
                    'error': f"Seat(s) {conflict_str} were just reserved by another user. Please choose alternative seats."
                }, status=409)

            # All requested seats are free or expired; lock them for current user
            for ss in show_seats:
                ss.status = ShowSeat.STATUS_LOCKED
                ss.locked_by = request.user
                ss.locked_until = lock_until
                ss.save(update_fields=['status', 'locked_by', 'locked_until'])

        # Store locked seat IDs and show ID into user session
        request.session['active_booking'] = {
            'show_id': show_id,
            'show_seat_ids': seat_ids,
            'locked_until': lock_until.isoformat(),
        }

        return JsonResponse({
            'success': True,
            'message': 'Seats locked successfully for 5 minutes.',
            'redirect_url': reverse('bookings:booking_summary')
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"An unexpected error occurred: {str(e)}"}, status=500)
