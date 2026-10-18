from django.contrib.auth import authenticate, get_user_model, login
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.models import Movie
from cinemas.models import Cinema
from shows.models import Show, ShowSeat
from bookings.models import Booking, Coupon
from reviews.models import Review
from recommendations.recommender import get_recommendations_for_user
from .serializers import (
    RegisterSerializer, MovieSerializer, CinemaSerializer, ShowSerializer,
    ShowSeatSerializer, BookingSerializer, ReviewSerializer, CouponSerializer,
)

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        login_id = request.data.get('username') or request.data.get('email') or ''
        password = request.data.get('password', '')
        user_obj = None
        if '@' in login_id:
            user_obj = User.objects.filter(email__iexact=login_id).first()
        else:
            user_obj = User.objects.filter(username__iexact=login_id).first()
        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None
        if not user:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response({'username': user.username, 'role': user.role})


class MovieListAPIView(generics.ListAPIView):
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Movie.objects.all().prefetch_related('genres', 'cast')


class MovieDetailAPIView(generics.RetrieveAPIView):
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Movie.objects.all().prefetch_related('genres', 'cast')
    lookup_field = 'pk'


class CinemaListAPIView(generics.ListAPIView):
    serializer_class = CinemaSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Cinema.objects.filter(is_active=True)


class CinemaDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CinemaSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Cinema.objects.filter(is_active=True)


class ShowListAPIView(generics.ListAPIView):
    serializer_class = ShowSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Show.objects.filter(is_active=True).select_related('movie', 'screen__cinema')
        movie_id = self.request.query_params.get('movie')
        date = self.request.query_params.get('date')
        cinema_id = self.request.query_params.get('cinema')
        if movie_id:
            qs = qs.filter(movie_id=movie_id)
        if date:
            qs = qs.filter(date=date)
        if cinema_id:
            qs = qs.filter(screen__cinema_id=cinema_id)
        return qs


class ShowSeatsAPIView(generics.ListAPIView):
    serializer_class = ShowSeatSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return ShowSeat.objects.filter(show_id=self.kwargs['pk']).select_related('seat')


class MyBookingsAPIView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('show__movie', 'show__screen__cinema')


class CouponListAPIView(generics.ListAPIView):
    serializer_class = CouponSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Coupon.objects.filter(is_active=True)


class ReviewListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = Review.objects.select_related('user', 'movie')
        movie_id = self.request.query_params.get('movie')
        if movie_id:
            qs = qs.filter(movie_id=movie_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recommendations_api(request):
    movies = get_recommendations_for_user(request.user, limit=8)
    return Response(MovieSerializer(movies, many=True).data)
