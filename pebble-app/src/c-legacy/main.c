#include <pebble.h>

// Message keys for communication with phone
#define KEY_CMD 0
#define KEY_ACTION 1
#define KEY_USERNAME 2
#define KEY_APPLE_ID 3
#define KEY_APPLE_PASSWORD 4
#define KEY_TOKEN 5
#define KEY_LIST_ID 6
#define KEY_LIST_TITLE 7
#define KEY_REMINDER_ID 8
#define KEY_REMINDER_TITLE 9
#define KEY_REMINDER_COMPLETED 10
#define KEY_REMINDER_INDEX 11
#define KEY_STATUS 12
#define KEY_ERROR 13
#define KEY_COUNT 14

// Commands
#define CMD_LOGIN 1
#define CMD_GET_LISTS 2
#define CMD_GET_REMINDERS 3
#define CMD_COMPLETE_REMINDER 4

// Status codes
#define STATUS_SUCCESS 1
#define STATUS_ERROR 0

// Maximum counts
#define MAX_LISTS 20
#define MAX_REMINDERS 50

// Data structures
typedef struct {
  char id[64];
  char title[64];
} ReminderList;

typedef struct {
  char id[64];
  char title[128];
  char list_id[64];
  bool completed;
} Reminder;

// Global state
static Window *s_main_window;
static MenuLayer *s_menu_layer;
static Window *s_settings_window;
static Window *s_reminders_window;
static MenuLayer *s_reminders_menu_layer;
static Window *s_detail_window;
static TextLayer *s_detail_text_layer;
static ActionBarLayer *s_action_bar;

static char s_token[256] = "";
static ReminderList s_lists[MAX_LISTS];
static int s_list_count = 0;
static Reminder s_reminders[MAX_REMINDERS];
static int s_reminder_count = 0;
static int s_current_list_index = -1;
static int s_current_reminder_index = -1;

// Settings state
static TextLayer *s_settings_text_layer;
static char s_username[64] = "";
static char s_apple_id[64] = "";
static char s_apple_password[64] = "";
static bool s_is_logged_in = false;

// Forward declarations
static void send_login_request(void);
static void send_get_lists_request(void);
static void send_get_reminders_request(const char *list_id);
static void send_complete_reminder_request(const char *list_id, const char *reminder_id);
static void show_settings_window(void);
static void show_reminders_window(void);
static void show_detail_window(int reminder_index);

// Persist keys for settings
#define PERSIST_KEY_TOKEN 1
#define PERSIST_KEY_USERNAME 2
#define PERSIST_KEY_APPLE_ID 3
#define PERSIST_KEY_APPLE_PASSWORD 4

// Load settings from persistent storage
static void load_settings(void) {
  if (persist_exists(PERSIST_KEY_TOKEN)) {
    persist_read_string(PERSIST_KEY_TOKEN, s_token, sizeof(s_token));
  }
  if (persist_exists(PERSIST_KEY_USERNAME)) {
    persist_read_string(PERSIST_KEY_USERNAME, s_username, sizeof(s_username));
  }
  if (persist_exists(PERSIST_KEY_APPLE_ID)) {
    persist_read_string(PERSIST_KEY_APPLE_ID, s_apple_id, sizeof(s_apple_id));
  }
  if (persist_exists(PERSIST_KEY_APPLE_PASSWORD)) {
    persist_read_string(PERSIST_KEY_APPLE_PASSWORD, s_apple_password, sizeof(s_apple_password));
  }

  s_is_logged_in = (strlen(s_token) > 0);
}

// Save settings to persistent storage
static void save_settings(void) {
  persist_write_string(PERSIST_KEY_TOKEN, s_token);
  persist_write_string(PERSIST_KEY_USERNAME, s_username);
  persist_write_string(PERSIST_KEY_APPLE_ID, s_apple_id);
  persist_write_string(PERSIST_KEY_APPLE_PASSWORD, s_apple_password);
}

