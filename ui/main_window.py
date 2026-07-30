import os
import re
import sys
import subprocess
import datetime
import threading
import random
import time as tm
import pyautogui as pag
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMenu, QAction
)
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QMouseEvent, QIcon
from tzlocal import get_localzone

from ui.base_window import BaseWindow
from core.paths import data_path
from core.helpers import gui_print, make_sound, pressing_key, add_timezone_to_str
from core.globals import (
    main_window, gui_messages_buffer, platform, vk_user_id,
    bot_id, chat_id, logs, my_nickname, using_sounds_in_program,
    screenshot_delay, log_display_mode, put_do_logov,
    all_mutes, all_warns, all_kicks, previous_sender, my_id
)
from config import VK_TOKEN, TELEGRAM_REDIR_BOT_TOKEN, LOG_CHAT_ID, VERSION

from threads.log_monitor import LogMonitorThread
from threads.message_sender import MessageSenderThread
from threads.action_threads import (
    MuteActionsThread, WarnActionsThread, KickActionsThread, ScreenshotThread
)
from threads.update_downloader import UpdateDownloaderThread
from updater import check_for_update


class MainWindow(BaseWindow):
    sound_requested = pyqtSignal()
    screenshot_complete = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'path', 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            gui_print(f"[ERROR] Не удалось установить иконку для MainWindow: {e}")

        self.themes = {
            "Dark Orange": {"primary": "#FF7F50", "primary_hover": "#FF9D7A", "primary_pressed": "#E67A5D", "background": "#2B2C34", "secondary": "#45475A", "secondary_hover": "#585B70", "text": "#CDD6F4", "text_secondary": "#A6ADC8", "accent": "#94E2D5", "error": "#F38BA8", "warning": "#F9E2AF", "success": "#A6E3A1", "chat": "#CDD6F4"},
            "Dark Blue": {"primary": "#89B4FA", "primary_hover": "#A6C8FF", "primary_pressed": "#74A7F7", "background": "#1E1E2E", "secondary": "#313244", "secondary_hover": "#45475A", "text": "#CDD6F4", "text_secondary": "#A6ADC8", "accent": "#74C7EC", "error": "#F38BA8", "warning": "#F9E2AF", "success": "#A6E3A1", "chat": "#CDD6F4"},
            "Light White": {"primary": "#2563EB", "primary_hover": "#3B82F6", "primary_pressed": "#1D4ED8", "background": "#FFFFFF", "secondary": "#F8FAFC", "secondary_hover": "#F1F5F9", "text": "#1E293B", "text_secondary": "#475569", "accent": "#0369A1", "error": "#DC2626", "warning": "#EA580C", "success": "#16A34A", "chat": "#1E293B"},
            "Purple": {"primary": "#CBA6F7", "primary_hover": "#D9BBF9", "primary_pressed": "#BB90F4", "background": "#1A1B26", "secondary": "#343B58", "secondary_hover": "#444B73", "text": "#C0CAF5", "text_secondary": "#A9B1D6", "accent": "#7AA2F7", "error": "#F7768E", "warning": "#E0AF68", "success": "#9ECE6A", "chat": "#C0CAF5"}
        }

        self.setGeometry(100, 100, 1000, 800)
        self.current_theme = self._load_theme()
        self.setStyleSheet(self._get_theme_stylesheet())

        self.operation_queue = []
        self.current_operation = None
        self.operation_lock = threading.Lock()
        self.processing_delay = 1.5

        self.session_start_time = datetime.datetime.now()
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        self.session_timer.start(1000)

        self.filter_new_messages = (log_display_mode == 'chat')

        self.current_bind_keycode = None
        self.setting_bind_mode = False
        self.keyboard_listener = None

        self._init_ui()
        self._flush_message_buffer()

        self.sound_requested.connect(self._play_sound)
        self.screenshot_complete.connect(self.log_message)

        self._load_bind()
        self._apply_theme(self.current_theme)
        self._load_platform()
        self._check_update_and_show_button()

        self.logs_path = put_do_logov
        self.log_monitor = LogMonitorThread(self.logs_path)
        self.log_monitor.update_signal.connect(self.log_message)
        self.log_monitor.log_line_signal.connect(self.process_log_line)

    def _load_theme(self):
        try:
            with open(data_path('theme.txt'), 'r') as f:
                t = f.read().strip()
                if t in self.themes:
                    return t
        except FileNotFoundError:
            pass
        return "Dark Orange"

    def _save_theme(self, tn):
        try:
            with open(data_path('theme.txt'), 'w') as f:
                f.write(tn)
        except Exception as e:
            gui_print(f"[ERROR] Ошибка сохранения темы: {e}")

    def _get_theme_stylesheet(self):
        t = self.themes.get(self.current_theme, self.themes["Dark Orange"])
        return f"""
        QWidget {{ background-color: {t['background']}; color: {t['text']}; font-family: 'Segoe UI', Arial; }}
        QTextEdit {{ background-color: {t['secondary']}; color: {t['text']}; border: 1px solid {t['secondary_hover']}; border-radius: 5px; padding: 10px; font-family: 'Cascadia Code', 'Courier New', monospace; font-size: 12px; selection-background-color: {t['primary']}; }}
        QLabel {{ color: {t['text']}; padding: 5px; }}
        QPushButton {{ background-color: {t['primary']}; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-size: 14px; font-weight: bold; }}
        QPushButton:hover {{ background-color: {t['primary_hover']}; }}
        QPushButton:pressed {{ background-color: {t['primary_pressed']}; }}
        QPushButton:disabled {{ background-color: {t['secondary']}; color: {t['text_secondary']}; }}
        QMenu {{ background-color: {t['background']}; color: {t['text']}; border: 1px solid {t['secondary_hover']}; }}
        QMenu::item:selected {{ background-color: {t['primary']}; }}
        """

    def _show_theme_menu(self):
        m = QMenu(self)
        m.setStyleSheet(self._get_theme_stylesheet())
        for tn in self.themes:
            a = QAction(tn, self)
            a.triggered.connect(lambda checked, n=tn: self._apply_theme(n))
            m.addAction(a)
        m.exec_(self.theme_btn.mapToGlobal(self.theme_btn.rect().bottomLeft()))

    def _apply_theme(self, tn):
        if tn not in self.themes:
            return
        self.current_theme = tn
        self.setStyleSheet(self._get_theme_stylesheet())
        self._update_theme_specific_styles()
        self._update_log_mode_btn_style()
        self._recolor_existing_messages()
        self._save_theme(tn)
        gui_print(f"[SYSTEM] Тема изменена на: {tn}")

    def _update_theme_specific_styles(self):
        t = self.themes[self.current_theme]
        self.title_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {t['text']}; background: transparent; padding: 0px; margin: 0px;")
        self.log_mode_btn.setStyleSheet(f"QPushButton {{ background-color: {t['secondary']}; color: {t['text']}; border: none; border-radius: 2px; padding: 4px 8px; font-size: 11px; margin: 0px; }} QPushButton:hover {{ background-color: {t['secondary_hover']}; }} QPushButton:pressed {{ background-color: {t['secondary']}; }}")
        self.theme_btn.setStyleSheet(f"QPushButton {{ background-color: {t['secondary']}; color: {t['text']}; border: none; border-radius: 2px; padding: 4px 8px; font-size: 11px; margin: 0px; }} QPushButton:hover {{ background-color: {t['secondary_hover']}; }} QPushButton:pressed {{ background-color: {t['secondary']}; }}")
        self.update_btn.setStyleSheet(f"QPushButton {{ background-color: {t['primary']}; color: white; border: none; border-radius: 2px; padding: 4px 8px; font-size: 11px; margin: 0px; }} QPushButton:hover {{ background-color: {t['primary_hover']}; }} QPushButton:pressed {{ background-color: {t['primary_pressed']}; }}")
        wb = f"QPushButton {{ background-color: transparent; color: {t['text']}; border: none; font-size: 16px; font-weight: normal; padding: 0px; margin: 0px; }} QPushButton:hover {{ background-color: {t['secondary_hover']}; }} QPushButton:pressed {{ background-color: {t['secondary']}; }}"
        cb = f"QPushButton {{ background-color: transparent; color: {t['text']}; border: none; font-size: 16px; font-weight: normal; padding: 0px; margin: 0px; }} QPushButton:hover {{ background-color: #FF4757; color: white; }} QPushButton:pressed {{ background-color: #FF3742; }}"
        self.minimize_btn.setStyleSheet(wb)
        self.maximize_btn.setStyleSheet(wb)
        self.close_btn.setStyleSheet(cb)
        self.bind_label.setStyleSheet(f"font-size: 14px; color: {t['primary']}; padding: 8px; background-color: {t['secondary']}; border-radius: 5px; border: 1px solid {t['secondary_hover']};")
        ss = f"font-size: 14px; background-color: {t['secondary']}; padding: 10px; border-radius: 5px; border: 1px solid {t['secondary_hover']}; color: {t['text']};"
        self.mutes_label.setStyleSheet(ss)
        self.warns_label.setStyleSheet(ss)
        self.kicks_label.setStyleSheet(ss)
        self.session_timer_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {t['accent']}; background-color: {t['secondary']}; padding: 8px 12px; border-radius: 8px; border: 1px solid {t['secondary_hover']}; min-width: 120px;")
        self.log_output.setStyleSheet(f"QTextEdit {{ background-color: {t['secondary']}; color: {t['text']}; border: 1px solid {t['secondary_hover']}; border-radius: 5px; padding: 10px; font-family: 'Cascadia Code', 'Courier New', monospace; font-size: 12px; selection-background-color: {t['primary']}; }} QScrollBar:vertical {{ border: none; background: {t['secondary']}; width: 12px; margin: 0px; }} QScrollBar::handle:vertical {{ background: {t['secondary_hover']}; border-radius: 6px; min-height: 30px; }} QScrollBar::handle:vertical:hover {{ background: {t['primary']}; }} QScrollBar::handle:vertical:pressed {{ background: {t['primary_pressed']}; }}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        theme = self.themes[self.current_theme]
        painter.setBrush(QBrush(QColor(theme['background'])))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRect(2, 2, self.width()-4, self.height()-4), 8, 8)
        painter.setBrush(QBrush(QColor(theme['secondary'])))
        painter.drawRect(QRect(2, 2, self.width()-4, 35))
        painter.setPen(QPen(QColor(theme['secondary_hover']), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRect(1, 1, self.width()-2, self.height()-2), 8, 8)

    def _load_platform(self):
        global platform, vk_user_id
        try:
            if os.path.exists(data_path('config.yml')):
                with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('platform:'):
                            platform = line.split(':', 1)[1].strip()
                        elif line.startswith('vk_user_id:'):
                            vk_user_id = line.split(':', 1)[1].strip()
        except Exception as e:
            gui_print(f"[ERROR] Ошибка загрузки платформы: {e}")

    def _check_update_and_show_button(self):
        has_update, new_version, download_url = check_for_update()
        if has_update and download_url:
            self.update_btn.setVisible(True)
            self.update_btn.setText(f"v{new_version}")
            self._update_download_url = download_url
            gui_print(f"[SYSTEM] Доступна новая версия: {new_version}")
        else:
            self.update_btn.setVisible(False)

    def _start_update_download(self):
        if not hasattr(self, '_update_download_url') or not self._update_download_url:
            gui_print("[ERROR] Ссылка для скачивания не найдена")
            return
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Скачивание...")
        self.download_thread = UpdateDownloaderThread(self._update_download_url)
        self.download_thread.progress.connect(self._on_update_progress)
        self.download_thread.finished.connect(self._on_update_downloaded)
        self.download_thread.start()

    def _on_update_progress(self, percent):
        self.update_btn.setText(f"Загрузка {percent}%")

    def _on_update_downloaded(self, success, filepath_or_error):
        if success:
            gui_print(f"[SYSTEM] Обновление скачано")
            self._restart_with_update(filepath_or_error)
        else:
            gui_print(f"[ERROR] Ошибка скачивания обновления: {filepath_or_error}")
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Ошибка")

    def _restart_with_update(self, new_exe_path):
        if not getattr(sys, 'frozen', False):
            gui_print("[WARNING] Автообновление работает только в .exe")
            gui_print(f"[INFO] Новый файл скачан: {new_exe_path}")
            return

        current_exe = sys.executable
        current_dir = os.path.dirname(current_exe)
        final_exe = os.path.join(current_dir, 'HelperTool.exe')

        bat_path = os.path.join(os.environ.get('TEMP', current_dir), 'helpertool_update.bat')

        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f'''@echo off
chcp 65001 >nul
echo Обновление HelperTool...
echo Закрытие старой версии...
taskkill /f /im HelperTool.exe >nul 2>&1
timeout /t 3 /nobreak >nul
echo Установка обновления...
:retry
move /Y "{new_exe_path}" "{final_exe}"
if exist "{new_exe_path}" (
    echo Файл занят, повтор...
    timeout /t 2 /nobreak >nul
    goto retry
)
echo Запуск...
explorer.exe "{final_exe}"
del "%~f0"
''')

        subprocess.Popen(
            ['cmd', '/c', bat_path],
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )

        os._exit(0)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        title_bar_widget = QWidget()
        title_bar_widget.setFixedHeight(35)
        title_bar_layout = QHBoxLayout(title_bar_widget)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)
        title_bar_layout.setSpacing(5)

        self.title_label = QLabel(f"HelperTool v{VERSION} - Панель управления")
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()

        self.log_mode_btn = QPushButton()
        self.log_mode_btn.setFixedSize(85, 24)
        self.log_mode_btn.setToolTip("Переключить режим отображения логов")
        self.log_mode_btn.clicked.connect(self._toggle_log_display_mode)
        title_bar_layout.addWidget(self.log_mode_btn)

        self.theme_btn = QPushButton("Тема")
        self.theme_btn.setFixedSize(70, 24)
        self.theme_btn.setToolTip("Сменить тему")
        self.theme_btn.clicked.connect(self._show_theme_menu)
        title_bar_layout.addWidget(self.theme_btn)

        self.update_btn = QPushButton("Обновление")
        self.update_btn.setFixedSize(100, 24)
        self.update_btn.setToolTip("Скачать новую версию")
        self.update_btn.setVisible(False)
        self.update_btn.clicked.connect(self._start_update_download)
        title_bar_layout.addWidget(self.update_btn)

        self.minimize_btn = QPushButton("_")
        self.minimize_btn.setFixedSize(30, 20)
        self.minimize_btn.setToolTip("Свернуть")
        self.minimize_btn.clicked.connect(self.showMinimized)

        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 20)
        self.maximize_btn.setToolTip("Развернуть")
        self.maximize_btn.clicked.connect(lambda: self.toggle_maximize(self.maximize_btn))

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 20)
        self.close_btn.setToolTip("Закрыть")
        self.close_btn.clicked.connect(self.close)

        title_bar_layout.addWidget(self.minimize_btn)
        title_bar_layout.addWidget(self.maximize_btn)
        title_bar_layout.addWidget(self.close_btn)
        main_layout.addWidget(title_bar_widget)

        top_panel_layout = QHBoxLayout()
        stats_layout = QHBoxLayout()
        self.mutes_label = QLabel("Муты: 0")
        self.warns_label = QLabel("Варны: 0")
        self.kicks_label = QLabel("Кики: 0")
        for l in [self.mutes_label, self.warns_label, self.kicks_label]:
            stats_layout.addWidget(l)
        top_panel_layout.addLayout(stats_layout)
        top_panel_layout.addStretch()
        self.session_timer_label = QLabel("Сессия: 00:00")
        self.session_timer_label.setAlignment(Qt.AlignCenter)
        top_panel_layout.addWidget(self.session_timer_label)
        content_layout.addLayout(top_panel_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        content_layout.addWidget(self.log_output)

        buttons_layout = QHBoxLayout()
        self.bind_btn = QPushButton("Изменить бинд скриншота")
        self.bind_btn.clicked.connect(self._start_binding)
        buttons_layout.addWidget(self.bind_btn)
        self.clear_btn = QPushButton("Очистить логи")
        self.clear_btn.clicked.connect(self._clear_logs)
        buttons_layout.addWidget(self.clear_btn)
        content_layout.addLayout(buttons_layout)

        self.bind_label = QLabel("Текущий бинд: Не задан")
        content_layout.addWidget(self.bind_label)

        main_layout.addWidget(content_widget)

        self.allowed_keys = (
            list(range(Qt.Key_A, Qt.Key_Z + 1)) + list(range(Qt.Key_0, Qt.Key_9 + 1)) + list(range(Qt.Key_F1, Qt.Key_F24 + 1)) +
            [Qt.Key_Insert, Qt.Key_Delete, Qt.Key_Home, Qt.Key_End, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Print, Qt.Key_Pause,
             Qt.Key_Escape, Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt,
             Qt.Key_Meta, Qt.Key_AltGr, Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab, Qt.Key_Backspace,
             Qt.Key_CapsLock, Qt.Key_NumLock, Qt.Key_ScrollLock, Qt.Key_Menu, Qt.Key_Backtab, Qt.Key_QuoteLeft,
             Qt.Key_Backslash, Qt.Key_BracketLeft, Qt.Key_BracketRight, Qt.Key_Semicolon, Qt.Key_Apostrophe, Qt.Key_Comma,
             Qt.Key_Period, Qt.Key_Slash, Qt.Key_Equal, Qt.Key_Minus, Qt.Key_AsciiTilde, Qt.Key_Exclam, Qt.Key_At,
             Qt.Key_NumberSign, Qt.Key_Dollar, Qt.Key_Percent, Qt.Key_Ampersand, Qt.Key_Asterisk, Qt.Key_Plus, Qt.Key_Less,
             Qt.Key_Greater, Qt.Key_Underscore, Qt.Key_Question, Qt.Key_ParenLeft, Qt.Key_ParenRight]
        )
        self._update_log_mode_btn_style()

    def setup_initial_display(self):
        global log_display_mode
        self.filter_new_messages = (log_display_mode == 'chat')
        self._update_log_mode_btn_style()
        self.log_message(f"[SYSTEM] Режим отображения новых логов: {'Только чат' if self.filter_new_messages else 'Все логи'}")

    def _flush_message_buffer(self):
        global gui_messages_buffer
        for m in gui_messages_buffer:
            self.log_message(m)
        gui_messages_buffer.clear()

    def update_stats(self):
        self.mutes_label.setText(f"Муты: {all_mutes}")
        self.warns_label.setText(f"Варны: {all_warns}")
        self.kicks_label.setText(f"Кики: {all_kicks}")

    def _update_session_timer(self):
        elapsed = datetime.datetime.now() - self.session_start_time
        ts = int(elapsed.total_seconds())
        d, h = ts // 86400, (ts % 86400) // 3600
        m, s = (ts % 3600) // 60, ts % 60
        if d > 0:
            self.session_timer_label.setText(f"Сессия: {d:02d}:{h:02d}:{m:02d}:{s:02d}")
        elif h > 0:
            self.session_timer_label.setText(f"Сессия: {h:02d}:{m:02d}:{s:02d}")
        else:
            self.session_timer_label.setText(f"Сессия: {m:02d}:{s:02d}")

    def _clear_logs(self):
        self.log_output.clear()

    def _toggle_log_display_mode(self):
        global log_display_mode
        log_display_mode = 'chat' if log_display_mode == 'all' else 'all'
        self.filter_new_messages = (log_display_mode == 'chat')
        self._update_log_mode_btn_style()
        self._save_log_display_mode()
        gui_print(f"[SYSTEM] Режим логов: {'Только чат' if self.filter_new_messages else 'Все логи'}")

    def _update_log_mode_btn_style(self):
        if hasattr(self, 'log_mode_btn'):
            self.log_mode_btn.setText("Все логи" if log_display_mode == 'all' else "Только чат")

    def _save_log_display_mode(self):
        global log_display_mode
        try:
            cl = []
            if os.path.exists(data_path('config.yml')):
                with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
                    cl = f.readlines()
            found = False
            for i, l in enumerate(cl):
                if l.strip().startswith('log_display_mode:'):
                    cl[i] = f"log_display_mode: {log_display_mode}\n"
                    found = True
                    break
            if not found:
                if cl and not cl[-1].endswith('\n'):
                    cl[-1] += '\n'
                cl.append(f"log_display_mode: {log_display_mode}\n")
            with open(data_path('config.yml'), 'w', encoding='utf-8', newline='\n') as f:
                for l in cl:
                    if l and not l.endswith('\n'):
                        l += '\n'
                    f.write(l)
        except Exception as e:
            gui_print(f"[ERROR] Ошибка сохранения режима отображения: {e}")

    def log_message(self, message):
        if not isinstance(message, str):
            message = str(message)
        if self.filter_new_messages:
            if not any(t in message for t in ['[SYSTEM]', '[ERROR]', '[WARNING]', '[CHAT]']):
                if '[CHAT]' not in message:
                    return
        t = self.themes[self.current_theme]
        if self.current_theme == "Light White":
            if "[ERROR]" in message:
                cm = f'<span style="color: {t["error"]}; font-weight: bold;">{message}</span>'
            elif "[WARNING]" in message:
                cm = f'<span style="color: {t["warning"]}; font-weight: bold;">{message}</span>'
            elif "[SYSTEM]" in message:
                cm = f'<span style="color: {t["accent"]}; font-weight: bold;">{message}</span>'
            elif "[CHAT]" in message:
                cm = f'<span style="color: {t["chat"]}; font-weight: bold;">{message}</span>'
            else:
                cm = f'<span style="color: {t["text"]};">{message}</span>'
        else:
            if "[ERROR]" in message:
                cm = f'<span style="color: {t["error"]}; font-weight: bold;">{message}</span>'
            elif "[WARNING]" in message:
                cm = f'<span style="color: {t["warning"]}; font-weight: bold;">{message}</span>'
            elif "[SYSTEM]" in message:
                cm = f'<span style="color: {t["accent"]}; font-weight: bold;">{message}</span>'
            elif "[CHAT]" in message:
                cm = f'<span style="color: {t["chat"]}; font-weight: bold; text-shadow: 0 0 2px rgba(255,255,255,0.3);">{message}</span>'
            else:
                cm = f'<span style="color: {t["text"]};">{message}</span>'
        sb = self.log_output.verticalScrollBar()
        was_bottom = sb.value() == sb.maximum()
        self.log_output.append(cm)
        if was_bottom:
            sb.setValue(sb.maximum())

    def _recolor_existing_messages(self):
        if not self.log_output.toPlainText():
            return
        sb = self.log_output.verticalScrollBar()
        cp = sb.value()
        at_bottom = sb.value() == sb.maximum()
        pt = self.log_output.toPlainText()
        self.log_output.clear()
        t = self.themes[self.current_theme]
        for line in pt.split('\n'):
            if not line.strip():
                continue
            if self.current_theme == "Light White":
                if "[ERROR]" in line:
                    cm = f'<span style="color: {t["error"]}; font-weight: bold;">{line}</span>'
                elif "[WARNING]" in line:
                    cm = f'<span style="color: {t["warning"]}; font-weight: bold;">{line}</span>'
                elif "[SYSTEM]" in line:
                    cm = f'<span style="color: {t["accent"]}; font-weight: bold;">{line}</span>'
                elif "[CHAT]" in line:
                    cm = f'<span style="color: {t["chat"]}; font-weight: bold;">{line}</span>'
                else:
                    cm = f'<span style="color: {t["text"]};">{line}</span>'
            else:
                if "[ERROR]" in line:
                    cm = f'<span style="color: {t["error"]}; font-weight: bold;">{line}</span>'
                elif "[WARNING]" in line:
                    cm = f'<span style="color: {t["warning"]}; font-weight: bold;">{line}</span>'
                elif "[SYSTEM]" in line:
                    cm = f'<span style="color: {t["accent"]}; font-weight: bold;">{line}</span>'
                elif "[CHAT]" in line:
                    cm = f'<span style="color: {t["chat"]}; font-weight: bold; text-shadow: 0 0 2px rgba(255,255,255,0.3);">{line}</span>'
                else:
                    cm = f'<span style="color: {t["text"]};">{line}</span>'
            self.log_output.append(cm)
        if at_bottom:
            sb.setValue(sb.maximum())
        else:
            sb.setValue(cp)

    def process_log_line(self, line):
        global previous_sender, my_nickname
        if previous_sender == line:
            return
        if not self.filter_new_messages or '[CHAT]' in line:
            self.log_message(line)
        try:
            escaped_nick = re.escape(my_nickname)

            tag_tail = r'\S*(?:\s+\S+)*'

            mute_pattern = (
                r'㰳\s+(\S+)\s+(\S+)\s+(' + escaped_nick + r')' + tag_tail +
                r'\s+замутил\s+игрока\s+(\S+)(?:\s+┃\s+(\S+))?.*причине:\s+(.+)'
            )
            mute_match = re.search(mute_pattern, line)
            if mute_match:
                temp_nick = mute_match.group(4) + ' ┃ ' + '<code>' + mute_match.group(5) + '</code>' if mute_match.group(5) else '<code>' + mute_match.group(4) + '</code>'
                my_full_nickname = mute_match.group(1) + ' ' + mute_match.group(2) + ' ' + '<code>' + mute_match.group(3) + '</code>'
                previous_sender = line
                self._add_to_queue('mute', {'line': line, 'my_full_nickname': my_full_nickname, 'temp_nick': temp_nick, 'warns': mute_match.group(6)})
                return

            warn_pattern = (
                r'(\S+)\s+(\S+)\s+(' + escaped_nick + r')' + tag_tail +
                r'\s+предупредил\s+игрока\s+(\S+)(?:\s+┃\s+(\S+))?.*причине:\s+(.+)'
            )
            warn_match = re.search(warn_pattern, line)
            if warn_match:
                tempo_nick = (warn_match.group(5)).rstrip(".") if warn_match.group(5) else (warn_match.group(4)).rstrip(".")
                temp_nick = warn_match.group(4) + ' ┃ ' + '<code>' + tempo_nick + '</code>' if warn_match.group(5) else '<code>' + tempo_nick + '</code>'
                my_full_nickname = warn_match.group(1) + ' ' + warn_match.group(2) + ' ' + '<code>' + warn_match.group(3) + '</code>'
                previous_sender = line
                self._add_to_queue('warn', {'line': line, 'my_full_nickname': my_full_nickname, 'temp_nick': temp_nick, 'warns': warn_match.group(6)})
                return

            kick_pattern = (
                r'㰳\s+(\S+)\s+(\S+)\s+(' + escaped_nick + r')' + tag_tail +
                r'\s+кикнул\s+игрока\s+(\S+)(?:\s+┃\s+(\S+))?.*причине:\s+(.+)'
            )
            kick_match = re.search(kick_pattern, line)
            if kick_match:
                temp_nick = kick_match.group(4) + ' ┃ ' + '<code>' + kick_match.group(5) + '</code>' if kick_match.group(5) else '<code>' + kick_match.group(4) + '</code>'
                my_full_nickname = kick_match.group(1) + ' ' + kick_match.group(2) + ' ' + '<code>' + kick_match.group(3) + '</code>'
                previous_sender = line
                current_date = datetime.datetime.now(get_localzone()).strftime("%d.%m.%Y")
                time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})', line)
                timesi = time_match.group(1) if time_match else "00:00:00"
                last_time = add_timezone_to_str(timesi)
                self._add_to_queue('kick', {'my_full_nickname': my_full_nickname, 'temp_nick': temp_nick, 'warns': kick_match.group(6), 'current_date': current_date, 'last_time': last_time})
                return
        except Exception as e:
            self.log_message(f"[ERROR] Ошибка при обработке строки '{line}': {e}")

    def _add_to_queue(self, ot, data):
        with self.operation_lock:
            self.operation_queue.append({'type': ot, 'data': data, 'timestamp': datetime.datetime.now()})
        if self.current_operation is None:
            self._process_next_operation()

    def _process_next_operation(self):
        with self.operation_lock:
            if not self.operation_queue or self.current_operation is not None:
                return
            self.current_operation = self.operation_queue.pop(0)
        if self.current_operation:
            op = self.current_operation
            QTimer.singleShot(int(self.processing_delay * 1000), lambda: self._start_operation(op))

    def _start_operation(self, op):
        try:
            if op['type'] == 'mute':
                self.mute_thread = MuteActionsThread(op['data']['line'], op['data']['my_full_nickname'], op['data']['temp_nick'], op['data']['warns'])
                self.mute_thread.finished_signal.connect(self._on_mute_finished)
                self.mute_thread.start()
            elif op['type'] == 'warn':
                self.warn_thread = WarnActionsThread(op['data']['line'], op['data']['my_full_nickname'], op['data']['temp_nick'], op['data']['warns'])
                self.warn_thread.finished_signal.connect(self._on_warn_finished)
                self.warn_thread.start()
            elif op['type'] == 'kick':
                self.kick_thread = KickActionsThread(op['data']['my_full_nickname'], op['data']['temp_nick'], op['data']['warns'], op['data']['current_date'], op['data']['last_time'])
                self.kick_thread.finished_signal.connect(self._on_kick_finished)
                self.kick_thread.start()
        except Exception as e:
            self.log_message(f"[ERROR] Ошибка при запуске операции {op['type']}: {e}")
            self._on_operation_completed()

    def _on_mute_finished(self, *args):
        global all_mutes, platform, vk_user_id
        all_mutes += 1
        self.update_stats()
        if using_sounds_in_program:
            self.sound_requested.emit()
        self.message_sender = MessageSenderThread('mute', platform, vk_user_id, *args)
        self.message_sender.finished_signal.connect(lambda s, m: self._on_message_sent(s, m, 'mute'))
        self.message_sender.start()

    def _on_warn_finished(self, *args):
        global all_warns, platform, vk_user_id
        all_warns += 1
        self.update_stats()
        if using_sounds_in_program:
            self.sound_requested.emit()
        self.message_sender = MessageSenderThread('warn', platform, vk_user_id, *args)
        self.message_sender.finished_signal.connect(lambda s, m: self._on_message_sent(s, m, 'warn'))
        self.message_sender.start()

    def _on_kick_finished(self, *args):
        global all_kicks, platform, vk_user_id
        all_kicks += 1
        self.update_stats()
        self.message_sender = MessageSenderThread('kick', platform, vk_user_id, *args)
        self.message_sender.finished_signal.connect(lambda s, m: self._on_message_sent(s, m, 'kick'))
        self.message_sender.start()

    def _on_message_sent(self, success, message, operation_type):
        self.log_message(message)
        if not success:
            gui_print(f"[WARNING] Отправка {operation_type} завершилась с ошибкой")
        self._on_operation_completed()

    def _on_operation_completed(self):
        self.current_operation = None
        QTimer.singleShot(500, self._process_next_operation)

    def take_screenshot(self, e=None):
        if hasattr(self, 'screenshot_thread') and self.screenshot_thread.isRunning():
            gui_print("[SYSTEM] Предыдущий скриншот ещё обрабатывается...")
            return
        self.screenshot_thread = ScreenshotThread()
        self.screenshot_thread.finished_signal.connect(self._on_screenshot_created)
        self.screenshot_thread.start()

    def _on_screenshot_created(self, success, message, filename):
        global platform
        self.log_message(message)
        if success and filename:
            self._load_platform()
            self.message_sender = MessageSenderThread('screenshot', platform, filename)
            self.message_sender.finished_signal.connect(self._on_screenshot_sent)
            self.message_sender.start()
            if using_sounds_in_program:
                self.sound_requested.emit()

    def _on_screenshot_sent(self, success, message):
        self.log_message(message)

    def _start_binding(self):
        if not self.setting_bind_mode:
            self.setting_bind_mode = True
            self.bind_btn.setText("Нажмите клавишу...")
            self.bind_btn.setEnabled(False)
            self.grabKeyboard()
            gui_print("[SYSTEM] Режим привязки: нажмите любую клавишу")

    def keyPressEvent(self, event):
        if self.setting_bind_mode:
            key = event.key()
            if key in [Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_CapsLock, Qt.Key_NumLock, Qt.Key_ScrollLock]:
                event.accept()
                return
            if key in self.allowed_keys:
                self.current_bind_keycode = key
                key_name = self._get_key_name(key)
                try:
                    with open(data_path('binds.txt'), 'w') as f:
                        f.write(str(key))
                except Exception as e:
                    gui_print(f"[ERROR] Ошибка сохранения бинда: {e}")
                self.bind_label.setText(f"Текущий бинд: {key_name}")
                self._setup_global_shortcut()
                gui_print(f"[SYSTEM] Бинд установлен: {key_name}")
            self.setting_bind_mode = False
            self.bind_btn.setText("Изменить бинд скриншота")
            self.bind_btn.setEnabled(True)
            self.releaseKeyboard()
            self._setup_global_shortcut()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _load_bind(self):
        try:
            with open(data_path('binds.txt'), 'r') as f:
                saved_key = int(f.read().strip())
            self.current_bind_keycode = saved_key
            self.bind_label.setText(f"Текущий бинд: {self._get_key_name(saved_key)}")
            self._setup_global_shortcut()
        except FileNotFoundError:
            self.bind_label.setText("Текущий бинд: Не задан")
        except Exception as e:
            self.bind_label.setText("Текущий бинд: Ошибка загрузки")
            gui_print(f"[ERROR] Ошибка загрузки бинда: {e}")

    def _setup_global_shortcut(self):
        import pynput.keyboard as pynput_kb
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.current_bind_keycode is not None:
                pynput_key = self._qt_key_to_pynput(self.current_bind_keycode)
                if pynput_key:
                    def on_press(key):
                        try:
                            if key == pynput_key:
                                QTimer.singleShot(0, self.take_screenshot)
                        except Exception:
                            pass
                    self.keyboard_listener = pynput_kb.Listener(on_press=on_press, suppress=False)
                    self.keyboard_listener.start()
        except Exception as e:
            gui_print(f"[ERROR] Ошибка настройки горячей клавиши: {e}")

    def _qt_key_to_pynput(self, qt_key_code):
        import pynput.keyboard as pynput_kb
        from pynput.keyboard import Key
        if Qt.Key_A <= qt_key_code <= Qt.Key_Z:
            return pynput_kb.KeyCode.from_char(chr(qt_key_code).lower())
        if Qt.Key_0 <= qt_key_code <= Qt.Key_9:
            return pynput_kb.KeyCode.from_char(chr(qt_key_code))
        if Qt.Key_F1 <= qt_key_code <= Qt.Key_F24:
            return getattr(Key, f'f{qt_key_code - Qt.Key_F1 + 1}')
        mapping = {
            Qt.Key_Insert: Key.insert, Qt.Key_Delete: Key.delete,
            Qt.Key_Home: Key.home, Qt.Key_End: Key.end,
            Qt.Key_PageUp: Key.page_up, Qt.Key_PageDown: Key.page_down,
            Qt.Key_Print: Key.print_screen, Qt.Key_Pause: Key.pause,
            Qt.Key_Escape: Key.esc, Qt.Key_Left: Key.left,
            Qt.Key_Right: Key.right, Qt.Key_Up: Key.up, Qt.Key_Down: Key.down,
            Qt.Key_Shift: Key.shift, Qt.Key_Control: Key.ctrl,
            Qt.Key_Alt: Key.alt, Qt.Key_Space: Key.space,
            Qt.Key_Return: Key.enter, Qt.Key_Enter: Key.enter,
            Qt.Key_Tab: Key.tab, Qt.Key_Backspace: Key.backspace,
            Qt.Key_CapsLock: Key.caps_lock, Qt.Key_NumLock: Key.num_lock,
        }
        if qt_key_code in mapping:
            return mapping[qt_key_code]
        return None

    def _get_key_name(self, key_code):
        if key_code is None:
            return "Не задан"
        if Qt.Key_A <= key_code <= Qt.Key_Z:
            return chr(key_code)
        if Qt.Key_0 <= key_code <= Qt.Key_9:
            return chr(key_code)
        if Qt.Key_F1 <= key_code <= Qt.Key_F24:
            return f"F{key_code - Qt.Key_F1 + 1}"
        names = {
            Qt.Key_Insert: "Insert", Qt.Key_Delete: "Delete",
            Qt.Key_Home: "Home", Qt.Key_End: "End",
            Qt.Key_PageUp: "Page Up", Qt.Key_PageDown: "Page Down",
            Qt.Key_Print: "Print Screen", Qt.Key_Pause: "Pause",
            Qt.Key_Escape: "Esc", Qt.Key_Left: "←", Qt.Key_Right: "→",
            Qt.Key_Up: "↑", Qt.Key_Down: "↓", Qt.Key_Shift: "Shift",
            Qt.Key_Control: "Ctrl", Qt.Key_Alt: "Alt",
            Qt.Key_Space: "Space", Qt.Key_Return: "Enter",
            Qt.Key_Enter: "Enter", Qt.Key_Tab: "Tab",
            Qt.Key_Backspace: "Backspace", Qt.Key_CapsLock: "Caps Lock",
        }
        return names.get(key_code, f"Key_{key_code}")

    def _play_sound(self):
        make_sound()

    def closeEvent(self, event):
        try:
            if hasattr(self, 'session_timer'):
                self.session_timer.stop()
            if hasattr(self, 'log_monitor'):
                self.log_monitor.stop()
            if hasattr(self, 'message_sender'):
                self.message_sender.stop()
            for attr in ['mute_thread', 'warn_thread', 'kick_thread', 'screenshot_thread', 'download_thread']:
                if hasattr(self, attr) and getattr(self, attr) is not None:
                    getattr(self, attr).quit()
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                self.keyboard_listener.stop()
        except Exception as e:
            gui_print(f"[ERROR] Ошибка при закрытии: {e}")
        event.accept()