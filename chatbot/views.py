import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from movies.models import Movie, Genre
from shows.models import Show
from .models import ChatMessage


# Intent pattern dictionary
INTENT_PATTERNS = {
    'movies_today': [
        r'movies?.*(today|now|showing|playing)',
        r'what.*show.*today',
        r'today.*movies?',
        r'current.*movies?',
    ],
    'action_movies': [
        r'action.*movies?',
        r'show.*action',
        r'action.*film',
    ],
    'horror_movies': [
        r'horror.*movies?',
        r'scary.*movies?',
        r'thriller.*film',
    ],
    'comedy_movies': [
        r'comedy.*movies?',
        r'funny.*movies?',
        r'rom.?com',
    ],
    'recommend': [
        r'recommend.*movie',
        r'suggest.*film',
        r'what.*should.*watch',
        r'good.*movie',
        r'best.*movie',
    ],
    'showtimes': [
        r'show.*time',
        r'timings',
        r'schedule',
        r'when.*show',
        r'shows.*tonight',
        r'evening.*show',
    ],
    'cancel_booking': [
        r'cancel.*booking',
        r'cancel.*ticket',
        r'refund.*ticket',
        r'how.*cancel',
    ],
    'find_ticket': [
        r'my.*ticket',
        r'where.*ticket',
        r'view.*ticket',
        r'booking.*id',
        r'find.*booking',
    ],
    'cinemas': [
        r'cinema',
        r'theater',
        r'multiplex',
        r'imax',
        r'near.*me',
    ],
    'coupons': [
        r'coupon',
        r'discount',
        r'promo.*code',
        r'offer',
    ],
    'greeting': [
        r'^hi$',
        r'^hello',
        r'^hey',
        r'good morning',
        r'good evening',
    ],
    'help': [
        r'help',
        r'how.*use',
        r'what.*can.*do',
        r'guide',
    ],
}


def classify_intent(text):
    text_lower = text.lower().strip()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent
    return 'general'


