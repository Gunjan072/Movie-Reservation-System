import math
import re
from collections import Counter
import numpy as np
import pandas as pd

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    ENGLISH_STOP_WORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
        "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
        "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
        "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
        "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
        "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
        "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
        "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
        "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
        "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
        "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
        "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
        "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
    }

    class TfidfVectorizer:  # type: ignore[no-redef]
        def __init__(self, stop_words='english', max_features=1500):
            self.stop_words = ENGLISH_STOP_WORDS if stop_words == 'english' else set()
            self.max_features = max_features
            self.vocabulary_ = {}
            self.idf_ = None

        def _tokenize(self, text):
            words = re.findall(r'(?u)\b\w\w+\b', str(text).lower())
            return [w for w in words if w not in self.stop_words]

        def fit_transform(self, raw_documents):
            tokenized_docs = [self._tokenize(doc) for doc in raw_documents]
            doc_count = len(tokenized_docs)
            if doc_count == 0:
                return np.zeros((0, 0))

            df_counts = Counter()
            for doc in tokenized_docs:
                unique_words = set(doc)
                for w in unique_words:
                    df_counts[w] += 1

            most_common = df_counts.most_common(self.max_features)
            self.vocabulary_ = {word: idx for idx, (word, _) in enumerate(most_common)}
            num_features = len(self.vocabulary_)

            self.idf_ = np.zeros(num_features)
            for word, idx in self.vocabulary_.items():
                self.idf_[idx] = math.log((1 + doc_count) / (1 + df_counts[word])) + 1.0

            matrix = np.zeros((doc_count, num_features), dtype=np.float64)
            for i, doc in enumerate(tokenized_docs):
                if not doc:
                    continue
                tf = Counter(doc)
                for word, count in tf.items():
                    if word in self.vocabulary_:
                        j = self.vocabulary_[word]
                        matrix[i, j] = count * self.idf_[j]
                norm = np.linalg.norm(matrix[i])
                if norm > 0:
                    matrix[i] /= norm

            return matrix

    def cosine_similarity(X, Y=None):  # type: ignore[no-redef]
        if Y is None:
            Y = X
        return np.dot(X, Y.T)
from movies.models import Movie, Wishlist
from bookings.models import Booking


def build_feature_soup(movie):
    """
    Combines movie metadata into a weighted text soup for TF-IDF feature extraction.
    Genres and Language are weighted by repeating them.
    """
    genres = " ".join([g.name for g in movie.genres.all()] * 3)
    cast = " ".join([a.name.replace(" ", "") for a in movie.cast.all()])
    director = movie.director.replace(" ", "")
    language = f"{movie.language} " * 2
    certification = movie.certification
    synopsis = movie.synopsis

    return f"{genres} {language} {director} {cast} {certification} {synopsis}".lower()


def get_all_movies_dataframe():
    """
    Extracts all movies from the project database into a Pandas DataFrame.
    """
    movies = list(Movie.objects.prefetch_related('genres', 'cast').all())
    if not movies:
        return None, []

    data = []
    for m in movies:
        data.append({
            'id': m.id,
            'title': m.title,
            'language': m.language,
            'rating': float(m.rating),
            'status': m.status,
            'soup': build_feature_soup(m)
        })

    df = pd.DataFrame(data)
    return df, movies


def compute_similarity_matrix():
    """
    Computes TF-IDF vectorization and pairwise Cosine Similarity matrix on movies.
    """
    df, movies = get_all_movies_dataframe()
    if df is None or len(df) == 0:
        return None, None, {}

    tfidf = TfidfVectorizer(stop_words='english', max_features=1500)
    tfidf_matrix = tfidf.fit_transform(df['soup'])

    # Compute pairwise cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Mapping of movie ID to matrix index
    indices = {row['id']: idx for idx, row in df.iterrows()}
    return cosine_sim, df, indices


def get_recommendations_for_user(user, limit=6):
    """
    Personalized Hybrid Recommender:
    Uses user booking history, wishlist, and profile preferences with Cosine Similarity.
    """
    cosine_sim, df, indices = compute_similarity_matrix()
    if df is None:
        return []

    movies_dict = {m.id: m for m in Movie.objects.prefetch_related('genres', 'cast').all()}

    # 1. Identify User's preference anchors
    interacted_movie_ids = set()
    user_weightings = {}

    if user and user.is_authenticated:
        # Bookings (High weight: 3.0)
        user_bookings = Booking.objects.filter(user=user, booking_status=Booking.STATUS_CONFIRMED).values_list('show__movie_id', flat=True)
        for mid in user_bookings:
            interacted_movie_ids.add(mid)
            user_weightings[mid] = user_weightings.get(mid, 0) + 3.0

        # Wishlist (Medium weight: 2.0)
        user_wishes = Wishlist.objects.filter(user=user).values_list('movie_id', flat=True)
        for mid in user_wishes:
            interacted_movie_ids.add(mid)
            user_weightings[mid] = user_weightings.get(mid, 0) + 2.0

        # User Profile Favorite Genre Match (Weight: 1.5)
        if hasattr(user, 'profile') and user.profile.favorite_genre:
            fav_genre = user.profile.favorite_genre.lower()
            for m in movies_dict.values():
                m_genres = [g.name.lower() for g in m.genres.all()]
                if any(fav_genre in g for g in m_genres):
                    user_weightings[m.id] = user_weightings.get(m.id, 0) + 1.5

    # 2. Compute aggregated recommendation scores
    num_movies = len(df)
    composite_scores = np.zeros(num_movies)

    if user_weightings:
        for mid, weight in user_weightings.items():
            if mid in indices:
                idx = indices[mid]
                composite_scores += cosine_sim[idx] * weight

        # Sort indices by descending score
        recommended_indices = composite_scores.argsort()[::-1]

        recommended_movies = []
        for idx in recommended_indices:
            movie_id = df.iloc[idx]['id']
            # Exclude movies the user has already confirmed booked
            if user and user.is_authenticated and movie_id in interacted_movie_ids:
                continue

            movie_obj = movies_dict.get(movie_id)
            if movie_obj and movie_obj.status == Movie.STATUS_NOW_SHOWING:
                recommended_movies.append(movie_obj)
            
            if len(recommended_movies) >= limit:
                break

        if recommended_movies:
            return recommended_movies

    # 3. Fallback for new / cold-start users: Popular & Highest-Rated Now Showing Movies
    return list(
        Movie.objects.filter(status=Movie.STATUS_NOW_SHOWING)
        .order_by('-rating', '-votes_count')[:limit]
    )
