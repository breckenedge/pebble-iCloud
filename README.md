# Pebble iCloud Reminders Integration

A production-ready multi-tenant service that enables Pebble smartwatches to access iCloud Reminders. Built using Test-Driven Development (TDD) with comprehensive test coverage.

## ✨ Version 2.0 - Multi-Tenant Cloud Service

**New in v2.0:**
- ☁️ **Centralized deployment** - One server for all users
- 🔒 **Enhanced security** - No passwords stored on watch
- 🚀 **Production-ready** - Rate limiting, HTTPS, PostgreSQL support
- 📦 **Easy deployment** - Railway, Fly.io, Render, Heroku
- 🎯 **Fixed backend URL** - No manual configuration needed

## Features

- 🔐 **Multi-tenant architecture** with user isolation
- 🔑 **JWT-based authentication** (30-day tokens)
- ✅ **iCloud Reminders integration** (list, create, complete reminders)
- 🛡️ **Production security** (rate limiting, input validation, encrypted storage)
- 🧪 **31 passing tests** (100% coverage of core functionality)
- 🗄️ **Database support** (SQLite for dev, PostgreSQL for production)
- 🔒 **Fernet encryption** for Apple app-specific passwords
- 🌐 **Auto-scaling** ready for cloud platforms

## Architecture

### Multi-Tenant Cloud Deployment (v2.0)

```
┌──────────────────┐         ┌──────────────────┐         ┌────────────────────────────┐
│  Pebble Watch    │◄───────►│  Phone           │◄───────►│  Cloud Platform            │
│  (stores token)  │ AppMsg  │  (PebbleKit JS)  │  HTTPS  │  (Railway/Fly.io/Render)   │
└──────────────────┘         └──────────────────┘         │                            │
                                                           │  ┌──────────────────────┐  │
      Multiple Users                                       │  │  Flask Backend       │  │
           ↓ ↓ ↓                                           │  │  - Rate limiting     │  │
                                                           │  │  - Input validation  │  │
                                                           │  │  - Multi-user auth   │  │
                                                           │  └──────────┬───────────┘  │
                                                           │             ↓              │
                                                           │  ┌──────────────────────┐  │
                                                           │  │  PostgreSQL          │  │
                                                           │  │  - Encrypted creds   │  │
                                                           │  │  - User isolation    │  │
                                                           │  └──────────────────────┘  │
                                                           └────────────┬───────────────┘
                                                                        ↓
                                                                ┌───────────────┐
                                                                │ iCloud API    │
                                                                │ (pyicloud)    │
                                                                └───────────────┘
```

### Components

1. **Pebble Watch App** (`pebble-app/src/c/main.c`) ✅
   - C-based native Pebble application
   - View reminder lists and reminders
   - Mark reminders as complete
   - Secure credential storage on watch

2. **PebbleKit JS** (`pebble-app/src/pkjs/index.js`) ✅
   - Runs on companion phone
   - HTTP communication with Flask backend
   - Web-based configuration interface
   - Message relay between watch and backend

3. **Backend Service** (`backend/app.py`)
   - Flask REST API
   - Multi-user authentication with JWT
   - iCloud Reminders API integration
   - User credential management

4. **Authentication** (`backend/auth_service.py`)
   - User registration and login
   - Password encryption (Fernet)
   - JWT token generation/verification
   - SQLite database for user storage

5. **Test Suite**
   - `test_auth.py` - 11 authentication tests
   - `test_integration.py` - 7 integration tests
   - `test_reminders.py` - 13 reminders API tests
   - **Total: 31 passing tests**

## Getting Started

### For Users (Quick Start)

