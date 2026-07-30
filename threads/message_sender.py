import os
import time as tm
from PyQt5.QtCore import QThread, pyqtSignal
import telebot
import vk_api
from vk_api import VkUpload
from vk_api.utils import get_random_id

from config import VK_TOKEN, TELEGRAM_REDIR_BOT_TOKEN, LOG_CHAT_ID
from core.paths import data_path
from core.globals import vk_user_id, chat_id, platform


class MessageSenderThread(QThread):

    finished_signal = pyqtSignal(bool, str)

    def __init__(self, send_type: str, platform: str, *args):
        super().__init__()
        self.send_type = send_type
        self.platform = platform
        self.args = args
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.isRunning():
            self.wait(2000)

    def run(self):
        try:
            if self.send_type == 'mute':
                vk_uid, user_id, full_nick, photoid, nick, reason, dating, timing = self.args
                if self.platform == 'telegram':
                    self._send_mute_telegram(user_id, full_nick, photoid, nick, reason, dating, timing)
                else:
                    self._send_mute_vk(full_nick, photoid, nick, reason, dating, timing)

            elif self.send_type == 'warn':
                vk_uid, user_id, full_nick, photoid, nick, reason, dating, timing = self.args
                if self.platform == 'telegram':
                    self._send_warn_telegram(user_id, full_nick, photoid, nick, reason, dating, timing)
                else:
                    self._send_warn_vk(full_nick, photoid, nick, reason, dating, timing)

            elif self.send_type == 'kick':
                vk_uid, user_id, full_nick, nick, reason, dating, timing = self.args
                if self.platform == 'telegram':
                    self._send_kick_telegram(user_id, full_nick, nick, reason, dating, timing)
                else:
                    self._send_kick_vk(full_nick, nick, reason, dating, timing)

            elif self.send_type == 'screenshot':
                filename = self.args[0]
                if self.platform == 'telegram':
                    self._send_screenshot_telegram(filename)
                else:
                    self._send_screenshot_vk(filename)

        except Exception as e:
            self.finished_signal.emit(False, f"[ERROR] Ошибка отправки: {e}")

    def _send_mute_telegram(self, user_id, full_nick, photoid, nick, reason, dating, timing):
        photo_path = f'./screenshot_{photoid}.png'
        for attempt in range(1, 11):
            if self.should_stop:
                return
            try:
                bot_redir = telebot.TeleBot(TELEGRAM_REDIR_BOT_TOKEN)
                bot = telebot.TeleBot(str(user_id))

                text_main = (
                    f'Ник: {nick}\n'
                    f'Тип наказания: Мут\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'<em>С любовью, NaGiNaT❤️</em>'
                )
                text_log = (
                    f'Блюститель: {full_nick}\n\n'
                    f'Ник: {nick}\n'
                    f'Тип наказания: Мут\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'<em>С любовью, NaGiNaT❤️</em>'
                )

                bot_redir.send_message(LOG_CHAT_ID, text_log, parse_mode='html')
                with open(photo_path, 'rb') as photo_file:
                    bot.send_photo(int(user_id), photo_file, text_main, parse_mode='html')

                os.remove(photo_path)
                self.finished_signal.emit(True, "[SYSTEM] Мут отправлен в Telegram")
                return
            except Exception as e:
                if attempt == 10:
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить мут в Telegram: {e}")
                else:
                    tm.sleep(1)

    def _send_warn_telegram(self, user_id, full_nick, photoid, nick, reason, dating, timing):
        photo_path = f'./screenshot_{photoid}.png'
        for attempt in range(1, 11):
            if self.should_stop:
                return
            try:
                bot_redir = telebot.TeleBot(TELEGRAM_REDIR_BOT_TOKEN)
                bot = telebot.TeleBot(str(user_id))

                text_main = (
                    f'Ник: {nick}\n'
                    f'Тип наказания: Предупреждение\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'<em>С любовью, NaGiNaT❤️</em>'
                )
                text_log = (
                    f'Блюститель: {full_nick}\n\n'
                    f'Ник: {nick}\n'
                    f'Тип наказания: Предупреждение\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'<em>С любовью, NaGiNaT❤️</em>'
                )

                bot_redir.send_message(LOG_CHAT_ID, text_log, parse_mode='html')
                with open(photo_path, 'rb') as photo_file:
                    bot.send_photo(int(user_id), photo_file, text_main, parse_mode='html')

                os.remove(photo_path)
                self.finished_signal.emit(True, "[SYSTEM] Варн отправлен в Telegram")
                return
            except Exception as e:
                if attempt == 10:
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить варн в Telegram: {e}")
                else:
                    tm.sleep(1)

    def _send_kick_telegram(self, user_id, full_nick, nick, reason, dating, timing):
        for attempt in range(1, 11):
            if self.should_stop:
                return
            try:
                bot_redir = telebot.TeleBot(TELEGRAM_REDIR_BOT_TOKEN)
                bot = telebot.TeleBot(str(user_id))

                text_main = (
                    f'Ник: {nick}\n'
                    f'Тип наказания: Кик\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'<em>С любовью, NaGiNaT❤️</em>'
                )
                text_log = (
                    f'Блюститель: {full_nick}\n\n'
                    f'Ник: {nick}\n'
                    f'Тип наказания: Кик\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'<em>С любовью, NaGiNaT❤️</em>'
                )

                bot.send_message(int(user_id), text_main, parse_mode='html')
                bot_redir.send_message(LOG_CHAT_ID, text_log, parse_mode='html')
                self.finished_signal.emit(True, "[SYSTEM] Кик отправлен в Telegram")
                return
            except Exception as e:
                if attempt == 10:
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить кик в Telegram: {e}")
                else:
                    tm.sleep(1)

    def _send_screenshot_telegram(self, filename):
        global chat_id
        for attempt in range(1, 4):
            if self.should_stop:
                return
            try:
                bot = telebot.TeleBot(str(chat_id))
                with open(filename, 'rb') as photo_file:
                    bot.send_photo(int(chat_id), photo_file, '<em>С любовью, NaGiNaT❤️</em>', parse_mode='html')
                try:
                    os.remove(filename)
                except Exception:
                    pass
                self.finished_signal.emit(True, "[SYSTEM] Скриншот отправлен в Telegram")
                return
            except Exception as e:
                if attempt == 3:
                    try:
                        os.remove(filename)
                    except Exception:
                        pass
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить скриншот в Telegram: {e}")
                else:
                    tm.sleep(2)

    def _init_vk_api(self):
        """Инициализирует VK API с токеном бота"""
        try:
            vk_session = vk_api.VkApi(token=VK_TOKEN)
            vk = vk_session.get_api()
            return vk, vk_session
        except Exception as e:
            raise Exception(f"Ошибка инициализации VK API: {e}")

    def _get_vk_user_id(self):
        """Безопасно получает vk_user_id из глобальной переменной или из config.yml"""
        global vk_user_id
        if not vk_user_id:
            try:
                if os.path.exists(data_path('config.yml')):
                    with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('vk_user_id:'):
                                vk_user_id = line.split(':', 1)[1].strip()
                                if vk_user_id:
                                    print(f"[SYSTEM] vk_user_id загружен из config.yml: {vk_user_id}")
                                break
            except Exception as e:
                print(f"[ERROR] Не удалось прочитать vk_user_id: {e}")
        return vk_user_id

    def _send_mute_vk(self, full_nick, photoid, nick, reason, dating, timing):
        photo_path = f'./screenshot_{photoid}.png'
        for attempt in range(1, 4):
            if self.should_stop:
                return
            try:
                vk, vk_session = self._init_vk_api()
                message_text = (
                    f'🛑 Мут\n\n'
                    f'Блюститель: {self._clean_html(full_nick)}\n'
                    f'Ник: {self._clean_html(nick)}\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'С любовью, NaGiNaT❤️'
                )

                upload = VkUpload(vk_session)
                photo = upload.photo_messages(photo_path)[0]
                current_vk_id = self._get_vk_user_id()

                vk.messages.send(
                    peer_id=int(current_vk_id),
                    random_id=get_random_id(),
                    message=message_text,
                    attachment=f'photo{photo["owner_id"]}_{photo["id"]}'
                )

                os.remove(photo_path)
                self.finished_signal.emit(True, "[SYSTEM] Мут отправлен во ВКонтакте")
                return
            except Exception as e:
                if attempt == 3:
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить мут во ВКонтакте: {e}")
                else:
                    tm.sleep(2)

    def _send_warn_vk(self, full_nick, photoid, nick, reason, dating, timing):
        photo_path = f'./screenshot_{photoid}.png'
        for attempt in range(1, 4):
            if self.should_stop:
                return
            try:
                vk, vk_session = self._init_vk_api()
                message_text = (
                    f'⚠️ Предупреждение\n\n'
                    f'Блюститель: {self._clean_html(full_nick)}\n'
                    f'Ник: {self._clean_html(nick)}\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'С любовью, NaGiNaT❤️'
                )

                upload = VkUpload(vk_session)
                photo = upload.photo_messages(photo_path)[0]
                current_vk_id = self._get_vk_user_id()

                vk.messages.send(
                    peer_id=int(current_vk_id),
                    random_id=get_random_id(),
                    message=message_text,
                    attachment=f'photo{photo["owner_id"]}_{photo["id"]}'
                )

                os.remove(photo_path)
                self.finished_signal.emit(True, "[SYSTEM] Варн отправлен во ВКонтакте")
                return
            except Exception as e:
                if attempt == 3:
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить варн во ВКонтакте: {e}")
                else:
                    tm.sleep(2)

    def _send_kick_vk(self, full_nick, nick, reason, dating, timing):
        for attempt in range(1, 4):
            if self.should_stop:
                return
            try:
                vk, vk_session = self._init_vk_api()
                message_text = (
                    f'👢 Кик\n\n'
                    f'Блюститель: {self._clean_html(full_nick)}\n'
                    f'Ник: {self._clean_html(nick)}\n'
                    f'Причина: {reason}\n'
                    f'Дата: {dating}\n'
                    f'Время: {timing}\n\n'
                    f'С любовью, NaGiNaT❤️'
                )

                current_vk_id = self._get_vk_user_id()
                vk.messages.send(
                    peer_id=int(current_vk_id),
                    random_id=get_random_id(),
                    message=message_text
                )

                self.finished_signal.emit(True, "[SYSTEM] Кик отправлен во ВКонтакте")
                return
            except Exception as e:
                if attempt == 3:
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить кик во ВКонтакте: {e}")
                else:
                    tm.sleep(2)

    def _send_screenshot_vk(self, filename):
        for attempt in range(1, 4):
            if self.should_stop:
                return
            try:
                vk, vk_session = self._init_vk_api()
                upload = VkUpload(vk_session)
                photo = upload.photo_messages(filename)[0]
                current_vk_id = self._get_vk_user_id()

                vk.messages.send(
                    peer_id=int(current_vk_id),
                    random_id=get_random_id(),
                    message='📸 Скриншот по запросу\nС любовью, NaGiNaT❤️',
                    attachment=f'photo{photo["owner_id"]}_{photo["id"]}'
                )

                try:
                    os.remove(filename)
                except Exception:
                    pass
                self.finished_signal.emit(True, "[SYSTEM] Скриншот отправлен во ВКонтакте")
                return
            except Exception as e:
                if attempt == 3:
                    try:
                        os.remove(filename)
                    except Exception:
                        pass
                    self.finished_signal.emit(False, f"[ERROR] Не удалось отправить скриншот во ВКонтакте: {e}")
                else:
                    tm.sleep(2)

    @staticmethod
    def _clean_html(text: str) -> str:
        import re
        return re.sub(r'<.*?>', '', text)