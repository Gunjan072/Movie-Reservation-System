from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from movies.models import Movie
from bookings.models import Booking
from .models import Review


@login_required
def add_review_view(request, movie_id):
    if request.method != 'POST':
        return redirect('movies:movie_list')

    movie = get_object_or_404(Movie, id=movie_id)

    # Check verified buyer policy: user MUST have a confirmed booking for this movie
    has_booked = Booking.objects.filter(
        user=request.user,
        show__movie=movie,
        booking_status=Booking.STATUS_CONFIRMED
    ).exists()

    if not has_booked:
        messages.error(request, "Only verified patrons with a confirmed booking can post a review for this movie.")
        return redirect('movies:movie_detail', slug=movie.slug)

    rating = int(request.POST.get('rating', 5))
    headline = request.POST.get('headline', '').strip()
    comment = request.POST.get('comment', '').strip()

    if not headline or not comment:
        messages.error(request, "Please provide both a headline and review comments.")
        return redirect('movies:movie_detail', slug=movie.slug)

    review, created = Review.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={
            'rating': rating,
            'headline': headline,
            'comment': comment,
            'is_verified_buyer': True
        }
    )

    messages.success(request, "Thank you! Your verified review has been posted.")
    return redirect('movies:movie_detail', slug=movie.slug)
