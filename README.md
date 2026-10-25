# CineReserve – Smart Movie Reservation & Cinema Management System

CineReserve is a full-stack Django cinema booking platform for movie discovery, interactive seat selection, real-time reservations, simulated payments, QR/PDF ticketing, role-based cinema operations, and AI-powered movie recommendations. It is designed as an original BCA AIML final-year capstone, not a thin CRUD demo.

## Features

- Customer, Admin, and Cinema Manager roles with hashed passwords and session auth
- Browse, search, and filter movies; cinema and showtime selection
- Interactive seat map with Regular / Premium / VIP / Recliner tiers
- 5-minute seat locking with `transaction.atomic()` and `select_for_update()` (double-booking protection)
- Coupons, GST-style tax, convenience fee, booking summary
- Simulated payment gateway (UPI / card / net banking / wallet) — no card data stored
- QR tickets, PDF download, print, in-app notifications
- Cancellation with 100% / 75% / 0% refund policy
- Wishlist, verified-buyer reviews, profile and loyalty points
- TF-IDF + cosine similarity recommendations (Pandas, NumPy, Scikit-Learn)
- Rule-based NLP chatbot for movies, showtimes, coupons, and refunds
- Admin and manager dashboards with occupancy and revenue charts
- REST APIs under `/api/`
- 403 / 404 / 500 pages

## Technology stack

- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Backend: Python, Django 5, Django REST Framework
- Database: SQLite (development) / PostgreSQL-ready
- AIML: Pandas, NumPy, Scikit-Learn
- Tickets: `qrcode`, ReportLab, Pillow

## System requirements

- Python 3.11+
- pip
- Windows / macOS / Linux

## Installation

```bash
cd CineReserve   # or this project folder
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy .env.example .env         # Windows
# cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Database setup

Development uses SQLite (`db.sqlite3`). For PostgreSQL, set Django `DATABASES` in `cinereserve_core/settings.py` to:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cinereserve',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Then run `python manage.py migrate` again.

## Environment variables

See `.env.example`. Never commit `.env`. Typical keys:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` (sandbox placeholders)
- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD`

## How to run tests

```bash
python manage.py test
```

## Demo accounts (after seed_data)

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@1234` |
| Cinema Manager | `manager_pvr` | `Manager@1234` |
| Customer | `customer1` | `Customer@1234` |
| Customer | `customer2` | `Customer@1234` |

Django admin: http://127.0.0.1:8000/admin/

Coupons: `WELCOME100`, `MOVIE50`, `CINEPROMO20`, `FIRSTBOOKING`

## API documentation

Base path: `/api/`

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register/` | Create customer |
| POST | `/api/auth/login/` | Session login |
| GET | `/api/movies/` | Catalogue |
| GET | `/api/movies/{id}/` | Movie detail |
| GET | `/api/cinemas/` | Venues |
| GET | `/api/cinemas/{id}/` | Cinema detail |
| GET | `/api/shows/` | Query `movie`, `date`, `cinema` |
| GET | `/api/shows/{id}/seats/` | Seat inventory |
| GET | `/api/bookings/` | Authenticated history |
| POST | `/shows/api/lock-seats/` | Lock seats (session + CSRF) |
| GET | `/api/recommendations/` | Hybrid recommender |
| GET/POST | `/api/reviews/` | List / create (verified buyer rules on HTML flow) |

Browsable API: http://127.0.0.1:8000/api/movies/

## Project structure

```
cinereserve_core/   Django settings, root URLs, error handlers
accounts/           Users, roles, profile, password reset, notifications
movies/             Catalogue, wishlist, home, search
cinemas/            Venues, screens, seats
shows/              Showtimes, seat map, lock API
bookings/           Summary, coupons, payment, tickets, policies
payments/           Payment records (no PAN/CVV storage)
tickets/            QR + PDF generation
reviews/            Verified ratings
recommendations/    TF-IDF recommender
chatbot/            Intent classifier
dashboard/          Admin + manager analytics
api/                DRF endpoints
templates/ static/ media/
```

## Future scope

- Native mobile apps
- WebSocket live seat sync
- Full collaborative filtering
- LLM-backed chatbot
- Dynamic pricing and demand prediction
- Additional payment gateways and cloud deployment
- Microservices split

## Academic note

All movies, cinemas, and characters in seed data are fictional demo content for academic demonstration.
