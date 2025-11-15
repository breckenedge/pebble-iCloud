// PebbleKit JS for iCloud Reminders
// Handles HTTP communication with Flask backend

// Message keys (must match C code)
var KEY_CMD = 0;
var KEY_ACTION = 1;
var KEY_USERNAME = 2;
var KEY_APPLE_ID = 3;
var KEY_APPLE_PASSWORD = 4;
var KEY_TOKEN = 5;
var KEY_LIST_ID = 6;
var KEY_LIST_TITLE = 7;
var KEY_REMINDER_ID = 8;
var KEY_REMINDER_TITLE = 9;
var KEY_REMINDER_COMPLETED = 10;
var KEY_REMINDER_INDEX = 11;
var KEY_STATUS = 12;
var KEY_ERROR = 13;
var KEY_COUNT = 14;

// Commands
var CMD_LOGIN = 1;
var CMD_GET_LISTS = 2;
var CMD_GET_REMINDERS = 3;
var CMD_COMPLETE_REMINDER = 4;

// Status codes
var STATUS_SUCCESS = 1;
var STATUS_ERROR = 0;

// Configuration - Fixed backend URL for production multi-tenant service
// TODO: Update this URL when deploying to production
var BACKEND_URL = 'https://pebble-icloud-api.up.railway.app'; // Production URL
// For local development, uncomment the line below:
// var BACKEND_URL = 'http://localhost:5000';

console.log('PebbleKit JS started');
console.log('Backend URL: ' + BACKEND_URL);

// Helper function to send error to watch
function sendError(cmd, error) {
  console.log('Sending error to watch: ' + error);
  Pebble.sendAppMessage({
    KEY_CMD: cmd,
    KEY_STATUS: STATUS_ERROR,
    KEY_ERROR: error
  }, function() {
    console.log('Error message sent successfully');
  }, function(e) {
    console.log('Failed to send error message: ' + e.error.message);
  });
}

// Helper function to send success to watch
function sendSuccess(cmd, data) {
  console.log('Sending success to watch');
  var message = {
    KEY_CMD: cmd,
    KEY_STATUS: STATUS_SUCCESS
  };

  // Add additional data
  for (var key in data) {
    if (data.hasOwnProperty(key)) {
      message[key] = data[key];
    }
  }

  Pebble.sendAppMessage(message, function() {
    console.log('Success message sent');
  }, function(e) {
    console.log('Failed to send success message: ' + e.error.message);
  });
}

// Handle login request
function handleLogin(username, appleId, applePassword) {
  console.log('Logging in user: ' + username);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', BACKEND_URL + '/api/auth/login', true);
  xhr.setRequestHeader('Content-Type', 'application/json');

  xhr.onload = function() {
    if (xhr.status === 200) {
      try {
        var response = JSON.parse(xhr.responseText);
        console.log('Login successful, token: ' + response.token);

        // Send token back to watch
        sendSuccess(CMD_LOGIN, {
          KEY_TOKEN: response.token
        });
      } catch (e) {
        sendError(CMD_LOGIN, 'Failed to parse login response');
      }
    } else if (xhr.status === 401) {
      // Try registration if login fails
      console.log('Login failed, trying registration');
      handleRegister(username, appleId, applePassword);
    } else {
      sendError(CMD_LOGIN, 'Login failed: ' + xhr.status);
    }
  };

  xhr.onerror = function() {
    sendError(CMD_LOGIN, 'Network error during login');
  };

  xhr.send(JSON.stringify({
    username: username,
    apple_id: appleId,
    apple_password: applePassword
  }));
}