// AppMessage callbacks
static void inbox_received_callback(DictionaryIterator *iterator, void *context) {
  Tuple *cmd_tuple = dict_find(iterator, KEY_CMD);
  if (!cmd_tuple) {
    return;
  }

  int cmd = cmd_tuple->value->int32;
  Tuple *status_tuple = dict_find(iterator, KEY_STATUS);
  int status = status_tuple ? status_tuple->value->int32 : STATUS_ERROR;

  if (status == STATUS_ERROR) {
    Tuple *error_tuple = dict_find(iterator, KEY_ERROR);
    const char *error = error_tuple ? error_tuple->value->cstring : "Unknown error";
    APP_LOG(APP_LOG_LEVEL_ERROR, "Error: %s", error);

    // Show error dialog
    static char error_message[128];
    snprintf(error_message, sizeof(error_message), "Error: %s", error);

    // Simple dialog using a window (Pebble doesn't have native dialogs)
    static Window *error_window;
    static TextLayer *error_text_layer;

    error_window = window_create();
    error_text_layer = text_layer_create(GRect(0, 50, 144, 100));
    text_layer_set_text(error_text_layer, error_message);
    text_layer_set_text_alignment(error_text_layer, GTextAlignmentCenter);
    layer_add_child(window_get_root_layer(error_window), text_layer_get_layer(error_text_layer));
    window_stack_push(error_window, true);

    return;
  }

  switch (cmd) {
    case CMD_LOGIN: {
      // Save token
      Tuple *token_tuple = dict_find(iterator, KEY_TOKEN);
      if (token_tuple) {
        snprintf(s_token, sizeof(s_token), "%s", token_tuple->value->cstring);
        s_is_logged_in = true;
        save_settings();

        // Close settings window and request lists
        window_stack_remove(s_settings_window, true);
        send_get_lists_request();
      }
      break;
    }

    case CMD_GET_LISTS: {
      // Parse lists
      Tuple *count_tuple = dict_find(iterator, KEY_COUNT);
      if (count_tuple) {
        s_list_count = count_tuple->value->int32;
        if (s_list_count > MAX_LISTS) {
          s_list_count = MAX_LISTS;
        }

        // Lists are sent in subsequent messages with KEY_REMINDER_INDEX
        menu_layer_reload_data(s_menu_layer);
      }
      break;
    }

    case CMD_GET_REMINDERS: {
      // Parse reminders
      Tuple *count_tuple = dict_find(iterator, KEY_COUNT);
      if (count_tuple) {
        s_reminder_count = count_tuple->value->int32;
        if (s_reminder_count > MAX_REMINDERS) {
          s_reminder_count = MAX_REMINDERS;
        }

        // Reminders are sent in subsequent messages
        if (s_reminders_window) {
          menu_layer_reload_data(s_reminders_menu_layer);
        }
      }
      break;
    }

    case CMD_COMPLETE_REMINDER: {
      // Reminder marked as complete
      if (status == STATUS_SUCCESS) {
        // Update local state
        if (s_current_reminder_index >= 0 && s_current_reminder_index < s_reminder_count) {
          s_reminders[s_current_reminder_index].completed = true;
        }

        // Close detail window and refresh list
        window_stack_remove(s_detail_window, true);
        menu_layer_reload_data(s_reminders_menu_layer);
      }
      break;
    }
  }

  // Check for individual list/reminder data
  Tuple *index_tuple = dict_find(iterator, KEY_REMINDER_INDEX);
  if (index_tuple) {
    int index = index_tuple->value->int32;

    // Check if this is a list or reminder
    Tuple *list_id_tuple = dict_find(iterator, KEY_LIST_ID);
    Tuple *list_title_tuple = dict_find(iterator, KEY_LIST_TITLE);
    Tuple *reminder_id_tuple = dict_find(iterator, KEY_REMINDER_ID);
    Tuple *reminder_title_tuple = dict_find(iterator, KEY_REMINDER_TITLE);
    Tuple *completed_tuple = dict_find(iterator, KEY_REMINDER_COMPLETED);

    if (list_id_tuple && list_title_tuple && index < MAX_LISTS) {
      // This is a list
      snprintf(s_lists[index].id, sizeof(s_lists[index].id), "%s", list_id_tuple->value->cstring);
      snprintf(s_lists[index].title, sizeof(s_lists[index].title), "%s", list_title_tuple->value->cstring);
      menu_layer_reload_data(s_menu_layer);
    } else if (reminder_id_tuple && reminder_title_tuple && index < MAX_REMINDERS) {
      // This is a reminder
      snprintf(s_reminders[index].id, sizeof(s_reminders[index].id), "%s", reminder_id_tuple->value->cstring);
      snprintf(s_reminders[index].title, sizeof(s_reminders[index].title), "%s", reminder_title_tuple->value->cstring);
      if (list_id_tuple) {
        snprintf(s_reminders[index].list_id, sizeof(s_reminders[index].list_id), "%s", list_id_tuple->value->cstring);
      }
      s_reminders[index].completed = completed_tuple ? completed_tuple->value->int32 : 0;

      if (s_reminders_window) {
        menu_layer_reload_data(s_reminders_menu_layer);
      }
    }
  }
}

