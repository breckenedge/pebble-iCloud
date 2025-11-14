# Pebble iCloud Reminders Integration

A multi-user service that enables Pebble smartwatches to access iCloud Reminders. Built using Test-Driven Development (TDD) with comprehensive test coverage.

## Features

- 🔐 **Multi-user support** with encrypted credential storage
- 🔑 **JWT-based authentication**
- ✅ **iCloud Reminders integration** (list, create, complete reminders)
- 🧪 **31 passing tests** (100% coverage of core functionality)
- 🗄️ **SQLite database** for encrypted user credentials
- 🔒 **Fernet encryption** for Apple passwords

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌──────────────────┐         ┌──────────────┐
│  Pebble Watch   │◄───────►│     Phone       │◄───────►│  Python Backend  │◄───────►│    iCloud    │
│   App (C)       │ AppMsg  │  (PebbleKit JS) │HTTP/JSON│  (Flask + Auth)  │pyicloud │  Reminders   │
└─────────────────┘         └─────────────────┘         └──────────────────┘         └──────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │ SQLite Database │
                                                         │  (Encrypted     │
                                                         │   Credentials)  │
                                                         └─────────────────┘
```

### Components

1. **Pebble Watch App** (`pebble-app/src/c/main.c`) ✅ NEW!
   - C-based native Pebble application
   - View reminder lists and reminders
   - Mark reminders as complete
   - Secure credential storage on watch

2. **PebbleKit JS** (`pebble-app/src/pkjs/index.js`) ✅ NEW!
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

### Prerequisites

**For Backend:**
- Python 3.8+
- Apple ID with app-specific password
- iCloud account with Reminders enabled

**For Pebble App:**
- Pebble watch (Aplite, Basalt, Chalk, or Diorite)
- Pebble SDK 3.x or CloudPebble account
- Pebble mobile app (iOS or Android)

### Quick Start

#### 1. Install and Run Backend

```bash
cd backend
pip install -r requirements.txt
```

Set up your computer's network IP (not localhost) for phone access:

```bash
# Find your IP address
# macOS/Linux: ifconfig | grep "inet "
# Windows: ipconfig
```

Start the backend:

```bash
python app.py
# Backend runs on http://0.0.0.0:5000
```

#### 2. Install Pebble App

See detailed instructions in `pebble-app/README.md`

**Quick Method (CloudPebble):**
1. Go to [CloudPebble](https://cloudpebble.net/)
2. Import the project from `pebble-app/`
3. Build and install to your watch

**Local Method:**
```bash
cd pebble-app
pebble build
pebble install --phone <PHONE_IP>
```

#### 3. Configure the App

1. Open Pebble mobile app
2. Go to Settings → iCloud Reminders
3. Enter:
   - Backend URL: `http://YOUR_COMPUTER_IP:5000`
   - Username: Choose a username
   - Apple ID: your.email@icloud.com
   - App-Specific Password: (generate at appleid.apple.com)
4. Save and launch the app on your watch!

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

## Security Considerations

⚠️ **Important Limitations:**

1. **Unofficial API** - Uses `pyicloud` which reverse-engineers Apple's internal APIs
2. **2FA Challenges** - Two-factor authentication requires manual intervention
3. **Credential Storage** - While encrypted, credentials are stored on your server
4. **App-Specific Passwords** - Required from iCloud settings

### Security Best Practices

- ✅ Passwords encrypted with Fernet (symmetric encryption)
- ✅ JWT tokens for stateless authentication
- ✅ Environment variables for sensitive configuration
- ✅ SQLite with parameterized queries (SQL injection protection)
- ⚠️ Change `JWT_SECRET_KEY` in production
- ⚠️ Use HTTPS in production
- ⚠️ Implement rate limiting for production use

## Known Limitations

1. **Apple API Stability** - The pyicloud library may break if Apple changes their APIs
2. **2FA Support** - Current implementation doesn't fully support 2FA workflows
3. **Server Required** - You need to host the Python backend yourself
4. **Network Access** - Phone must be able to reach the backend server
5. **No Reminder Creation on Watch** - Pebble lacks keyboard/voice input for creating reminders
6. **No Editing** - Can only mark complete, not edit reminder details on watch

## Future Enhancements

- [x] ~~Pebble watch app implementation~~ ✅ COMPLETED!
- [ ] 2FA flow improvement
- [ ] WebSocket support for real-time updates
- [ ] Caching layer for improved performance
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Push notifications for due reminders
- [ ] Offline mode with sync

## Project Structure

```
pebble-iCloud/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── auth_service.py        # Authentication module
│   ├── icloud_service.py      # Original iCloud service (deprecated)
│   ├── test_auth.py           # Auth unit tests (11 tests)
│   ├── test_integration.py    # Integration tests (7 tests)
│   ├── test_reminders.py      # Reminders tests (13 tests)
│   ├── requirements.txt       # Python dependencies
│   ├── pytest.ini             # Pytest configuration
│   ├── Makefile              # Test and build commands
│   └── .gitignore            # Git ignore rules
├── pebble-app/               # ✅ Pebble smartwatch app
│   ├── src/
│   │   ├── c/
│   │   │   └── main.c        # Main C application
│   │   └── pkjs/
│   │       └── index.js      # PebbleKit JavaScript
│   ├── package.json          # Pebble app manifest
│   ├── wscript               # Build configuration
│   └── README.md             # Pebble app documentation
└── README.md                 # This file
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
