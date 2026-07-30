import os
from core.paths import data_path


main_window = None
gui_ready = False
gui_messages_buffer = []

bot_id = None
chat_id = None
logs = None
my_nickname = None
using_sounds_in_program = None
platform = 'telegram'
vk_user_id = ''
screenshot_delay = 0.7
log_display_mode = 'all'

all_mutes = 0
all_warns = 0
all_kicks = 0

previous_sender = None
last_line_access = ''
last_line_access2 = ''
access = True

my_id = 0
put_do_logov = ""


def reload_globals_from_config():
    global platform, vk_user_id, chat_id, bot_id, logs, my_nickname
    global using_sounds_in_program, screenshot_delay, log_display_mode

    try:
        if not os.path.exists(data_path('config.yml')):
            print("[SYSTEM] config.yml не найден, используются значения по умолчанию")
            return

        with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ':' not in line:
                    continue

                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'platform':
                    platform = value if value else 'telegram'
                elif key == 'vk_user_id':
                    vk_user_id = value if value else ''
                elif key == 'chat_id':
                    chat_id = value if value else '0'
                elif key == 'bot_id':
                    bot_id = value if value else '0:default'
                elif key == 'logs':
                    logs = value if value else ''
                elif key == 'nick':
                    my_nickname = value if value else ''
                elif key == 'use_sound':
                    using_sounds_in_program = (value.lower() == 'true') if value else True
                elif key == 'screenshot_delay':
                    try:
                        screenshot_delay = float(value) if value else 0.7
                    except (ValueError, TypeError):
                        screenshot_delay = 0.7
                elif key == 'log_display_mode':
                    log_display_mode = value if value else 'all'

        global my_id, put_do_logov
        try:
            my_id = int(chat_id) if chat_id and chat_id.isdigit() else 0
        except (ValueError, TypeError):
            my_id = 0
        put_do_logov = logs if logs else ""

        print(f"[SYSTEM] Глобальные переменные перезагружены из config.yml")
        print(f"[SYSTEM] platform={platform}, vk_user_id={vk_user_id}, chat_id={chat_id}")

    except Exception as e:
        print(f"[ERROR] Ошибка перезагрузки глобальных переменных: {e}")