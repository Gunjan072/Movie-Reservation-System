from django.test import TestCase
from django.contrib.auth import get_user_model
from movies.models import Genre, Movie
from recommendations.recommender import get_recommendations_for_user

User = get_user_model()


class RecommendationTests(TestCase):
    def setUp(self):
        action = Genre.objects.create(name='Action')
        comedy = Genre.objects.create(name='Comedy')
        self.m1 = Movie.objects.create(
            title='Action Blast', synopsis='explosions cars chase', duration=100,
            language='English', release_date='2026-01-01', director='A Dir',
            status=Movie.STATUS_NOW_SHOWING, rating=8.5,
        )
        self.m1.genres.add(action)
        self.m2 = Movie.objects.create(
            title='Action Reloaded', synopsis='chase explosions combat', duration=110,
            language='English', release_date='2026-02-01', director='B Dir',
            status=Movie.STATUS_NOW_SHOWING, rating=8.1,
        )
        self.m2.genres.add(action)
        self.m3 = Movie.objects.create(
            title='Silly Sitcom', synopsis='jokes friends wedding', duration=95,
            language='Hindi', release_date='2026-03-01', director='C Dir',
            status=Movie.STATUS_NOW_SHOWING, rating=7.0,
        )
        self.m3.genres.add(comedy)

    def test_cold_start_returns_now_showing(self):
        recs = get_recommendations_for_user(None, limit=3)
        self.assertTrue(len(recs) >= 1)

    def test_genre_preference_influences_recs(self):
        user = User.objects.create_user(username='fan', password='Pass12345')
        user.profile.favorite_genre = 'Action'
        user.profile.save()
        recs = get_recommendations_for_user(user, limit=3)
        titles = [m.title for m in recs]
        self.assertTrue(any('Action' in t for t in titles))
