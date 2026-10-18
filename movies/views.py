from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from .models import Movie, Genre, Actor, Wishlist
from cinemas.models import Cinema
from bookings.models import Coupon
from reviews.models import Review


def home_view(request):
    featured_movies = Movie.objects.filter(is_featured=True, status=Movie.STATUS_NOW_SHOWING)[:4]
    now_showing = Movie.objects.filter(status=Movie.STATUS_NOW_SHOWING).order_by('-rating')[:8]
    coming_soon = Movie.objects.filter(status=Movie.STATUS_COMING_SOON).order_by('release_date')[:4]
    cinemas = Cinema.objects.filter(is_active=True)[:3]
    coupons = Coupon.objects.filter(is_active=True)[:4]

    # AI Recommendation Preview
    recommended_movies = []
    try:
        from recommendations.recommender import get_recommendations_for_user
        recommended_movies = get_recommendations_for_user(request.user, limit=4)
    except Exception:
        recommended_movies = Movie.objects.filter(status=Movie.STATUS_NOW_SHOWING).order_by('-rating')[:4]

    context = {
        'featured_movies': featured_movies,
        'now_showing': now_showing,
        'coming_soon': coming_soon,
        'cinemas': cinemas,
        'coupons': coupons,
        'recommended_movies': recommended_movies,
    }
    return render(request, 'home.html', context)


def movie_list_view(request):
    movies = Movie.objects.all()
    genres = Genre.objects.all()

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        movies = movies.filter(
            Q(title__icontains=q) |
            Q(director__icontains=q) |
            Q(synopsis__icontains=q) |
            Q(genres__name__icontains=q) |
            Q(cast__name__icontains=q)
        ).distinct()

    # Genre filter
    genre_slug = request.GET.get('genre', '').strip()
    if genre_slug:
        movies = movies.filter(genres__slug=genre_slug)

    # Language filter
    language = request.GET.get('language', '').strip()
    if language:
        movies = movies.filter(language__iexact=language)

    # Status filter
    status = request.GET.get('status', '').strip()
    if status:
        movies = movies.filter(status=status)
    else:
        # Default show now showing first
        pass

    # Certification filter
    cert = request.GET.get('certification', '').strip()
    if cert:
        movies = movies.filter(certification=cert)

    # Format filter (movies that have upcoming shows in this format)
    fmt = request.GET.get('format', '').strip()
    if fmt:
        movies = movies.filter(shows__format=fmt, shows__is_active=True).distinct()

    show_date = request.GET.get('date', '').strip()
    if show_date:
        movies = movies.filter(shows__date=show_date, shows__is_active=True).distinct()

    # Sorting
    sort_by = request.GET.get('sort', 'rating_desc')
    if sort_by == 'rating_desc':
        movies = movies.order_by('-rating')
    elif sort_by == 'release_desc':
        movies = movies.order_by('-release_date')
    elif sort_by == 'title_asc':
        movies = movies.order_by('title')

    # Available languages for dropdown
    languages = Movie.objects.values_list('language', flat=True).distinct()

    context = {
        'movies': movies,
        'genres': genres,
        'languages': languages,
        'selected_genre': genre_slug,
        'selected_language': language,
        'selected_status': status,
        'selected_cert': cert,
        'selected_sort': sort_by,
        'selected_format': fmt,
        'selected_date': show_date,
        'query': q,
    }
    return render(request, 'movies/movie_list.html', context)


def movie_detail_view(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    reviews = movie.reviews.select_related('user').order_by('-created_at')
    
    in_wishlist = False
    has_booked = False
    user_review = None

    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, movie=movie).exists()
        from bookings.models import Booking
        has_booked = Booking.objects.filter(
            user=request.user,
            show__movie=movie,
            booking_status=Booking.STATUS_CONFIRMED
        ).exists()
        user_review = Review.objects.filter(user=request.user, movie=movie).first()

    # Associated Shows for quick schedule preview
    from shows.models import Show
    from django.utils import timezone
    shows = Show.objects.filter(
        movie=movie,
        date__gte=timezone.now().date(),
        is_active=True
    ).select_related('screen__cinema').order_by('date', 'start_time')

    # Group shows by Cinema
    cinemas_with_shows = {}
    for show in shows:
        cinema = show.screen.cinema
        if cinema not in cinemas_with_shows:
            cinemas_with_shows[cinema] = []
        cinemas_with_shows[cinema].append(show)

    # Similar movies recommendation
    similar_movies = Movie.objects.filter(
        genres__in=movie.genres.all()
    ).exclude(id=movie.id).distinct().order_by('-rating')[:4]

    context = {
        'movie': movie,
        'reviews': reviews,
        'in_wishlist': in_wishlist,
        'has_booked': has_booked,
        'user_review': user_review,
        'cinemas_with_shows': cinemas_with_shows,
        'similar_movies': similar_movies,
    }
    return render(request, 'movies/movie_detail.html', context)


@login_required
def toggle_wishlist(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, movie=movie).first()
    
    if wishlist_item:
        wishlist_item.delete()
        is_saved = False
        msg = f"'{movie.title}' removed from your wishlist."
    else:
        Wishlist.objects.create(user=request.user, movie=movie)
        is_saved = True
        msg = f"'{movie.title}' added to your wishlist!"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_saved': is_saved, 'message': msg})
    
    messages.success(request, msg)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('movies:movie_detail', slug=movie.slug)


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('movie')
    return render(request, 'movies/wishlist.html', {'wishlist_items': wishlist_items})


def search_suggest_view(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'movies': [], 'cinemas': [], 'genres': [], 'actors': []})

    movies = list(
        Movie.objects.filter(Q(title__icontains=q) | Q(director__icontains=q))
        .values('title', 'slug', 'language', 'rating')[:6]
    )
    actors = list(Actor.objects.filter(name__icontains=q).values('name')[:5])
    genres = list(Genre.objects.filter(name__icontains=q).values('name', 'slug')[:5])
    cinemas = list(
        Cinema.objects.filter(Q(name__icontains=q) | Q(city__icontains=q), is_active=True)
        .values('name', 'slug', 'city')[:5]
    )
    return JsonResponse({'movies': movies, 'cinemas': cinemas, 'genres': genres, 'actors': actors})
