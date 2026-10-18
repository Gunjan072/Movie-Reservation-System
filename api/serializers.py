from rest_framework import serializers
from django.contrib.auth import get_user_model
from movies.models import Movie, Genre, Actor
from cinemas.models import Cinema, Screen
from shows.models import Show, ShowSeat
from bookings.models import Booking, Coupon
from reviews.models import Review

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data, role=User.ROLE_CUSTOMER)
        user.set_password(password)
        user.save()
        return user


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ['id', 'name']


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    cast = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'synopsis', 'duration', 'language', 'release_date',
            'director', 'certification', 'rating', 'votes_count', 'trailer_url',
            'status', 'genres', 'cast',
        ]


class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ['id', 'name', 'slug', 'address', 'city', 'facilities', 'contact_number']


class ScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screen
        fields = ['id', 'name', 'screen_type', 'total_capacity']


class ShowSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    cinema = serializers.CharField(source='screen.cinema.name', read_only=True)
    screen_name = serializers.CharField(source='screen.name', read_only=True)
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = [
            'id', 'movie', 'cinema', 'screen_name', 'date', 'start_time', 'end_time',
            'format', 'language', 'base_price', 'available_seats',
        ]

    def get_available_seats(self, obj):
        return obj.available_seats_count()


class ShowSeatSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='seat.label', read_only=True)
    row = serializers.CharField(source='seat.row', read_only=True)
    number = serializers.IntegerField(source='seat.number', read_only=True)
    seat_type = serializers.CharField(source='seat.seat_type', read_only=True)
    available = serializers.SerializerMethodField()

    class Meta:
        model = ShowSeat
        fields = ['id', 'label', 'row', 'number', 'seat_type', 'price', 'status', 'available']

    def get_available(self, obj):
        return obj.is_available()


class BookingSerializer(serializers.ModelSerializer):
    movie = serializers.CharField(source='show.movie.title', read_only=True)
    cinema = serializers.CharField(source='show.screen.cinema.name', read_only=True)
    seats = serializers.CharField(source='seat_labels', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'movie', 'cinema', 'final_amount', 'booking_status',
            'seats', 'created_at',
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'min_amount', 'max_discount', 'valid_until']


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'headline', 'comment', 'is_verified_buyer', 'created_at']
        read_only_fields = ['is_verified_buyer', 'created_at']