static void inbox_dropped_callback(AppMessageResult reason, void *context) {
  APP_LOG(APP_LOG_LEVEL_ERROR, "Message dropped: %d", reason);
}

static void outbox_failed_callback(DictionaryIterator *iterator, AppMessageResult reason, void *context) {
  APP_LOG(APP_LOG_LEVEL_ERROR, "Outbox send failed: %d", reason);
}

static void outbox_sent_callback(DictionaryIterator *iterator, void *context) {
  APP_LOG(APP_LOG_LEVEL_INFO, "Outbox send success!");
}

// Send messages to phone
static void send_login_request(void) {
  DictionaryIterator *iter;
  app_message_outbox_begin(&iter);

  dict_write_int(iter, KEY_CMD, &(int){CMD_LOGIN}, sizeof(int), true);
  dict_write_cstring(iter, KEY_USERNAME, s_username);
  dict_write_cstring(iter, KEY_APPLE_ID, s_apple_id);
  dict_write_cstring(iter, KEY_APPLE_PASSWORD, s_apple_password);

  app_message_outbox_send();
}

static void send_get_lists_request(void) {
  DictionaryIterator *iter;
  app_message_outbox_begin(&iter);

  dict_write_int(iter, KEY_CMD, &(int){CMD_GET_LISTS}, sizeof(int), true);
  dict_write_cstring(iter, KEY_TOKEN, s_token);

  app_message_outbox_send();
}

static void send_get_reminders_request(const char *list_id) {
  DictionaryIterator *iter;
  app_message_outbox_begin(&iter);

  dict_write_int(iter, KEY_CMD, &(int){CMD_GET_REMINDERS}, sizeof(int), true);
  dict_write_cstring(iter, KEY_TOKEN, s_token);
  dict_write_cstring(iter, KEY_LIST_ID, list_id);

  app_message_outbox_send();
}

static void send_complete_reminder_request(const char *list_id, const char *reminder_id) {
  DictionaryIterator *iter;
  app_message_outbox_begin(&iter);

  dict_write_int(iter, KEY_CMD, &(int){CMD_COMPLETE_REMINDER}, sizeof(int), true);
  dict_write_cstring(iter, KEY_TOKEN, s_token);
  dict_write_cstring(iter, KEY_LIST_ID, list_id);
  dict_write_cstring(iter, KEY_REMINDER_ID, reminder_id);

  app_message_outbox_send();
}

// Menu callbacks for lists
static uint16_t menu_get_num_sections_callback(MenuLayer *menu_layer, void *data) {
  return 1;
}

static uint16_t menu_get_num_rows_callback(MenuLayer *menu_layer, uint16_t section_index, void *data) {
  return s_list_count;
}

static int16_t menu_get_header_height_callback(MenuLayer *menu_layer, uint16_t section_index, void *data) {
  return MENU_CELL_BASIC_HEADER_HEIGHT;
}

static void menu_draw_header_callback(GContext* ctx, const Layer *cell_layer, uint16_t section_index, void *data) {
  menu_cell_basic_header_draw(ctx, cell_layer, "Reminder Lists");
}

