from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Cinema, Screen
from shows.models import Show


def cinema_list_view(request):
    cinemas = Cinema.objects.filter(is_active=True).prefetch_related('screens')
    city = request.GET.get('city', '').strip()
    if city:
        cinemas = cinemas.filter(city__iexact=city)

    cities = Cinema.objects.filter(is_active=True).values_list('city', flat=True).distinct()

    context = {
        'cinemas': cinemas,
        'cities': cities,
        'selected_city': city,
    }
    return render(request, 'cinemas/cinema_list.html', context)


def cinema_detail_view(request, slug):
    cinema = get_object_or_404(Cinema, slug=slug, is_active=True)
    today = timezone.now().date()
    
    # Retrieve upcoming shows scheduled at this cinema
    shows = Show.objects.filter(
        screen__cinema=cinema,
        date__gte=today,
        is_active=True
    ).select_related('movie', 'screen').order_by('date', 'start_time')

    # Group shows by Movie
    movies_with_shows = {}
    for show in shows:
        if show.movie not in movies_with_shows:
            movies_with_shows[show.movie] = []
        movies_with_shows[show.movie].append(show)

    context = {
        'cinema': cinema,
        'movies_with_shows': movies_with_shows,
    }
    return render(request, 'cinemas/cinema_detail.html', context)