// Handle registration request
function handleRegister(username, appleId, applePassword) {
  console.log('Registering user: ' + username);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', BACKEND_URL + '/api/auth/register', true);
  xhr.setRequestHeader('Content-Type', 'application/json');

  xhr.onload = function() {
    if (xhr.status === 200 || xhr.status === 201) {
      try {
        var response = JSON.parse(xhr.responseText);
        console.log('Registration successful, token: ' + response.token);

        // Send token back to watch
        sendSuccess(CMD_LOGIN, {
          KEY_TOKEN: response.token
        });
      } catch (e) {
        sendError(CMD_LOGIN, 'Failed to parse registration response');
      }
    } else {
      try {
        var error = JSON.parse(xhr.responseText);
        sendError(CMD_LOGIN, error.error || 'Registration failed');
      } catch (e) {
        sendError(CMD_LOGIN, 'Registration failed: ' + xhr.status);
      }
    }
  };

  xhr.onerror = function() {
    sendError(CMD_LOGIN, 'Network error during registration');
  };

  xhr.send(JSON.stringify({
    username: username,
    apple_id: appleId,
    apple_password: applePassword
  }));
}

// Handle get lists request
function handleGetLists(token) {
  console.log('Getting reminder lists');

  var xhr = new XMLHttpRequest();
  xhr.open('GET', BACKEND_URL + '/api/reminders/lists', true);
  xhr.setRequestHeader('Authorization', 'Bearer ' + token);

  xhr.onload = function() {
    if (xhr.status === 200) {
      try {
        var response = JSON.parse(xhr.responseText);
        var lists = response.lists || [];

        console.log('Received ' + lists.length + ' lists');

        // Send count first
        sendSuccess(CMD_GET_LISTS, {
          KEY_COUNT: lists.length
        });

        // Send each list individually
        lists.forEach(function(list, index) {
          Pebble.sendAppMessage({
            KEY_REMINDER_INDEX: index,
            KEY_LIST_ID: list.id,
            KEY_LIST_TITLE: list.title
          }, function() {
            console.log('Sent list ' + index + ': ' + list.title);
          }, function(e) {
            console.log('Failed to send list ' + index + ': ' + e.error.message);
          });
        });
      } catch (e) {
        sendError(CMD_GET_LISTS, 'Failed to parse lists response');
      }
    } else if (xhr.status === 401) {
      sendError(CMD_GET_LISTS, 'Authentication failed. Please login again.');
    } else {
      sendError(CMD_GET_LISTS, 'Failed to get lists: ' + xhr.status);
    }
  };

  xhr.onerror = function() {
    sendError(CMD_GET_LISTS, 'Network error getting lists');
  };

  xhr.send();
}

// Handle get reminders request
function handleGetReminders(token, listId) {
  console.log('Getting reminders for list: ' + listId);

  var xhr = new XMLHttpRequest();
  xhr.open('GET', BACKEND_URL + '/api/reminders/list/' + encodeURIComponent(listId), true);
  xhr.setRequestHeader('Authorization', 'Bearer ' + token);

  xhr.onload = function() {
    if (xhr.status === 200) {
      try {
        var response = JSON.parse(xhr.responseText);
        var reminders = response.reminders || [];

        console.log('Received ' + reminders.length + ' reminders');

        // Send count first
        sendSuccess(CMD_GET_REMINDERS, {
          KEY_COUNT: reminders.length
        });

        // Send each reminder individually
        reminders.forEach(function(reminder, index) {
          Pebble.sendAppMessage({
            KEY_REMINDER_INDEX: index,
            KEY_REMINDER_ID: reminder.id,
            KEY_REMINDER_TITLE: reminder.title,
            KEY_LIST_ID: listId,
            KEY_REMINDER_COMPLETED: reminder.completed ? 1 : 0
          }, function() {
            console.log('Sent reminder ' + index + ': ' + reminder.title);
          }, function(e) {
            console.log('Failed to send reminder ' + index + ': ' + e.error.message);
          });
        });
      } catch (e) {
        sendError(CMD_GET_REMINDERS, 'Failed to parse reminders response');
      }
    } else if (xhr.status === 401) {
      sendError(CMD_GET_REMINDERS, 'Authentication failed. Please login again.');
    } else {
      sendError(CMD_GET_REMINDERS, 'Failed to get reminders: ' + xhr.status);
    }
  };

  xhr.onerror = function() {
    sendError(CMD_GET_REMINDERS, 'Network error getting reminders');
  };

  xhr.send();
}