static void menu_draw_row_callback(GContext* ctx, const Layer *cell_layer, MenuIndex *cell_index, void *data) {
  menu_cell_basic_draw(ctx, cell_layer, s_lists[cell_index->row].title, NULL, NULL);
}

static void menu_select_callback(MenuLayer *menu_layer, MenuIndex *cell_index, void *data) {
  // Selected a list - show reminders
  s_current_list_index = cell_index->row;
  show_reminders_window();
  send_get_reminders_request(s_lists[s_current_list_index].id);
}

// Menu callbacks for reminders
static uint16_t reminders_menu_get_num_rows_callback(MenuLayer *menu_layer, uint16_t section_index, void *data) {
  return s_reminder_count;
}

static void reminders_menu_draw_header_callback(GContext* ctx, const Layer *cell_layer, uint16_t section_index, void *data) {
  if (s_current_list_index >= 0 && s_current_list_index < s_list_count) {
    menu_cell_basic_header_draw(ctx, cell_layer, s_lists[s_current_list_index].title);
  }
}

static void reminders_menu_draw_row_callback(GContext* ctx, const Layer *cell_layer, MenuIndex *cell_index, void *data) {
  const char *subtitle = s_reminders[cell_index->row].completed ? "✓ Complete" : "Incomplete";
  menu_cell_basic_draw(ctx, cell_layer, s_reminders[cell_index->row].title, subtitle, NULL);
}

static void reminders_menu_select_callback(MenuLayer *menu_layer, MenuIndex *cell_index, void *data) {
  // Selected a reminder - show detail
  s_current_reminder_index = cell_index->row;
  show_detail_window(cell_index->row);
}

// Detail window
static void action_bar_click_handler(ClickRecognizerRef recognizer, void *context) {
  // Complete button clicked
  if (s_current_reminder_index >= 0 && s_current_reminder_index < s_reminder_count) {
    if (!s_reminders[s_current_reminder_index].completed) {
      send_complete_reminder_request(
        s_reminders[s_current_reminder_index].list_id,
        s_reminders[s_current_reminder_index].id
      );
    }
  }
}

static void detail_click_config_provider(void *context) {
  window_single_click_subscribe(BUTTON_ID_SELECT, action_bar_click_handler);
}

static void detail_window_load(Window *window) {
  Layer *window_layer = window_get_root_layer(window);
  GRect bounds = layer_get_bounds(window_layer);

  // Create text layer for reminder details
  s_detail_text_layer = text_layer_create(GRect(0, 20, bounds.size.w - ACTION_BAR_WIDTH, bounds.size.h - 40));
  text_layer_set_text_alignment(s_detail_text_layer, GTextAlignmentLeft);
  text_layer_set_overflow_mode(s_detail_text_layer, GTextOverflowModeWordWrap);
  layer_add_child(window_layer, text_layer_get_layer(s_detail_text_layer));

  // Create action bar for completion
  s_action_bar = action_bar_layer_create();
  action_bar_layer_add_to_window(s_action_bar, window);
  action_bar_layer_set_click_config_provider(s_action_bar, detail_click_config_provider);
}

static void detail_window_unload(Window *window) {
  text_layer_destroy(s_detail_text_layer);
  action_bar_layer_destroy(s_action_bar);
}

static void show_detail_window(int reminder_index) {
  s_detail_window = window_create();
  window_set_window_handlers(s_detail_window, (WindowHandlers) {
    .load = detail_window_load,
    .unload = detail_window_unload,
  });

  // Set reminder text
  if (reminder_index >= 0 && reminder_index < s_reminder_count) {
    static char detail_text[256];
    snprintf(detail_text, sizeof(detail_text), "%s\n\n%s",
             s_reminders[reminder_index].title,
             s_reminders[reminder_index].completed ? "Status: Complete" : "Status: Incomplete\n\nPress SELECT to mark complete");
    text_layer_set_text(s_detail_text_layer, detail_text);
  }

  window_stack_push(s_detail_window, true);
}

