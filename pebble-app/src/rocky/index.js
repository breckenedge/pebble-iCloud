// Rocky.js app for iCloud Reminders
// Pure JavaScript implementation - no C code needed

var rocky = Rocky.bindCanvas(document.getElementById('pebble-canvas'));

// Message keys (must match pkjs)
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

// App state
var state = {
  view: 'lists', // 'lists', 'reminders', 'detail', 'settings', 'error'
  token: localStorage.getItem('token') || '',
  lists: [],
  reminders: [],
  currentListIndex: -1,
  currentReminderIndex: -1,
  selectedIndex: 0,
  scrollOffset: 0,
  errorMessage: '',
  isLoggedIn: false
};

// Constants
var MAX_VISIBLE_ITEMS = 5;
var ITEM_HEIGHT = 30;
var HEADER_HEIGHT = 20;

// Initialize
state.isLoggedIn = state.token.length > 0;

// Load settings from localStorage
function loadSettings() {
  var token = localStorage.getItem('token');
  if (token) {
    state.token = token;
    state.isLoggedIn = true;
  }
}

// Save settings to localStorage
function saveSettings() {
  localStorage.setItem('token', state.token);
}

// Send message to phone
function sendMessage(message) {
  Rocky.postMessage(message);
}

// Request lists from backend
function requestLists() {
  sendMessage({
    KEY_CMD: CMD_GET_LISTS,
    KEY_TOKEN: state.token
  });
}

// Request reminders for a list
function requestReminders(listId) {
  sendMessage({
    KEY_CMD: CMD_GET_REMINDERS,
    KEY_TOKEN: state.token,
    KEY_LIST_ID: listId
  });
}

// Mark reminder as complete
function completeReminder(listId, reminderId) {
  sendMessage({
    KEY_CMD: CMD_COMPLETE_REMINDER,
    KEY_TOKEN: state.token,
    KEY_LIST_ID: listId,
    KEY_REMINDER_ID: reminderId
  });
}

// Handle messages from phone
Rocky.on('message', function(event) {
  var message = event.data;
  var cmd = message.KEY_CMD;
  var status = message.KEY_STATUS;

  if (status === STATUS_ERROR) {
    state.view = 'error';
    state.errorMessage = message.KEY_ERROR || 'Unknown error';
    rocky.requestDraw();
    return;
  }

  switch (cmd) {
    case CMD_LOGIN:
      state.token = message.KEY_TOKEN;
      state.isLoggedIn = true;
      saveSettings();
      state.view = 'lists';
      requestLists();
      break;

    case CMD_GET_LISTS:
      var count = message.KEY_COUNT;
      if (count !== undefined) {
        state.lists = new Array(count);
        state.selectedIndex = 0;
        state.scrollOffset = 0;
      }
      break;

    case CMD_GET_REMINDERS:
      var count = message.KEY_COUNT;
      if (count !== undefined) {
        state.reminders = new Array(count);
        state.selectedIndex = 0;
        state.scrollOffset = 0;
      }
      break;

    case CMD_COMPLETE_REMINDER:
      // Mark reminder as completed locally
      if (state.currentReminderIndex >= 0 && state.currentReminderIndex < state.reminders.length) {
        state.reminders[state.currentReminderIndex].completed = true;
      }
      state.view = 'reminders';
      break;
  }

  // Handle individual list/reminder data
  var index = message.KEY_REMINDER_INDEX;
  if (index !== undefined) {
    if (message.KEY_LIST_ID && message.KEY_LIST_TITLE) {
      // This is a list
      state.lists[index] = {
        id: message.KEY_LIST_ID,
        title: message.KEY_LIST_TITLE
      };
    } else if (message.KEY_REMINDER_ID && message.KEY_REMINDER_TITLE) {
      // This is a reminder
      state.reminders[index] = {
        id: message.KEY_REMINDER_ID,
        title: message.KEY_REMINDER_TITLE,
        listId: message.KEY_LIST_ID,
        completed: message.KEY_REMINDER_COMPLETED === 1
      };
    }
  }

  rocky.requestDraw();
});

// Drawing functions
function drawText(ctx, text, x, y, maxWidth) {
  if (text.length * 6 > maxWidth) {
    // Truncate text if too long
    var maxChars = Math.floor(maxWidth / 6) - 3;
    text = text.substring(0, maxChars) + '...';
  }
  ctx.fillText(text, x, y);
}

function drawHeader(ctx, text, bounds) {
  ctx.fillStyle = 'black';
  ctx.fillRect(0, 0, bounds.width, HEADER_HEIGHT);
  ctx.fillStyle = 'white';
  ctx.font = '14px Gothic';
  ctx.textAlign = 'center';
  ctx.fillText(text, bounds.width / 2, 15);
}