// Handle complete reminder request
function handleCompleteReminder(token, listId, reminderId) {
  console.log('Completing reminder: ' + reminderId + ' in list: ' + listId);

  var xhr = new XMLHttpRequest();
  xhr.open('POST', BACKEND_URL + '/api/reminders/' + encodeURIComponent(reminderId) + '/complete', true);
  xhr.setRequestHeader('Authorization', 'Bearer ' + token);
  xhr.setRequestHeader('Content-Type', 'application/json');

  xhr.onload = function() {
    if (xhr.status === 200) {
      console.log('Reminder completed successfully');
      sendSuccess(CMD_COMPLETE_REMINDER, {});
    } else if (xhr.status === 401) {
      sendError(CMD_COMPLETE_REMINDER, 'Authentication failed. Please login again.');
    } else {
      sendError(CMD_COMPLETE_REMINDER, 'Failed to complete reminder: ' + xhr.status);
    }
  };

  xhr.onerror = function() {
    sendError(CMD_COMPLETE_REMINDER, 'Network error completing reminder');
  };

  xhr.send(JSON.stringify({
    list_id: listId
  }));
}

// Listen for messages from the watch
Pebble.addEventListener('appmessage', function(e) {
  console.log('Received message from watch');

  var cmd = e.payload.KEY_CMD;
  console.log('Command: ' + cmd);

  switch (cmd) {
    case CMD_LOGIN:
      var username = e.payload.KEY_USERNAME;
      var appleId = e.payload.KEY_APPLE_ID;
      var applePassword = e.payload.KEY_APPLE_PASSWORD;
      handleLogin(username, appleId, applePassword);
      break;

    case CMD_GET_LISTS:
      var token = e.payload.KEY_TOKEN;
      handleGetLists(token);
      break;

    case CMD_GET_REMINDERS:
      var token = e.payload.KEY_TOKEN;
      var listId = e.payload.KEY_LIST_ID;
      handleGetReminders(token, listId);
      break;

    case CMD_COMPLETE_REMINDER:
      var token = e.payload.KEY_TOKEN;
      var listId = e.payload.KEY_LIST_ID;
      var reminderId = e.payload.KEY_REMINDER_ID;
      handleCompleteReminder(token, listId, reminderId);
      break;

    default:
      console.log('Unknown command: ' + cmd);
  }
});

