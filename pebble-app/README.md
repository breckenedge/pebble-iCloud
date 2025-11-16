# Pebble iCloud Reminders App

A Pebble smartwatch app that integrates with iCloud Reminders through a Flask backend. View and mark reminders as complete directly from your wrist!

## Features

- **Authentication**: Secure login with Apple ID credentials
- **View Reminder Lists**: Browse all your iCloud reminder lists
- **View Reminders**: See all reminders in each list
- **Mark Complete**: Mark reminders as complete with a button press
- **Persistent Login**: Credentials stored securely on watch
- **Configuration**: Easy web-based configuration through Pebble app settings

## Architecture

### Components

1. **Pebble Watch App (C)**: `src/c/main.c`
   - User interface and interaction
   - Data storage and state management
   - AppMessage communication with phone

2. **PebbleKit JS (JavaScript)**: `src/pkjs/index.js`
   - HTTP communication with Flask backend
   - Credential and settings management
   - Configuration web interface

3. **Flask Backend**: `../backend/`
   - Authentication and user management
   - iCloud API integration
   - REST API endpoints

### Communication Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Pebble    │         │   Phone     │         │   Flask     │
│   Watch     │◄───────►│  (PebbleJS) │◄───────►│   Backend   │
│    (C)      │ AppMsg  │     (JS)    │  HTTP   │   (Python)  │
└─────────────┘         └─────────────┘         └─────────────┘
```

## Prerequisites

### Required

- Pebble SDK 3.x or later
- Pebble watch (Aplite, Basalt, Chalk, or Diorite)
- Pebble mobile app on iOS or Android
- Flask backend running (see `../backend/README.md`)
- Apple ID with app-specific password

### Optional

- CloudPebble account (for online development)
- Local Pebble development environment

## Installation

### Option 1: Using CloudPebble (Recommended for Beginners)

1. Go to [CloudPebble](https://cloudpebble.net/)
2. Create a new project
3. Upload all files maintaining the directory structure:
   - `package.json`
   - `wscript`
   - `src/c/main.c`
   - `src/pkjs/index.js`
4. Build and install to your watch

### Option 2: Local Development

1. Install the Pebble SDK:
   ```bash
   # See https://developer.rebble.io/developer.pebble.com/sdk/install/index.html
   ```

2. Navigate to the pebble-app directory:
   ```bash
   cd pebble-app
   ```

3. Build the project:
   ```bash
   pebble build
   ```

4. Install to your watch:
   ```bash
   pebble install --phone <PHONE_IP>
   ```

## Configuration

### 1. Set Up the Flask Backend

First, ensure the Flask backend is running and accessible:

```bash
cd ../backend
python app.py
# Backend runs on http://localhost:5000
```

For phone access, the backend must be on the same network. Find your computer's IP:

```bash
# macOS/Linux
ifconfig | grep "inet "

