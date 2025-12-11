# Billiard Backend - Setup & Quick Start Guide

## Overview
Django-based backend for billiard tournament management with REST API, WebSocket support, and JWT authentication.

## Features
- ✅ JWT Authentication with login endpoint
- ✅ Public REST API for tournaments and matches
- ✅ Bíró (Admin) CRUD endpoints for full tournament management
- ✅ WebSocket support for live match updates
- ✅ Bíró WebSocket for live match administration
- ✅ Django Admin interface with all models registered

## Prerequisites
- Python 3.12+
- Redis (for WebSocket channels)
- Virtual Environment

## Installation

### 1. Activate Virtual Environment
```bash
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables (Optional)
Create `.env` file:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Create Bíró Profile
After creating superuser, run:
```python
python manage.py shell
```
```python
from django.contrib.auth.models import User
from api.models import Profile

user = User.objects.get(username='your_username')
profile, created = Profile.objects.get_or_create(user=user)
profile.is_biro = True
profile.save()
```

### 7. Start Redis (Required for WebSockets)
```bash
redis-server
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Or with ASGI for WebSocket support:
```bash
daphne -b 0.0.0.0 -p 8000 biliardbackend.asgi:application
```

## Quick Test

### 1. Login to get JWT token
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

### 2. Access Django Admin
```
http://localhost:8000/admin/
```

### 3. Test Public API
```bash
curl http://localhost:8000/api/tournaments/
```

### 4. Test Bíró Endpoint
```bash
curl -X GET http://localhost:8000/api/biro/tournaments/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Endpoints Summary

### Public (No Auth)
- `GET /api/tournaments/` - List tournaments
- `GET /api/tournaments/<id>/` - Tournament details
- `GET /api/matches/` - List matches
- `GET /api/matches/<id>/` - Match details

### Authentication
- `POST /api/login/` - Login and get JWT

### Authenticated
- `GET /api/profile/` - My profile
- `GET /api/profile/<user_id>/` - User profile

### Bíró Admin (requires is_biro=true)
- **Tournaments**: `/api/biro/tournaments/`
- **Phases**: `/api/biro/tournaments/<id>/phases/`
- **Groups**: `/api/biro/phases/<id>/groups/`
- **Matches**: `/api/biro/matches/`
- **Frames**: `/api/biro/matches/<id>/frames/`
- **Events**: `/api/biro/frames/<id>/events/`
- **Profiles**: `/api/biro/profiles/`

All bíró endpoints support:
- `GET` - List/retrieve
- `POST` - Create
- `PUT` - Update
- `DELETE` - Delete

## WebSocket Endpoints

### Live Match Viewer (Public)
```
ws://localhost:8000/ws/match/<match_id>/
```

### Bíró Match Admin (Authenticated)
```
ws://localhost:8000/ws/biro/match/<match_id>/?token=<jwt_token>
```

## Project Structure
```
biliard-backend/
├── api/
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API endpoints
│   ├── urls.py            # URL routing
│   ├── consumers.py       # WebSocket consumers
│   ├── routing.py         # WebSocket routing
│   ├── utils.py           # Auth decorators
│   └── admin.py           # Django admin config
├── biliardbackend/
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL config
│   └── asgi.py            # ASGI config for WebSockets
├── manage.py
├── requirements.txt
└── API_DOCUMENTATION.md
```

## Development Tips

### Testing WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/match/1/');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));
```

### Testing Bíró WebSocket
```javascript
const token = 'YOUR_JWT_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/ws/biro/match/1/?token=${token}`);

// Create event
ws.send(JSON.stringify({
  action: 'create_event',
  event_data: {
    eventType: 'balls_potted',
    player_id: 1,
    ball_ids: [1, 2],
    turn_number: 1
  }
}));
```

### Common Commands
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

## Troubleshooting

### "No module named rest_framework"
```bash
pip install djangorestframework djangorestframework-simplejwt
```

### "No module named channels"
```bash
pip install channels channels-redis
```

### WebSocket connection refused
Make sure Redis is running:
```bash
redis-server
```

### CORS issues
Add your frontend URL to `CORS_ALLOWED_ORIGINS` in `settings.py`

## Production Deployment

1. Set `DEBUG=False` in settings
2. Configure proper `SECRET_KEY`
3. Set `ALLOWED_HOSTS`
4. Use production ASGI server (Daphne, Uvicorn)
5. Configure Redis for production
6. Use PostgreSQL instead of SQLite
7. Set up static files serving
8. Enable HTTPS

## Additional Resources
- Full API Documentation: `API_DOCUMENTATION.md`
- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- Channels Docs: https://channels.readthedocs.io/