// Show configuration page when settings icon is tapped
Pebble.addEventListener('showConfiguration', function() {
  console.log('Showing configuration page');

  var url = 'data:text/html,' + encodeURIComponent(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>iCloud Reminders Settings</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          margin: 0;
          padding: 20px;
          background: #f5f5f5;
        }
        .container {
          max-width: 600px;
          margin: 0 auto;
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
          margin: 0 0 20px 0;
          font-size: 24px;
          color: #333;
        }
        label {
          display: block;
          margin: 15px 0 5px 0;
          font-weight: 500;
          color: #555;
        }
        input {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
          box-sizing: border-box;
        }
        .button-group {
          display: flex;
          gap: 10px;
          margin-top: 20px;
        }
        button {
          flex: 1;
          padding: 12px;
          background: #007AFF;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
        }
        button:hover {
          background: #0051D5;
        }
        button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
        button.secondary {
          background: #6c757d;
        }
        button.secondary:hover {
          background: #5a6268;
        }
        .info {
          margin-top: 20px;
          padding: 10px;
          background: #f0f0f0;
          border-radius: 4px;
          font-size: 14px;
          color: #666;
        }
        .message {
          margin-top: 15px;
          padding: 10px;
          border-radius: 4px;
          font-size: 14px;
          display: none;
        }
        .message.success {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }
        .message.error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
        .required {
          color: #dc3545;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>iCloud Reminders Settings</h1>

        <label for="username">Username:</label>
        <input type="text" id="username" placeholder="Your username" />

        <label for="apple_password">App-Specific Password: <span class="required">*</span></label>
        <input type="password" id="apple_password" placeholder="App-specific password" required />

        <div id="message" class="message"></div>

        <div class="button-group">
          <button class="secondary" onclick="cancelSettings()">Cancel</button>
          <button id="saveBtn" onclick="saveSettings()">Save Settings</button>
        </div>

        <div class="info">
          <strong>Important:</strong>
          <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Use an app-specific password, not your regular Apple ID password</li>
            <li>Generate one at: <a href="https://appleid.apple.com" target="_blank">appleid.apple.com</a></li>
            <li>Your data is encrypted and stored securely on our servers</li>
            <li>We never store your regular Apple password, only app-specific passwords</li>
          </ul>
        </div>
      </div>

      <script>
        // Load existing settings
        var settings = JSON.parse(localStorage.getItem('pebble_icloud_settings') || '{}');
        document.getElementById('username').value = settings.username || '';
        document.getElementById('apple_id').value = settings.apple_id || '';
        document.getElementById('apple_password').value = settings.apple_password || '';

        function showMessage(message, isError) {
          var messageDiv = document.getElementById('message');
          messageDiv.textContent = message;
          messageDiv.className = 'message ' + (isError ? 'error' : 'success');
          messageDiv.style.display = 'block';
        }

        function validateUrl(url) {
          try {
            var parsed = new URL(url);
            return parsed.protocol === 'http:' || parsed.protocol === 'https:';
          } catch (e) {
            return false;
          }
        }

        function cancelSettings() {
          document.location = 'pebblekit://close#';
        }

        function saveSettings() {
          // Get values
          var backendUrl = document.getElementById('backend_url').value.trim();
          var username = document.getElementById('username').value.trim();
          var appleId = document.getElementById('apple_id').value.trim();
          var applePassword = document.getElementById('apple_password').value.trim();

          // Validate required fields
          if (!backendUrl || !username || !appleId || !applePassword) {
            showMessage('Please fill in all required fields', true);
            return;
          }

          // Validate backend URL
          if (!validateUrl(backendUrl)) {
            showMessage('Please enter a valid HTTP or HTTPS URL for the backend server', true);
            return;
          }

          // Validate Apple ID format
          if (!appleId.includes('@') || !appleId.includes('.')) {
            showMessage('Please enter a valid Apple ID (email address)', true);
            return;
          }

          // Disable buttons during processing
          var saveBtn = document.getElementById('saveBtn');
          saveBtn.disabled = true;
          saveBtn.textContent = 'Saving...';

          var settings = {
            username: document.getElementById('username').value,
            apple_id: document.getElementById('apple_id').value,
            apple_password: document.getElementById('apple_password').value
          };

          // Save to localStorage
          localStorage.setItem('pebble_icloud_settings', JSON.stringify(settings));

          // Show success message briefly before closing
          showMessage('Settings saved! Connecting to iCloud...', false);

          // Send to watch and close after a short delay
          setTimeout(function() {
            var url = 'pebblekit://close#' + encodeURIComponent(JSON.stringify(settings));
            document.location = url;
          }, 1000);
        }
      </script>
    </body>
    </html>
  `);

  Pebble.openURL(url);
});

// Handle configuration closure
Pebble.addEventListener('webviewclosed', function(e) {
  if (!e || !e.response) {
    console.log('Configuration cancelled');
    return;
  }

  try {
    var settings = JSON.parse(decodeURIComponent(e.response));
    console.log('Configuration received');

    if (settings.username && settings.apple_id && settings.apple_password) {
      // Save credentials
      localStorage.setItem('pebble_icloud_settings', JSON.stringify(settings));
      console.log('Credentials saved, initiating login...');

      // Directly initiate login (more efficient than round-trip through watch)
      handleLogin(settings.username, settings.apple_id, settings.apple_password);
    }
  } catch (e) {
    console.log('Failed to parse configuration: ' + e);
    sendError(CMD_LOGIN, 'Failed to process configuration');
  }
});

// Ready event
Pebble.addEventListener('ready', function() {
  console.log('PebbleKit JS ready!');
  console.log('Using backend: ' + BACKEND_URL);
});
