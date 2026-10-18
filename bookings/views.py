import datetime
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from .models import Coupon, CouponUsage, Booking, BookingSeat, Refund
from shows.models import Show, ShowSeat
from payments.models import Payment
from tickets.models import Ticket
from tickets.utils import generate_ticket_pdf_bytes
from accounts.models import Notification


@login_required
def booking_summary_view(request):
    active_booking = request.session.get('active_booking')
    if not active_booking:
        messages.warning(request, "No active seat reservation found. Please select seats from the cinema schedule.")
        return redirect('movies:movie_list')

    show_id = active_booking.get('show_id')
    seat_ids = active_booking.get('show_seat_ids', [])
    locked_until_str = active_booking.get('locked_until')

    try:
        locked_until = datetime.datetime.fromisoformat(locked_until_str)
        if timezone.is_naive(locked_until):
            locked_until = timezone.make_aware(locked_until)
    except Exception:
        locked_until = timezone.now()

    now = timezone.now()
    if now >= locked_until:
        # Lock expired
        request.session.pop('active_booking', None)
        request.session.pop('applied_coupon', None)
        messages.error(request, "Your 5-minute seat reservation timer has expired. Please select your seats again.")
        return redirect('shows:seat_layout', show_id=show_id)

    show = get_object_or_404(Show.objects.select_related('movie', 'screen__cinema'), id=show_id)
    show_seats = ShowSeat.objects.filter(
        id__in=seat_ids,
        show=show,
        status=ShowSeat.STATUS_LOCKED,
        locked_by=request.user
    ).select_related('seat')

    if show_seats.count() != len(seat_ids):
        messages.error(request, "One or more seats are no longer locked for you. Please reselect your seats.")
        return redirect('shows:seat_layout', show_id=show_id)

    # Calculate itemized bill
    ticket_total = sum(ss.price for ss in show_seats)
    convenience_fee = Decimal('30.00')
    taxable_amount = ticket_total + convenience_fee
    taxes = round(taxable_amount * Decimal('0.18'), 2)
    subtotal_before_discount = taxable_amount + taxes

    # Check coupon
    coupon_code = request.session.get('applied_coupon')
    discount_amount = Decimal('0.00')
    applied_coupon = None

    if coupon_code:
        applied_coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        if applied_coupon:
            valid, msg = applied_coupon.is_valid(subtotal_before_discount)
            if valid:
                discount_amount = Decimal(str(applied_coupon.calculate_discount(subtotal_before_discount)))
            else:
                request.session.pop('applied_coupon', None)
                applied_coupon = None

    final_total = max(Decimal('0.00'), subtotal_before_discount - discount_amount)

    # Remaining seconds on countdown timer
    seconds_remaining = max(0, int((locked_until - now).total_seconds()))

    context = {
        'show': show,
        'show_seats': show_seats,
        'ticket_total': ticket_total,
        'convenience_fee': convenience_fee,
        'taxes': taxes,
        'discount_amount': discount_amount,
        'applied_coupon': applied_coupon,
        'final_total': final_total,
        'seconds_remaining': seconds_remaining,
    }
    return render(request, 'bookings/summary.html', context)