// Reminders window
static void reminders_window_load(Window *window) {
  Layer *window_layer = window_get_root_layer(window);
  GRect bounds = layer_get_bounds(window_layer);

  s_reminders_menu_layer = menu_layer_create(bounds);
  menu_layer_set_callbacks(s_reminders_menu_layer, NULL, (MenuLayerCallbacks){
    .get_num_sections = menu_get_num_sections_callback,
    .get_num_rows = reminders_menu_get_num_rows_callback,
    .get_header_height = menu_get_header_height_callback,
    .draw_header = reminders_menu_draw_header_callback,
    .draw_row = reminders_menu_draw_row_callback,
    .select_click = reminders_menu_select_callback,
  });

  menu_layer_set_click_config_onto_window(s_reminders_menu_layer, window);
  layer_add_child(window_layer, menu_layer_get_layer(s_reminders_menu_layer));
}

static void reminders_window_unload(Window *window) {
  menu_layer_destroy(s_reminders_menu_layer);
  window_destroy(window);
  s_reminders_window = NULL;
}

static void show_reminders_window(void) {
  s_reminders_window = window_create();
  window_set_window_handlers(s_reminders_window, (WindowHandlers) {
    .load = reminders_window_load,
    .unload = reminders_window_unload,
  });
  window_stack_push(s_reminders_window, true);
}

// Settings window (simplified - in production use text input)
static void settings_window_load(Window *window) {
  Layer *window_layer = window_get_root_layer(window);
  GRect bounds = layer_get_bounds(window_layer);

  s_settings_text_layer = text_layer_create(GRect(0, 20, bounds.size.w, bounds.size.h - 40));
  text_layer_set_text(s_settings_text_layer, "Configure credentials\nin companion app");
  text_layer_set_text_alignment(s_settings_text_layer, GTextAlignmentCenter);
  layer_add_child(window_layer, text_layer_get_layer(s_settings_text_layer));
}

static void settings_window_unload(Window *window) {
  text_layer_destroy(s_settings_text_layer);
  window_destroy(window);
  s_settings_window = NULL;
}

static void show_settings_window(void) {
  s_settings_window = window_create();
  window_set_window_handlers(s_settings_window, (WindowHandlers) {
    .load = settings_window_load,
    .unload = settings_window_unload,
  });
  window_stack_push(s_settings_window, true);
}

// Main window
static void main_window_load(Window *window) {
  Layer *window_layer = window_get_root_layer(window);
  GRect bounds = layer_get_bounds(window_layer);

  s_menu_layer = menu_layer_create(bounds);
  menu_layer_set_callbacks(s_menu_layer, NULL, (MenuLayerCallbacks){
    .get_num_sections = menu_get_num_sections_callback,
    .get_num_rows = menu_get_num_rows_callback,
    .get_header_height = menu_get_header_height_callback,
    .draw_header = menu_draw_header_callback,
    .draw_row = menu_draw_row_callback,
    .select_click = menu_select_callback,
  });

  menu_layer_set_click_config_onto_window(s_menu_layer, window);
  layer_add_child(window_layer, menu_layer_get_layer(s_menu_layer));
}

static void main_window_unload(Window *window) {
  menu_layer_destroy(s_menu_layer);
}

static void init(void) {
  // Load settings
  load_settings();

  // Initialize AppMessage
  app_message_register_inbox_received(inbox_received_callback);
  app_message_register_inbox_dropped(inbox_dropped_callback);
  app_message_register_outbox_failed(outbox_failed_callback);
  app_message_register_outbox_sent(outbox_sent_callback);

  app_message_open(512, 512);

  // Create main window
  s_main_window = window_create();
  window_set_window_handlers(s_main_window, (WindowHandlers) {
    .load = main_window_load,
    .unload = main_window_unload
  });
  window_stack_push(s_main_window, true);

  // Check if logged in
  if (s_is_logged_in) {
    send_get_lists_request();
  } else {
    show_settings_window();
  }
}

static void deinit(void) {
  window_destroy(s_main_window);
}

int main(void) {
  init();
  app_event_loop();
  deinit();
}
