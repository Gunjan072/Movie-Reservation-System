from django.shortcuts import render
from django.http import JsonResponse
from movies.models import Movie
from .recommender import get_recommendations_for_user


def recommended_view(request):
    recommended_movies = get_recommendations_for_user(request.user, limit=8)

    # Academic explanation context
    user_has_history = False
    if request.user.is_authenticated:
        user_has_history = request.user.bookings.filter(booking_status='CONFIRMED').exists() or request.user.wishlist_items.exists()

    context = {
        'recommended_movies': recommended_movies,
        'user_has_history': user_has_history,
    }
    return render(request, 'recommendations/recommended.html', context)


def recommendations_api(request):
    movies = get_recommendations_for_user(request.user, limit=6)
    data = []
    for m in movies:
        data.append({
            'id': m.id,
            'title': m.title,
            'slug': m.slug,
            'rating': float(m.rating),
            'genres': [g.name for g in m.genres.all()],
            'language': m.language,
            'poster_url': m.poster.url if m.poster else None,
        })
    return JsonResponse({'success': True, 'count': len(data), 'recommendations': data})