# Windows
ipconfig
```

### 2. Configure the Pebble App

1. Install the app on your watch
2. Open the Pebble mobile app
3. Go to Settings → iCloud Reminders
4. Enter the following:

   - **Backend Server URL**: `http://YOUR_COMPUTER_IP:5000`
     - Example: `http://192.168.1.100:5000`
   - **Username**: Choose a username
   - **Apple ID**: Your iCloud email address
   - **App-Specific Password**: Generate at [appleid.apple.com](https://appleid.apple.com)

5. Tap "Save Settings"

### Generating an App-Specific Password

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with your Apple ID
3. Navigate to "Security" → "App-Specific Passwords"
4. Click "Generate Password"
5. Label it "Pebble iCloud"
6. Copy the generated password (format: xxxx-xxxx-xxxx-xxxx)
7. Use this in the Pebble app configuration

**Important**: Do NOT use your regular Apple ID password!

## Usage

### First Launch

1. Launch the app on your watch
2. You'll see "Configure credentials in companion app"
3. Follow the configuration steps above
4. Once configured, the app will automatically log in and display your reminder lists

### Viewing Reminder Lists

- The main screen shows all your iCloud reminder lists
- Use the UP/DOWN buttons to scroll
- Press SELECT to open a list

### Viewing Reminders

- Inside a list, you'll see all reminders
- Completed reminders show "✓ Complete"
- Incomplete reminders show "Incomplete"
- Press SELECT to view details

### Marking Reminders Complete

1. Select a reminder to view details
2. Press the SELECT button (middle button)
3. The reminder will be marked complete on iCloud
4. The list will refresh automatically

## API Communication

### Message Keys

The watch and phone communicate using AppMessage with these keys:

```c
#define KEY_CMD 0                    // Command type
#define KEY_STATUS 12                // Success/error status
#define KEY_TOKEN 5                  // JWT authentication token
#define KEY_LIST_ID 6                // Reminder list ID
#define KEY_LIST_TITLE 7             // Reminder list title
#define KEY_REMINDER_ID 8            // Reminder ID
#define KEY_REMINDER_TITLE 9         // Reminder title
#define KEY_REMINDER_COMPLETED 10    // Completion status
#define KEY_COUNT 14                 // Item count
#define KEY_ERROR 13                 // Error message
```

### Commands

1. **CMD_LOGIN (1)**: Authenticate with backend
   ```
   Watch → Phone: {CMD, USERNAME, APPLE_ID, APPLE_PASSWORD}
   Phone → Watch: {CMD, STATUS, TOKEN}
   ```

2. **CMD_GET_LISTS (2)**: Fetch reminder lists
   ```
   Watch → Phone: {CMD, TOKEN}
   Phone → Watch: {CMD, STATUS, COUNT}
   Phone → Watch: {INDEX, LIST_ID, LIST_TITLE} (for each list)
   ```

3. **CMD_GET_REMINDERS (3)**: Fetch reminders in a list
   ```
   Watch → Phone: {CMD, TOKEN, LIST_ID}
   Phone → Watch: {CMD, STATUS, COUNT}
   Phone → Watch: {INDEX, REMINDER_ID, REMINDER_TITLE, COMPLETED} (for each)
   ```

4. **CMD_COMPLETE_REMINDER (4)**: Mark reminder complete
   ```
   Watch → Phone: {CMD, TOKEN, LIST_ID, REMINDER_ID}
   Phone → Watch: {CMD, STATUS}
   ```

## Data Persistence

The app stores credentials locally on the watch using Pebble's persistent storage:

- `PERSIST_KEY_TOKEN (1)`: JWT authentication token
- `PERSIST_KEY_USERNAME (2)`: Username
- `PERSIST_KEY_APPLE_ID (3)`: Apple ID email
- `PERSIST_KEY_APPLE_PASSWORD (4)`: App-specific password

**Security Note**: Credentials are stored in Pebble's persistent storage which is accessible only to the app. However, they are not encrypted at rest on the watch. The password is only transmitted over local network to the backend.

## Troubleshooting

### "Configure credentials in companion app"

- The app hasn't been configured yet
- Open Pebble app → Settings → iCloud Reminders

### "Authentication failed. Please login again."

- JWT token expired (30-day validity)
- Go to settings and re-save configuration
- Or regenerate app-specific password

### "Network error"

- Backend server is not accessible
- Check that Flask backend is running
- Verify the backend URL in settings
- Ensure phone is on the same network as backend
- Try using computer's IP address instead of localhost

### Empty Lists or Reminders

- iCloud account may not have any reminders
- Check iCloud Reminders on iPhone/Mac to verify
- Try creating a test reminder list

### "Failed to send message"

- AppMessage buffer might be full
- Close and reopen the app
- Check phone connection to watch

## Development

### Project Structure

```
pebble-app/
├── package.json           # Pebble app manifest
├── wscript               # Build configuration
├── src/
│   ├── c/
│   │   └── main.c        # Main C application
│   └── pkjs/
│       └── index.js      # PebbleKit JavaScript
└── README.md             # This file
```

### Building from Source

```bash
# Clean build
pebble clean

# Build for all platforms
pebble build

# Build for specific platform
pebble build --platform basalt

# Install and view logs
pebble install --logs
```

### Adding Features

The app is designed to be extensible. Some ideas:

- **Add Reminders**: Implement voice dictation or pre-defined templates
- **Due Dates**: Display and filter by due dates
- **Priorities**: Show priority indicators
- **Notifications**: Push notifications for due reminders
- **Multiple Accounts**: Support switching between accounts
- **Offline Mode**: Cache reminders for offline viewing

### Code Modifications

Key areas to modify:

- **UI**: Update window creation functions in `main.c`
- **Commands**: Add new CMD_* constants and handlers
- **Backend Communication**: Modify `index.js` HTTP functions
- **Data Structures**: Update structs in `main.c`

## Limitations

1. **No Reminder Creation**: Pebble lacks keyboard/voice input for creating reminders
2. **No Editing**: Can only mark complete, not edit reminder details
3. **Network Required**: Must have phone connection and backend access
4. **Limited Display**: Small screen limits amount of text shown
5. **No Images**: Cannot display reminder attachments
6. **Polling Only**: No push notifications (must manually refresh)

## Backend API Reference

See `../README.md` for full API documentation.

Quick reference:

```
GET  /health                          # Health check endpoint
POST /api/auth/register               # Register new user
POST /api/auth/login                  # Login user
GET  /api/reminders/lists             # Get all lists (requires auth)
GET  /api/reminders/list/:id          # Get reminders in list (requires auth)
POST /api/reminders                   # Create new reminder (requires auth)
POST /api/reminders/:id/complete      # Mark complete (requires auth)
```

## License

This project is open source. Feel free to modify and distribute.

## Credits

- Built with Pebble SDK 3.x
- Uses [pyicloud](https://github.com/picklepete/pyicloud) for iCloud integration
- Flask backend with JWT authentication

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review backend logs: `cd ../backend && cat app.log`
3. Check Pebble logs: `pebble logs`
4. Verify backend is running: `curl http://localhost:5000/health`

## Version History

### v1.0.0 (2025-11-14)
- Initial release
- View reminder lists and reminders
- Mark reminders as complete
- Web-based configuration
- JWT authentication
- Multi-platform support (Aplite, Basalt, Chalk, Diorite)