def generate_response(intent, user=None):
    """
    Generate rule-based intelligent responses for each intent.
    """

    if intent == 'greeting':
        name = user.first_name if user and user.is_authenticated and user.first_name else "there"
        return (
            f"Hello, {name}! 🎬 Welcome to CineReserve! I can help you find movies, discover showtimes, "
            f"manage your bookings, or get AI-powered movie recommendations. What would you like to do today?"
        )

    elif intent == 'movies_today':
        today = timezone.now().date()
        movies = Movie.objects.filter(
            status=Movie.STATUS_NOW_SHOWING
        ).order_by('-rating')[:5]

        if movies.exists():
            movie_list = "\n".join([
                f"🎬 <strong>{m.title}</strong> ({m.language}) — ⭐ {m.rating}/10"
                for m in movies
            ])
            return (
                f"Here are the top movies showing today:<br><br>{movie_list}<br><br>"
                f"<a href='/movies/' class='text-danger fw-bold'>Browse All Movies →</a>"
            )
        return "No movies are currently showing. Please check back soon!"

    elif intent in ['action_movies', 'horror_movies', 'comedy_movies']:
        genre_map = {
            'action_movies': 'Action',
            'horror_movies': 'Horror',
            'comedy_movies': 'Comedy',
        }
        genre_name = genre_map[intent]
        movies = Movie.objects.filter(
            genres__name__iexact=genre_name,
            status=Movie.STATUS_NOW_SHOWING
        ).order_by('-rating')[:4]

        if movies.exists():
            movie_list = "\n".join([
                f"🎬 <strong>{m.title}</strong> — ⭐ {m.rating}/10"
                for m in movies
            ])
            return (
                f"Here are the top <strong>{genre_name}</strong> movies currently showing:<br><br>"
                f"{movie_list}<br><br>"
                f"<a href='/movies/?genre={genre_name.lower()}' class='text-danger fw-bold'>View All {genre_name} Movies →</a>"
            )
        return f"No {genre_name} movies are currently in theaters. They may be arriving soon — check our Coming Soon section!"

    elif intent == 'recommend':
        from recommendations.recommender import get_recommendations_for_user
        try:
            movies = get_recommendations_for_user(user, limit=4)
            if movies:
                movie_list = "\n".join([
                    f"⭐ <strong>{m.title}</strong> ({m.language}) — {m.rating}/10"
                    for m in movies
                ])
                return (
                    f"Based on your movie preferences, our AI engine suggests:<br><br>"
                    f"{movie_list}<br><br>"
                    f"<a href='/recommendations/' class='text-danger fw-bold'>View Full AI Analysis →</a>"
                )
        except Exception:
            pass
        return "Explore our <a href='/recommendations/' class='text-danger'>AI Recommendations</a> page for personalized movie suggestions powered by Scikit-Learn!"

    elif intent == 'showtimes':
        today = timezone.now().date()
        shows = Show.objects.filter(
            date=today,
            is_active=True
        ).select_related('movie', 'screen__cinema').order_by('start_time')[:5]

        if shows.exists():
            show_list = "\n".join([
                f"🕐 <strong>{s.start_time.strftime('%I:%M %p')}</strong> — {s.movie.title} at {s.screen.cinema.name}"
                for s in shows
            ])
            return (
                f"Today's upcoming shows:<br><br>{show_list}<br><br>"
                f"<a href='/movies/' class='text-danger fw-bold'>Book Tickets Now →</a>"
            )
        return "No shows scheduled for today yet. Please check the Movies section for upcoming schedules."

    elif intent == 'cancel_booking':
        return (
            "📋 <strong>Cancellation Policy:</strong><br><br>"
            "• <strong>More than 24 hours before showtime:</strong> 100% full refund<br>"
            "• <strong>2 to 24 hours before showtime:</strong> 75% refund<br>"
            "• <strong>Less than 2 hours before showtime:</strong> No refund<br><br>"
            "To cancel, visit <a href='/bookings/my-bookings/' class='text-danger fw-bold'>My Bookings</a> and click the 'Cancel & Refund' button."
        )

    elif intent == 'find_ticket':
        ticket_url = '/bookings/my-bookings/'
        return (
            f"Your digital tickets are in <a href='{ticket_url}' class='text-danger fw-bold'>My Bookings</a>.<br><br>"
            "From there you can:<br>"
            "• 📱 View your QR code ticket<br>"
            "• 📄 Download a PDF pass<br>"
            "• ❌ Cancel and request a refund"
        )

    elif intent == 'cinemas':
        from cinemas.models import Cinema
        cinemas = Cinema.objects.filter(is_active=True)[:3]
        if cinemas.exists():
            cinema_list = "\n".join([
                f"🏢 <strong>{c.name}</strong> — {c.city}"
                for c in cinemas
            ])
            return (
                f"Our partner cinema locations:<br><br>{cinema_list}<br><br>"
                f"<a href='/cinemas/' class='text-danger fw-bold'>View All Cinemas →</a>"
            )
        return "Explore our partner cinemas at <a href='/cinemas/' class='text-danger'>CineReserve Venues</a>."

    elif intent == 'coupons':
        return (
            "🎟️ <strong>Active Promotional Coupons:</strong><br><br>"
            "• <code class='text-warning'>WELCOME100</code> — ₹100 off (min. ₹300)<br>"
            "• <code class='text-warning'>MOVIE50</code> — ₹50 off (min. ₹200)<br>"
            "• <code class='text-warning'>CINEPROMO20</code> — 20% off (max. ₹150)<br>"
            "• <code class='text-warning'>FIRSTBOOKING</code> — ₹75 off (min. ₹250)<br><br>"
            "Apply codes at the Booking Summary page during checkout!<br>"
            f"<a href='/bookings/offers/' class='text-danger fw-bold'>View All Offers →</a>"
        )

    elif intent == 'help':
        return (
            "🤖 <strong>I can assist you with:</strong><br><br>"
            "• 🎬 Discovering movies showing today<br>"
            "• ⏰ Finding show schedules & timings<br>"
            "• 🎫 Managing your bookings<br>"
            "• 💰 Explaining refund & cancellation policy<br>"
            "• 🌟 Getting personalized movie recommendations<br>"
            "• 🏷️ Finding discount coupons<br><br>"
            "Just type your question naturally!"
        )

    else:
        return (
            "I am not sure I understood that. Let me suggest a few things:<br><br>"
            "• Ask 'What movies are playing today?'<br>"
            "• Try 'Recommend an action movie'<br>"
            "• Say 'How do I cancel my booking?'<br>"
            "• Ask 'Show me available coupons'<br><br>"
            "<a href='/movies/' class='text-danger fw-bold'>Browse All Movies →</a>"
        )


def chatbot_message_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'reply': 'Please type a message!'})

        intent = classify_intent(user_message)
        reply = generate_response(intent, user=request.user if request.user.is_authenticated else None)

        # Log to database for analytics
        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or '',
            user_query=user_message,
            bot_response=reply,
            intent=intent
        )

        return JsonResponse({'success': True, 'reply': reply, 'intent': intent})

    except Exception as e:
        return JsonResponse({'success': False, 'reply': f'Sorry, I encountered an error. Please try again. ({str(e)})'})