function drawMenuItem(ctx, text, y, isSelected, bounds) {
  // Background
  if (isSelected) {
    ctx.fillStyle = 'black';
    ctx.fillRect(0, y, bounds.width, ITEM_HEIGHT);
    ctx.fillStyle = 'white';
  } else {
    ctx.fillStyle = 'black';
  }

  // Text
  ctx.font = '18px Gothic';
  ctx.textAlign = 'left';
  drawText(ctx, text, 5, y + 20, bounds.width - 10);

  // Separator
  ctx.strokeStyle = '#CCCCCC';
  ctx.beginPath();
  ctx.moveTo(0, y + ITEM_HEIGHT);
  ctx.lineTo(bounds.width, y + ITEM_HEIGHT);
  ctx.stroke();
}

function drawListsView(ctx, bounds) {
  drawHeader(ctx, 'Reminder Lists', bounds);

  var startY = HEADER_HEIGHT;
  var visibleStart = Math.floor(state.scrollOffset / ITEM_HEIGHT);
  var visibleEnd = Math.min(visibleStart + MAX_VISIBLE_ITEMS, state.lists.length);

  for (var i = visibleStart; i < visibleEnd; i++) {
    var y = startY + (i - visibleStart) * ITEM_HEIGHT;
    var list = state.lists[i];
    var title = list ? list.title : 'Loading...';
    drawMenuItem(ctx, title, y, i === state.selectedIndex, bounds);
  }

  // Draw scroll indicator if needed
  if (state.lists.length > MAX_VISIBLE_ITEMS) {
    var indicatorHeight = Math.max(20, (MAX_VISIBLE_ITEMS / state.lists.length) * bounds.height);
    var indicatorY = (state.scrollOffset / (state.lists.length * ITEM_HEIGHT)) * bounds.height;
    ctx.fillStyle = '#888888';
    ctx.fillRect(bounds.width - 3, indicatorY, 3, indicatorHeight);
  }
}

function drawRemindersView(ctx, bounds) {
  var headerText = 'Reminders';
  if (state.currentListIndex >= 0 && state.currentListIndex < state.lists.length) {
    headerText = state.lists[state.currentListIndex].title;
  }
  drawHeader(ctx, headerText, bounds);

  var startY = HEADER_HEIGHT;
  var visibleStart = Math.floor(state.scrollOffset / ITEM_HEIGHT);
  var visibleEnd = Math.min(visibleStart + MAX_VISIBLE_ITEMS, state.reminders.length);

  for (var i = visibleStart; i < visibleEnd; i++) {
    var y = startY + (i - visibleStart) * ITEM_HEIGHT;
    var reminder = state.reminders[i];
    if (reminder) {
      var title = (reminder.completed ? '✓ ' : '○ ') + reminder.title;
      drawMenuItem(ctx, title, y, i === state.selectedIndex, bounds);
    } else {
      drawMenuItem(ctx, 'Loading...', y, i === state.selectedIndex, bounds);
    }
  }

  // Draw scroll indicator if needed
  if (state.reminders.length > MAX_VISIBLE_ITEMS) {
    var indicatorHeight = Math.max(20, (MAX_VISIBLE_ITEMS / state.reminders.length) * bounds.height);
    var indicatorY = (state.scrollOffset / (state.reminders.length * ITEM_HEIGHT)) * bounds.height;
    ctx.fillStyle = '#888888';
    ctx.fillRect(bounds.width - 3, indicatorY, 3, indicatorHeight);
  }
}

function drawDetailView(ctx, bounds) {
  drawHeader(ctx, 'Reminder Details', bounds);

  var reminder = state.reminders[state.currentReminderIndex];
  if (!reminder) return;

  ctx.fillStyle = 'black';
  ctx.font = '16px Gothic';
  ctx.textAlign = 'left';

  var y = HEADER_HEIGHT + 20;
  var lines = wrapText(ctx, reminder.title, bounds.width - 10);

  for (var i = 0; i < lines.length; i++) {
    ctx.fillText(lines[i], 5, y);
    y += 20;
  }

  y += 10;
  ctx.font = '14px Gothic';
  ctx.fillText('Status: ' + (reminder.completed ? 'Complete' : 'Incomplete'), 5, y);

  if (!reminder.completed) {
    y += 30;
    ctx.fillText('Press SELECT to mark complete', 5, y);
  }
}

function drawSettingsView(ctx, bounds) {
  drawHeader(ctx, 'Settings', bounds);

  ctx.fillStyle = 'black';
  ctx.font = '16px Gothic';
  ctx.textAlign = 'center';

  var y = bounds.height / 2;
  ctx.fillText('Configure credentials', bounds.width / 2, y);
  ctx.fillText('in Pebble app settings', bounds.width / 2, y + 20);
}