**Prerequisites:**
- Pebble smartwatch (Aplite, Basalt, Chalk, or Diorite)
- Pebble mobile app (iOS or Android)
- iCloud account with Reminders enabled
- App-specific password from [appleid.apple.com](https://appleid.apple.com)

**Installation Steps:**

1. **Install the Pebble App**
   - Download from Pebble Appstore (if published)
   - Or sideload using CloudPebble/local build

2. **Configure Your Account**
   - Open Pebble app → Settings → iCloud Reminders
   - Enter:
     - **Username**: Choose a unique username
     - **Apple ID**: your.email@icloud.com
     - **App-Specific Password**: (from appleid.apple.com)
   - Save settings

3. **Start Using**
   - App will auto-login and sync with iCloud
   - View reminder lists and items
   - Mark reminders complete from your wrist!

**No backend setup needed** - the service is hosted for you!

---

### For Developers (Deployment)

Want to deploy your own instance?

**Quick Deploy to Railway:**

1. **Generate secrets**:
   ```bash
   cd backend
   python3 generate_secrets.py
   ```

2. **Deploy to Railway**:
   - Go to [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub"
   - Select this repo
   - Add PostgreSQL database
   - Set environment variables (from step 1)

3. **Update Pebble app**:
   ```bash
   # Edit pebble-app/src/pkjs/index.js
   var BACKEND_URL = 'https://your-app.up.railway.app';
   ```

4. **Build and deploy**:
   ```bash
   cd pebble-app
   pebble build
   pebble install --phone <PHONE_IP>
   ```

**Full deployment guide**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

---

### Local Development

**1. Set up backend**:
```bash
cd backend
pip install -r requirements.txt
cp .env.development .env
python app.py
```

**2. Build Pebble app**:
```bash
cd pebble-app
# Edit src/pkjs/index.js: uncomment localhost URL
pebble build
pebble install --emulator
```

**3. Configure and test**:
- Open settings in Pebble app
- Enter credentials
- Test with local backend


### Configuration

Create a `.env` file in the `backend/` directory:

```bash
# iCloud Configuration
DATABASE_PATH=users.db
JWT_SECRET_KEY=your_secret_key_change_in_production
PORT=5000
FLASK_ENV=development
```

### Running the Service

```bash
cd backend
python app.py
```

The service will start on `http://localhost:5000`

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
python -m pytest test_auth.py -v
```

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "your_username",
  "apple_id": "your_apple_id@icloud.com",
  "apple_password": "your_app_specific_password"
}
```

**Response:**
```json
{
  "success": true,
  "token": "jwt_token_here",
  "user_id": 1
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "apple_id": "your_apple_id@icloud.com",
  "apple_password": "your_app_specific_password"
}
```

**Response:**
```json
{
  "success": true,
  "token": "jwt_token_here",
  "user_id": 1
}
```

### Reminders Endpoints

All reminders endpoints require authentication via JWT token in the `Authorization` header:

```
Authorization: Bearer {your_jwt_token}
```

#### Get Reminder Lists
```http
GET /api/reminders/lists
Authorization: Bearer {token}
```

**Response:**
```json
{
  "lists": [
    {
      "id": "list-guid-123",
      "title": "Personal",
      "color": "blue"
    }
  ]
}
```

#### Get Reminders from List
```http
GET /api/reminders/list/{list_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "reminders": [
    {
      "id": "reminder-guid-456",
      "title": "Buy groceries",
      "description": "Milk, eggs, bread",
      "completed": false,
      "due_date": null,
      "priority": 0
    }
  ]
}
```

#### Create Reminder
```http
POST /api/reminders
Authorization: Bearer {token}
Content-Type: application/json

{
  "list_id": "list-guid-123",
  "title": "New task",
  "description": "Optional description"
}
```

**Response:**
```json
{
  "success": true,
  "reminder": {
    "id": "new-reminder-guid",
    "title": "New task",
    "description": "Optional description"
  }
}
```

#### Complete Reminder
```http
POST /api/reminders/{reminder_id}/complete
Authorization: Bearer {token}
Content-Type: application/json

{
  "list_id": "list-guid-123"
}
```

**Response:**
```json
{
  "success": true
}
```

## Test-Driven Development Approach

This project was built using TDD:

1. **Write tests first** - All features were defined through tests before implementation
2. **Red-Green-Refactor** - Tests fail first, then code is written to pass, then refactored
3. **Comprehensive coverage** - 31 tests covering all critical paths
4. **Integration tests** - End-to-end testing of user flows

### Test Coverage

```
✓ Authentication (11 tests)
  - User registration
  - User login
  - Password encryption/decryption
  - JWT token generation/verification

✓ Integration (7 tests)
  - Complete authentication flow
  - Multi-user isolation
  - Protected endpoints
  - Health checks

✓ Reminders API (13 tests)
  - List retrieval
  - Reminder creation
  - Reminder completion
  - Error handling
```

## Security Features

### Production Security (v2.0)

**Authentication & Authorization:**
- ✅ JWT tokens with 30-day expiration
- ✅ Rate limiting (5 login attempts/min, 10 registrations/hour)
- ✅ Input validation (email format, username constraints)
- ✅ Password strength requirements (8+ characters)

**Data Protection:**
- ✅ Fernet symmetric encryption for Apple app-specific passwords
- ✅ Environment-based secret management
- ✅ No passwords stored on watch (token-only)
- ✅ Parameterized SQL queries (SQL injection protection)
- ✅ HTTPS enforced in production

**Infrastructure:**
- ✅ Multi-user isolation (per-user database rows)
- ✅ PostgreSQL in production (vs SQLite in dev)
- ✅ Automatic SSL/TLS (via Railway/Fly.io/Render)
- ✅ Health monitoring endpoints

### Security Considerations

⚠️ **Important to know:**

1. **Unofficial API** - Uses `pyicloud` which reverse-engineers Apple's internal APIs (may break if Apple changes their APIs)
2. **2FA Support** - Limited 2FA support; use app-specific passwords from [appleid.apple.com](https://appleid.apple.com)
3. **Credential Storage** - Apple credentials are encrypted and stored server-side (required for pyicloud to work)
4. **Third-Party Service** - You're trusting the service operator with encrypted credentials

### For Service Operators

**Production Checklist:**
- [ ] Generate unique `JWT_SECRET_KEY` (use `generate_secrets.py`)
- [ ] Generate unique `ENCRYPTION_KEY` (use `generate_secrets.py`)
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (automatic on cloud platforms)
- [ ] Configure database backups
- [ ] Set up monitoring/alerting
- [ ] Never commit `.env` files to git

## Known Limitations

1. **Apple API Dependency** - Uses unofficial `pyicloud` library (may break with Apple API changes)
2. **2FA Support** - Limited support; requires app-specific passwords
3. **Watch Input** - No reminder creation from watch (Pebble lacks keyboard)
4. **Read-Only Operations** - Can complete but not edit reminder text/dates from watch
5. **iCloud Sync Delay** - Changes may take a few seconds to sync with Apple servers

## Changelog

### Version 2.0 (Multi-Tenant)
- [x] ✅ Centralized cloud deployment architecture
- [x] ✅ Production security hardening (rate limiting, validation)
- [x] ✅ PostgreSQL support for scalability
- [x] ✅ Removed password storage from watch
- [x] ✅ Fixed backend URL (no manual configuration)
- [x] ✅ Deployment guides for Railway/Fly.io/Render/Heroku
- [x] ✅ Docker containerization

### Version 1.0 (Self-Hosted)
- [x] ✅ Pebble watch app implementation
- [x] ✅ Multi-user backend with JWT auth
- [x] ✅ Encrypted credential storage
- [x] ✅ Comprehensive test suite (31 tests)

## Future Enhancements

- [ ] 2FA flow improvement (web-based authentication)
- [ ] WebSocket support for real-time sync
- [ ] Caching layer for improved performance
- [ ] Push notifications for due reminders
- [ ] Offline mode with local sync
- [ ] Reminder creation via voice (if Pebble supports)
- [ ] Support for reminder notes and attachments

## Project Structure

```
pebble-iCloud/
├── backend/                   # Production-ready backend
│   ├── app.py                 # Flask app (v2.0: production config)
│   ├── auth_service.py        # Authentication (v2.0: env-based encryption)
│   ├── db_config.py           # Database abstraction (SQLite/PostgreSQL)
│   ├── icloud_service.py      # Legacy service (deprecated)
│   ├── generate_secrets.py    # Secret key generator for deployment
│   ├── requirements.txt       # Dependencies (v2.0: +gunicorn, psycopg2)
│   ├── Procfile               # For Railway/Heroku deployment
│   ├── Dockerfile             # Docker containerization
│   ├── railway.json           # Railway configuration
│   ├── .dockerignore          # Docker ignore rules
│   ├── .env.development       # Dev environment template
│   ├── .env.production.example # Production env template
│   ├── test_auth.py           # Auth tests (11 tests)
│   ├── test_integration.py    # Integration tests (7 tests)
│   ├── test_reminders.py      # Reminders tests (13 tests)
│   ├── pytest.ini             # Test configuration
│   ├── Makefile               # Build commands
│   └── .gitignore             # Git ignore
├── pebble-app/                # Pebble smartwatch app
│   ├── src/
│   │   ├── c/
│   │   │   └── main.c         # Watch app (v2.0: no password storage)
│   │   └── pkjs/
│   │       └── index.js       # PebbleKit JS (v2.0: fixed backend URL)
│   ├── package.json           # App manifest
│   ├── wscript                # Build config
│   └── README.md              # Pebble app docs
├── DEPLOYMENT.md              # Full deployment guide
└── README.md                  # This file
```

## Contributing

This project was built with TDD principles. When contributing:

1. Write tests first
2. Ensure all existing tests pass
3. Maintain test coverage
4. Follow the existing code style

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [pyicloud](https://github.com/picklepete/pyicloud) - Unofficial iCloud API library
- Pebble developer community
- Flask and Python ecosystem

---

**Note:** This is a proof-of-concept project. Use at your own risk. Apple does not officially support third-party access to iCloud Reminders.