@login_required
def apply_coupon_view(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        if not code:
            messages.error(request, "Please enter a valid coupon code.")
            return redirect('bookings:booking_summary')

        coupon = Coupon.objects.filter(code=code).first()
        if not coupon:
            messages.error(request, f"Coupon code '{code}' does not exist.")
            return redirect('bookings:booking_summary')

        active_booking = request.session.get('active_booking')
        if not active_booking:
            return redirect('movies:movie_list')

        show_seats = ShowSeat.objects.filter(id__in=active_booking.get('show_seat_ids', []))
        ticket_total = sum(ss.price for ss in show_seats)
        taxable = ticket_total + Decimal('30.00')
        taxes = round(taxable * Decimal('0.18'), 2)
        total = taxable + taxes

        valid, msg = coupon.is_valid(total)
        if valid:
            request.session['applied_coupon'] = coupon.code
            messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
        else:
            messages.error(request, msg)

    return redirect('bookings:booking_summary')


@login_required
def remove_coupon_view(request):
    request.session.pop('applied_coupon', None)
    messages.info(request, "Coupon removed.")
    return redirect('bookings:booking_summary')


@login_required
def release_seats_view(request):
    active_booking = request.session.get('active_booking')
    if active_booking:
        seat_ids = active_booking.get('show_seat_ids', [])
        ShowSeat.objects.filter(
            id__in=seat_ids,
            status=ShowSeat.STATUS_LOCKED,
            locked_by=request.user
        ).update(status=ShowSeat.STATUS_AVAILABLE, locked_by=None, locked_until=None)
        
        request.session.pop('active_booking', None)
        request.session.pop('applied_coupon', None)
        messages.info(request, "Your reserved seats have been released.")

    return redirect('movies:movie_list')


@login_required
def payment_gateway_view(request):
    active_booking = request.session.get('active_booking')
    if not active_booking:
        messages.warning(request, "No active reservation to pay for.")
        return redirect('movies:movie_list')

    show_id = active_booking.get('show_id')
    seat_ids = active_booking.get('show_seat_ids', [])
    show = get_object_or_404(Show.objects.select_related('movie', 'screen__cinema'), id=show_id)
    show_seats = ShowSeat.objects.filter(id__in=seat_ids, locked_by=request.user)

    if not show_seats.exists():
        messages.error(request, "Seats are no longer reserved. Please re-select.")
        return redirect('shows:seat_layout', show_id=show_id)

    # Calculate final amount
    ticket_total = sum(ss.price for ss in show_seats)
    convenience_fee = Decimal('30.00')
    taxable_amount = ticket_total + convenience_fee
    taxes = round(taxable_amount * Decimal('0.18'), 2)
    subtotal = taxable_amount + taxes

    coupon_code = request.session.get('applied_coupon')
    discount_amount = Decimal('0.00')
    if coupon_code:
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        if coupon:
            discount_amount = Decimal(str(coupon.calculate_discount(subtotal)))

    final_total = max(Decimal('0.00'), subtotal - discount_amount)

    context = {
        'show': show,
        'show_seats': show_seats,
        'final_total': final_total,
    }
    return render(request, 'bookings/payment.html', context)


@login_required
def process_payment_view(request):
    if request.method != 'POST':
        return redirect('bookings:booking_summary')

    active_booking = request.session.get('active_booking')
    if not active_booking:
        messages.error(request, "No active reservation found.")
        return redirect('movies:movie_list')

    payment_action = request.POST.get('payment_action', 'SUCCESS')
    payment_method = request.POST.get('payment_method', Payment.METHOD_UPI)
    show_id = active_booking.get('show_id')
    seat_ids = active_booking.get('show_seat_ids', [])

    # If simulated payment failure
    if payment_action == 'FAILED':
        # Release seats
        ShowSeat.objects.filter(
            id__in=seat_ids,
            locked_by=request.user
        ).update(status=ShowSeat.STATUS_AVAILABLE, locked_by=None, locked_until=None)

        request.session.pop('active_booking', None)
        request.session.pop('applied_coupon', None)

        Notification.objects.create(
            user=request.user,
            title="Payment Failed",
            message="Your ticket transaction could not be processed. Any temporarily held seats have been released.",
            notification_type=Notification.TYPE_WARNING
        )
        return render(request, 'bookings/booking_failed.html')

    # Payment SUCCESS Flow with ACID concurrency transaction
    try:
        with transaction.atomic():
            show = get_object_or_404(Show, id=show_id)
            show_seats = list(
                ShowSeat.objects.select_for_update().filter(
                    id__in=seat_ids,
                    show=show,
                    locked_by=request.user
                )
            )

            if len(show_seats) != len(seat_ids):
                messages.error(request, "Reservation expired during payment. Please try again.")
                return redirect('shows:seat_layout', show_id=show_id)

            now = timezone.now()
            for ss in show_seats:
                if ss.status == ShowSeat.STATUS_BOOKED:
                    messages.error(request, "One or more seats were already booked. Please choose again.")
                    return redirect('shows:seat_layout', show_id=show_id)
                if ss.locked_until and ss.locked_until <= now:
                    messages.error(request, "Your seat lock expired during payment. Please select seats again.")
                    return redirect('shows:seat_layout', show_id=show_id)

            ticket_total = sum(ss.price for ss in show_seats)
            convenience_fee = Decimal('30.00')
            taxable_amount = ticket_total + convenience_fee
            taxes = round(taxable_amount * Decimal('0.18'), 2)
            subtotal = taxable_amount + taxes

            coupon_code = request.session.get('applied_coupon')
            discount_amount = Decimal('0.00')
            applied_coupon = None

            if coupon_code:
                applied_coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
                if applied_coupon:
                    discount_amount = Decimal(str(applied_coupon.calculate_discount(subtotal)))
                    applied_coupon.times_used += 1
                    applied_coupon.save(update_fields=['times_used'])

            final_total = max(Decimal('0.00'), subtotal - discount_amount)

            # 1. Create Booking
            booking = Booking.objects.create(
                user=request.user,
                show=show,
                total_ticket_price=ticket_total,
                convenience_fee=convenience_fee,
                tax_amount=taxes,
                discount_amount=discount_amount,
                coupon=applied_coupon,
                final_amount=final_total,
                booking_status=Booking.STATUS_CONFIRMED
            )

            # 2. Create BookingSeat and convert ShowSeat from LOCKED -> BOOKED
            for ss in show_seats:
                BookingSeat.objects.create(
                    booking=booking,
                    show_seat=ss,
                    seat_price=ss.price
                )
                ss.status = ShowSeat.STATUS_BOOKED
                ss.locked_by = None
                ss.locked_until = None
                ss.save(update_fields=['status', 'locked_by', 'locked_until'])

            # 3. Create Payment record
            Payment.objects.create(
                booking=booking,
                payment_method=payment_method,
                amount=final_total,
                status=Payment.STATUS_SUCCESS
            )

            if applied_coupon:
                CouponUsage.objects.create(coupon=applied_coupon, user=request.user, booking=booking)

            # 4. Generate Ticket with QR code
            ticket = Ticket.objects.create(booking=booking)

            # 5. Award loyalty points (1 point per ₹20 spent)
            if hasattr(request.user, 'profile'):
                points_earned = int(final_total // 20)
                request.user.profile.loyalty_points += points_earned
                request.user.profile.save(update_fields=['loyalty_points'])

            # 6. Create in-app Notification
            Notification.objects.create(
                user=request.user,
                title="Booking Confirmed!",
                message=f"Your tickets for '{show.movie.title}' (Booking ID: {booking.booking_id}) at {show.screen.cinema.name} are confirmed. Present your digital QR ticket at the gate.",
                notification_type=Notification.TYPE_TICKET
            )

        # Clear active booking session
        request.session.pop('active_booking', None)
        request.session.pop('applied_coupon', None)

        messages.success(request, "Payment successful! Your tickets have been reserved.")
        return redirect('bookings:booking_success', booking_id=booking.booking_id)

    except Exception as e:
        messages.error(request, f"Error completing booking: {str(e)}")
        return redirect('bookings:booking_summary')


@login_required
def booking_success_view(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('show__movie', 'show__screen__cinema', 'payment', 'ticket'),
        booking_id=booking_id,
        user=request.user
    )
    return render(request, 'bookings/booking_success.html', {'booking': booking})


@login_required
def my_bookings_view(request):
    bookings = Booking.objects.filter(user=request.user).select_related(
        'show__movie', 'show__screen__cinema', 'ticket'
    ).order_by('-created_at')

    today = timezone.now().date()
    upcoming_bookings = [b for b in bookings if b.booking_status == Booking.STATUS_CONFIRMED and b.show.date >= today]
    completed_bookings = [b for b in bookings if b.booking_status == Booking.STATUS_CONFIRMED and b.show.date < today]
    cancelled_bookings = [b for b in bookings if b.booking_status == Booking.STATUS_CANCELLED]

    context = {
        'upcoming_bookings': upcoming_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
    }
    return render(request, 'bookings/my_bookings.html', context)


@login_required
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)

    if booking.booking_status != Booking.STATUS_CONFIRMED:
        messages.warning(request, "Only confirmed bookings can be cancelled.")
        return redirect('bookings:my_bookings')

    if not booking.can_cancel:
        messages.error(request, "This booking cannot be cancelled because the show has already commenced.")
        return redirect('bookings:my_bookings')

    if request.method == 'POST':
        reason = request.POST.get('reason', 'Customer request')
        refund_pct = booking.refund_percentage_eligibility()
        refund_amount = round((booking.final_amount * Decimal(str(refund_pct))) / Decimal('100'), 2)

        with transaction.atomic():
            booking.booking_status = Booking.STATUS_CANCELLED
            booking.save(update_fields=['booking_status', 'updated_at'])

            # Free the seats back to AVAILABLE
            for bs in booking.booked_seats.select_related('show_seat'):
                ss = bs.show_seat
                ss.status = ShowSeat.STATUS_AVAILABLE
                ss.locked_by = None
                ss.locked_until = None
                ss.save(update_fields=['status', 'locked_by', 'locked_until'])

            # Create Refund record
            Refund.objects.create(
                booking=booking,
                refund_amount=refund_amount,
                refund_percentage=refund_pct,
                cancellation_reason=reason,
                status='PROCESSED'
            )

            # Update Payment status if refund occurred
            if hasattr(booking, 'payment'):
                booking.payment.status = Payment.STATUS_REFUNDED
                booking.payment.save(update_fields=['status'])

            # In-app notification
            Notification.objects.create(
                user=request.user,
                title="Booking Cancelled",
                message=f"Booking {booking.booking_id} for '{booking.show.movie.title}' was cancelled. Refund of ₹{refund_amount} ({refund_pct}%) has been issued.",
                notification_type=Notification.TYPE_INFO
            )

        messages.success(request, f"Booking cancelled successfully. Refund of ₹{refund_amount} ({refund_pct}%) processed.")
        return redirect('bookings:my_bookings')

    refund_pct = booking.refund_percentage_eligibility()
    estimated_refund = round((booking.final_amount * Decimal(str(refund_pct))) / Decimal('100'), 2)

    context = {
        'booking': booking,
        'refund_pct': refund_pct,
        'estimated_refund': estimated_refund,
    }
    return render(request, 'bookings/cancel_booking.html', context)


@login_required
def download_ticket_pdf(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    if not hasattr(booking, 'ticket'):
        messages.error(request, "Ticket pass not found for this booking.")
        return redirect('bookings:my_bookings')

    pdf_bytes = generate_ticket_pdf_bytes(booking.ticket)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CineReserve_Ticket_{booking.booking_id}.pdf"'
    return response


def offers_view(request):
    coupons = Coupon.objects.filter(is_active=True).order_by('-discount_value')
    return render(request, 'bookings/offers.html', {'coupons': coupons})


def terms_view(request):
    return render(request, 'bookings/terms.html')


def privacy_view(request):
    return render(request, 'bookings/privacy.html')


def refund_policy_view(request):
    return render(request, 'bookings/refund_policy.html')


def faq_view(request):
    return render(request, 'bookings/faq.html')


def about_view(request):
    return render(request, 'bookings/about.html')


def booking_failed_view(request):
    return render(request, 'bookings/booking_failed.html')