function drawErrorView(ctx, bounds) {
  drawHeader(ctx, 'Error', bounds);

  ctx.fillStyle = 'black';
  ctx.font = '14px Gothic';
  ctx.textAlign = 'left';

  var y = HEADER_HEIGHT + 20;
  var lines = wrapText(ctx, state.errorMessage, bounds.width - 10);

  for (var i = 0; i < lines.length; i++) {
    ctx.fillText(lines[i], 5, y);
    y += 18;
  }

  y += 20;
  ctx.textAlign = 'center';
  ctx.fillText('Press BACK to return', bounds.width / 2, y);
}

// Helper function to wrap text
function wrapText(ctx, text, maxWidth) {
  var words = text.split(' ');
  var lines = [];
  var currentLine = '';

  for (var i = 0; i < words.length; i++) {
    var testLine = currentLine + words[i] + ' ';
    var metrics = ctx.measureText(testLine);

    if (metrics.width > maxWidth && currentLine.length > 0) {
      lines.push(currentLine.trim());
      currentLine = words[i] + ' ';
    } else {
      currentLine = testLine;
    }
  }

  if (currentLine.length > 0) {
    lines.push(currentLine.trim());
  }

  return lines;
}

// Main draw handler
rocky.update_proc = function(ctx, bounds) {
  // Clear screen
  ctx.clearRect(0, 0, bounds.width, bounds.height);
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, bounds.width, bounds.height);

  // Draw current view
  switch (state.view) {
    case 'lists':
      drawListsView(ctx, bounds);
      break;
    case 'reminders':
      drawRemindersView(ctx, bounds);
      break;
    case 'detail':
      drawDetailView(ctx, bounds);
      break;
    case 'settings':
      drawSettingsView(ctx, bounds);
      break;
    case 'error':
      drawErrorView(ctx, bounds);
      break;
  }
};

// Button handlers
rocky.on('buttonup', function(event) {
  switch (event.button) {
    case 'up':
      handleUpButton();
      break;
    case 'select':
      handleSelectButton();
      break;
    case 'down':
      handleDownButton();
      break;
    case 'back':
      handleBackButton();
      break;
  }
  rocky.requestDraw();
});

function handleUpButton() {
  if (state.view === 'lists' || state.view === 'reminders') {
    if (state.selectedIndex > 0) {
      state.selectedIndex--;
      // Scroll up if needed
      if (state.selectedIndex * ITEM_HEIGHT < state.scrollOffset) {
        state.scrollOffset = state.selectedIndex * ITEM_HEIGHT;
      }
    }
  }
}

function handleDownButton() {
  var maxIndex = 0;
  if (state.view === 'lists') {
    maxIndex = state.lists.length - 1;
  } else if (state.view === 'reminders') {
    maxIndex = state.reminders.length - 1;
  }

  if (state.selectedIndex < maxIndex) {
    state.selectedIndex++;
    // Scroll down if needed
    var visibleBottom = state.scrollOffset + (MAX_VISIBLE_ITEMS * ITEM_HEIGHT);
    if ((state.selectedIndex + 1) * ITEM_HEIGHT > visibleBottom) {
      state.scrollOffset = (state.selectedIndex - MAX_VISIBLE_ITEMS + 1) * ITEM_HEIGHT;
    }
  }
}

function handleSelectButton() {
  switch (state.view) {
    case 'lists':
      // Navigate to reminders for selected list
      state.currentListIndex = state.selectedIndex;
      if (state.lists[state.currentListIndex]) {
        state.view = 'reminders';
        state.selectedIndex = 0;
        state.scrollOffset = 0;
        requestReminders(state.lists[state.currentListIndex].id);
      }
      break;

    case 'reminders':
      // Navigate to detail view for selected reminder
      state.currentReminderIndex = state.selectedIndex;
      if (state.reminders[state.currentReminderIndex]) {
        state.view = 'detail';
      }
      break;

    case 'detail':
      // Mark reminder as complete
      var reminder = state.reminders[state.currentReminderIndex];
      if (reminder && !reminder.completed) {
        completeReminder(reminder.listId, reminder.id);
      }
      break;

    case 'settings':
      // Open settings (handled by pkjs)
      break;

    case 'error':
      // Return to previous view
      state.view = state.isLoggedIn ? 'lists' : 'settings';
      break;
  }
}

function handleBackButton() {
  switch (state.view) {
    case 'reminders':
      state.view = 'lists';
      state.selectedIndex = state.currentListIndex;
      break;

    case 'detail':
      state.view = 'reminders';
      state.selectedIndex = state.currentReminderIndex;
      break;

    case 'error':
      state.view = state.isLoggedIn ? 'lists' : 'settings';
      break;

    default:
      // Already at top level
      break;
  }
}

// Initialize app
loadSettings();

if (state.isLoggedIn) {
  requestLists();
} else {
  state.view = 'settings';
}

rocky.requestDraw();
