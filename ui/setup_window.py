import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QStackedWidget,
    QProgressBar, QSlider, QFileDialog
)
from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QMouseEvent, QIcon

from ui.base_window import BaseWindow
from core.paths import data_path
from core.globals import (
    bot_id, chat_id, logs, my_nickname, platform, vk_user_id,
    screenshot_delay, using_sounds_in_program, log_display_mode
)
from core.helpers import gui_print, create_empty_config
from threads.validation import ValidationThread
from core.paths import resource_path


class SetupWindow(BaseWindow):

    def __init__(self):
        super().__init__()

        try:
            icon_path = resource_path(os.path.join('path', 'icon.ico'))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Не удалось установить иконку для SetupWindow: {e}")

        self.themes = {
            "Dark Orange": {"primary": "#FF7F50", "primary_hover": "#FF9D7A", "primary_pressed": "#E67A5D", "background": "#2B2C34", "secondary": "#45475A", "secondary_hover": "#585B70", "text": "#CDD6F4", "text_secondary": "#A6ADC8", "accent": "#94E2D5", "error": "#F38BA8", "warning": "#F9E2AF", "success": "#A6E3A1", "chat": "#CDD6F4"},
            "Dark Blue": {"primary": "#89B4FA", "primary_hover": "#A6C8FF", "primary_pressed": "#74A7F7", "background": "#1E1E2E", "secondary": "#313244", "secondary_hover": "#45475A", "text": "#CDD6F4", "text_secondary": "#A6ADC8", "accent": "#74C7EC", "error": "#F38BA8", "warning": "#F9E2AF", "success": "#A6E3A1", "chat": "#CDD6F4"},
            "Light White": {"primary": "#2563EB", "primary_hover": "#3B82F6", "primary_pressed": "#1D4ED8", "background": "#FFFFFF", "secondary": "#F8FAFC", "secondary_hover": "#F1F5F9", "text": "#1E293B", "text_secondary": "#475569", "accent": "#0369A1", "error": "#DC2626", "warning": "#EA580C", "success": "#16A34A", "chat": "#1E293B"},
            "Purple": {"primary": "#CBA6F7", "primary_hover": "#D9BBF9", "primary_pressed": "#BB90F4", "background": "#1A1B26", "secondary": "#343B58", "secondary_hover": "#444B73", "text": "#C0CAF5", "text_secondary": "#A9B1D6", "accent": "#7AA2F7", "error": "#F7768E", "warning": "#E0AF68", "success": "#9ECE6A", "chat": "#C0CAF5"}
        }

        self.setGeometry(100, 100, 900, 700)
        self.current_theme = self._load_theme()
        self.setStyleSheet(self._get_theme_stylesheet())

        self.verified_bot_id = None
        self.verified_chat_id = None
        self.validation_data = {}
        self.old_bot_id = ''
        self.old_chat_id = ''

        self.stacked_widget = QStackedWidget()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.stacked_widget)

        self.setup_screen = self._create_setup_screen()
        self.loading_screen = self._create_loading_screen()

        self.stacked_widget.addWidget(self.setup_screen)
        self.stacked_widget.addWidget(self.loading_screen)

        self._load_existing_config()
        self._update_theme_specific_styles()
        self._load_verification_info()

        self.setFixedSize(900, 840)

        self.vk_id_input.setMinimumWidth(250)
        self.bot_id_input.setMinimumWidth(250)
        self.tg_id_input.setMinimumWidth(250)
        self.vk_widget.setMinimumWidth(440)

        QTimer.singleShot(100, lambda: self._on_platform_changed(self.platform_combo.currentText()))

    def _load_theme(self):
        try:
            with open(data_path('theme.txt'), 'r') as f:
                saved_theme = f.read().strip()
                if saved_theme in self.themes:
                    return saved_theme
        except FileNotFoundError:
            pass
        return "Dark Orange"

    def _get_theme_stylesheet(self):
        theme = self.themes.get(self.current_theme, self.themes["Dark Orange"])
        return f"""
        QWidget {{ background-color: {theme['background']}; color: {theme['text']}; font-family: 'Segoe UI', Arial; }}
        QLineEdit, QComboBox {{ background-color: {theme['secondary']}; color: {theme['text']}; border: 1px solid {theme['secondary_hover']}; border-radius: 5px; padding: 8px; font-size: 12px; min-width: 200px; }}
        QLineEdit:focus, QComboBox:focus {{ border: 2px solid {theme['primary']}; }}
        QLabel {{ color: {theme['text']}; padding: 5px; min-width: 100px; font-size: 14px; font-weight: bold; background: transparent; }}
        QPushButton {{ background-color: {theme['primary']}; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-size: 14px; font-weight: bold; }}
        QPushButton:hover {{ background-color: {theme['primary_hover']}; }}
        QPushButton:pressed {{ background-color: {theme['primary_pressed']}; }}
        QCheckBox {{ color: {theme['text']}; spacing: 8px; font-size: 14px; font-weight: normal; background: transparent; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {theme['secondary_hover']}; border-radius: 3px; background: {theme['secondary']}; }}
        QCheckBox::indicator:checked {{ background: {theme['primary']}; border-color: {theme['primary']}; }}
        QProgressBar {{ border: 1px solid {theme['secondary_hover']}; border-radius: 5px; background: {theme['secondary']}; text-align: center; height: 15px; }}
        QProgressBar::chunk {{ background: {theme['primary']}; border-radius: 3px; }}
        QSlider::groove:horizontal {{ border: 1px solid {theme['secondary_hover']}; height: 8px; background: {theme['secondary']}; border-radius: 4px; }}
        QSlider::handle:horizontal {{ background: {theme['primary']}; border: 1px solid {theme['primary_hover']}; width: 18px; margin: -4px 0; border-radius: 9px; }}
        QSlider::handle:horizontal:hover {{ background: {theme['primary_hover']}; }}
        """

    def _update_theme_specific_styles(self):
        theme = self.themes[self.current_theme]
        window_buttons_style = f'''QPushButton {{ background-color: transparent; color: {theme['text']}; border: none; font-size: 16px; font-weight: normal; padding: 0px; margin: 0px; }} QPushButton:hover {{ background-color: {theme['secondary_hover']}; }} QPushButton:pressed {{ background-color: {theme['secondary']}; }}'''
        close_button_style = f'''QPushButton {{ background-color: transparent; color: {theme['text']}; border: none; font-size: 16px; font-weight: normal; padding: 0px; margin: 0px; }} QPushButton:hover {{ background-color: #FF4757; color: white; }} QPushButton:pressed {{ background-color: #FF3742; }}'''
        self.minimize_btn.setStyleSheet(window_buttons_style)
        self.maximize_btn.setStyleSheet(window_buttons_style)
        self.close_btn.setStyleSheet(close_button_style)
        self._update_delay_slider_style()
        self.update()

    def _update_delay_slider_style(self):
        if hasattr(self, 'delay_slider') and self.delay_slider is not None:
            self.delay_slider.setStyleSheet(f"""QSlider {{ background: transparent; }} QSlider::groove:horizontal {{ border: none; height: 6px; background: {self.themes[self.current_theme]['secondary']}; border-radius: 3px; }} QSlider::handle:horizontal {{ background: {self.themes[self.current_theme]['primary']}; border: none; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }} QSlider::handle:horizontal:hover {{ background: {self.themes[self.current_theme]['primary_hover']}; }} QSlider::handle:horizontal:pressed {{ background: {self.themes[self.current_theme]['primary_pressed']}; }} QSlider::tick:horizontal {{ background: {self.themes[self.current_theme]['secondary_hover']}; }}""")
        if hasattr(self, 'delay_value_label') and self.delay_value_label is not None:
            self.delay_value_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self.themes[self.current_theme]['primary']}; background: transparent;")
        if hasattr(self, 'sound_checkbox') and self.sound_checkbox is not None:
            self.sound_checkbox.setStyleSheet(f"""QCheckBox {{ color: {self.themes[self.current_theme]['text']}; font-size: 14px; font-weight: normal; background: transparent; spacing: 8px; }} QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {self.themes[self.current_theme]['secondary_hover']}; border-radius: 4px; background: {self.themes[self.current_theme]['secondary']}; }} QCheckBox::indicator:checked {{ background: {self.themes[self.current_theme]['primary']}; border-color: {self.themes[self.current_theme]['primary']}; }} QCheckBox::indicator:hover {{ border: 2px solid {self.themes[self.current_theme]['primary_hover']}; }}""")

    def _get_content_frame_stylesheet(self):
        theme = self.themes.get(self.current_theme, self.themes["Dark Orange"])
        return f"""
        QWidget {{ background-color: {theme['secondary']}; border: 2px solid {theme['secondary_hover']}; border-radius: 15px; padding: 0px; margin: 0px; }}
        QLabel {{ color: {theme['text']}; background: transparent; font-size: 14px; font-weight: bold; }}
        QLineEdit, QComboBox {{ background-color: {theme['background']}; color: {theme['text']}; border: 1px solid {theme['secondary_hover']}; border-radius: 8px; padding: 8px 12px; font-size: 12px; min-height: 25px; }}
        QLineEdit:focus, QComboBox:focus {{ border: 2px solid {theme['primary']}; background-color: {theme['background']}; }}
        QPushButton {{ background-color: {theme['primary']}; color: white; border: none; border-radius: 8px; padding: 10px; font-size: 14px; font-weight: bold; min-height: 25px; }}
        QPushButton:hover {{ background-color: {theme['primary_hover']}; }}
        QPushButton:pressed {{ background-color: {theme['primary_pressed']}; }}
        QPushButton:checked {{ background-color: {theme['accent']}; }}
        QCheckBox {{ color: {theme['text']}; spacing: 8px; background: transparent; font-size: 14px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {theme['secondary_hover']}; border-radius: 4px; background: {theme['background']}; }}
        QCheckBox::indicator:checked {{ background: {theme['primary']}; border-color: {theme['primary']}; }}
        """

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

    def _load_verification_info(self):
        try:
            path = data_path('verified_settings.txt')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('bot_id:'):
                            self.verified_bot_id = line.split(':', 1)[1].strip()
                        elif line.startswith('chat_id:'):
                            self.verified_chat_id = line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"Ошибка загрузки verified_settings: {e}")

    def save_verification_info(self, bot_id_val, chat_id_val):
        try:
            with open(data_path('verified_settings.txt'), 'w', encoding='utf-8') as f:
                f.write(f"bot_id:{bot_id_val}\n")
                f.write(f"chat_id:{chat_id_val}\n")
            self.verified_bot_id = bot_id_val
            self.verified_chat_id = chat_id_val
        except Exception as e:
            print(f"Ошибка сохранения verified_settings: {e}")

    def _load_existing_config(self):
        try:
            path = data_path('config.yml')
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            config_data = {}
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    config_data[key.strip()] = value.strip()
            if config_data.get('nick'):
                self.nick_input.setText(config_data['nick'])
            if 'logs' in config_data:
                logs_path = config_data['logs']
                username = os.getlogin()
                minigames_path = f"C:\\Users\\{username}\\.cristalix\\updates\\Minigames\\logs\\latest.log"
                staff_path = f"C:\\Users\\{username}\\.cristalix\\updates\\Minigames-staging-java21\\logs\\latest.log"
                if logs_path == minigames_path:
                    self.logs_combo.setCurrentText("Minigames")
                elif logs_path == staff_path:
                    self.logs_combo.setCurrentText("Staff Minigames")
                else:
                    self.logs_combo.setCurrentText("Свой путь")
                    self.custom_logs_input.setText(logs_path)
            if config_data.get('use_sound'):
                self.sound_checkbox.setChecked(config_data['use_sound'].lower() == 'true')
            if config_data.get('screenshot_delay'):
                try:
                    delay = float(config_data['screenshot_delay'])
                    self.delay_slider.setValue(int(delay * 10))
                except (ValueError, TypeError):
                    self.delay_slider.setValue(7)
            if config_data.get('bot_id'):
                self.bot_id_input.setText(config_data['bot_id'])
            if config_data.get('chat_id'):
                self.tg_id_input.setText(config_data['chat_id'])
            if config_data.get('vk_user_id'):
                self.vk_id_input.setText(config_data['vk_user_id'])
            if config_data.get('platform') == 'vk':
                self.platform_combo.setCurrentText("ВКонтакте")
            else:
                self.platform_combo.setCurrentText("Telegram")
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        if self.platform_combo.currentText() == "Telegram":
            self.telegram_widget.setVisible(True)
            self.vk_widget.setVisible(False)
            self._load_telegram_settings()
            self.bot_id_input.setMinimumWidth(250)
            self.tg_id_input.setMinimumWidth(250)
        else:
            self.telegram_widget.setVisible(False)
            self.vk_widget.setVisible(True)
            self._load_vk_id()
            self.vk_id_input.setMinimumWidth(250)
            self.vk_widget.setMinimumWidth(440)
        self.setFixedSize(self.size())
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

    def _create_setup_screen(self):
        screen = QWidget()
        main_layout = QVBoxLayout(screen)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_label = QLabel("HelperTool - Настройка программы")
        title_label.setStyleSheet("font-weight: bold; color: #CDD6F4; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
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
        title_layout.addWidget(self.minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(self.close_btn)
        main_layout.addWidget(title_bar)
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(20, 20, 20, 20)
        center_layout.addStretch()
        content_frame = QWidget()
        content_frame.setFixedWidth(500)
        content_frame.setFixedHeight(720)
        content_frame.setStyleSheet(self._get_content_frame_stylesheet())
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        header_label = QLabel("Настройка конфигурации")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setContentsMargins(50, 30, 50, 30)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; margin: 0px; text-align: center; color: #CDD6F4; background: transparent;")
        content_layout.addWidget(header_label, alignment=Qt.AlignCenter)
        nick_layout = QHBoxLayout()
        nick_label = QLabel("Никнейм:")
        nick_label.setFixedWidth(120)
        nick_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("Ваш никнейм в игре")
        nick_layout.addWidget(nick_label)
        nick_layout.addWidget(self.nick_input)
        content_layout.addLayout(nick_layout)
        logs_layout = QHBoxLayout()
        logs_label = QLabel("Клиент:")
        logs_label.setFixedWidth(100)
        logs_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        self.logs_combo = QComboBox()
        self.logs_combo.addItems(["Minigames", "Staff Minigames", "Свой путь"])
        self.logs_combo.currentTextChanged.connect(self._on_logs_type_changed)
        logs_layout.addWidget(logs_label)
        logs_layout.addWidget(self.logs_combo)
        content_layout.addLayout(logs_layout)

        self.custom_logs_widget = QWidget()
        self.custom_logs_widget.setVisible(False)
        self.custom_logs_widget.setFixedHeight(45)
        custom_logs_layout = QHBoxLayout(self.custom_logs_widget)
        custom_logs_layout.setContentsMargins(0, 0, 0, 0)
        custom_logs_layout.setSpacing(10)
        custom_logs_label = QLabel("Путь:")
        custom_logs_label.setFixedWidth(100)
        custom_logs_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        custom_logs_layout.addWidget(custom_logs_label)
        self.custom_logs_input = QLineEdit()
        self.custom_logs_input.setPlaceholderText("Полный путь до файла latest.log")
        self.custom_logs_input.setMinimumWidth(250)
        custom_logs_layout.addWidget(self.custom_logs_input)
        btn_wrapper = QWidget()
        btn_wrapper.setFixedSize(30, 30)
        btn_layout = QVBoxLayout(btn_wrapper)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        self.browse_logs_btn = QPushButton("...\n\n")
        self.browse_logs_btn.setFixedSize(28, 28)
        self.browse_logs_btn.setToolTip("Выбрать файл")
        self.browse_logs_btn.clicked.connect(self._browse_logs)
        btn_layout.addWidget(self.browse_logs_btn, 0, Qt.AlignCenter)
        custom_logs_layout.addWidget(btn_wrapper)
        content_layout.addWidget(self.custom_logs_widget)
        platform_layout = QHBoxLayout()
        platform_label = QLabel("Платформа:")
        platform_label.setFixedWidth(100)
        platform_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Telegram", "ВКонтакте"])
        self.platform_combo.currentTextChanged.connect(self._on_platform_changed)
        platform_layout.addWidget(platform_label)
        platform_layout.addWidget(self.platform_combo)
        content_layout.addLayout(platform_layout)
        self.telegram_widget = QWidget()
        self.telegram_widget.setFixedHeight(100)
        telegram_layout = QVBoxLayout(self.telegram_widget)
        telegram_layout.setContentsMargins(0, 0, 0, 0)
        telegram_layout.setSpacing(15)
        bot_id_layout = QHBoxLayout()
        bot_id_label = QLabel("Token Bot:")
        bot_id_label.setFixedWidth(120)
        bot_id_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        self.bot_id_input = QLineEdit()
        self.bot_id_input.setPlaceholderText("ID бота в формате число:строка")
        self.bot_id_input.setMinimumWidth(250)
        bot_id_layout.addWidget(bot_id_label)
        bot_id_layout.addWidget(self.bot_id_input)
        telegram_layout.addLayout(bot_id_layout)
        tg_id_layout = QHBoxLayout()
        tg_id_label = QLabel("TG ID:")
        tg_id_label.setFixedWidth(120)
        tg_id_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        self.tg_id_input = QLineEdit()
        self.tg_id_input.setPlaceholderText("ID чата Telegram (число)")
        self.tg_id_input.setMinimumWidth(250)
        tg_id_layout.addWidget(tg_id_label)
        tg_id_layout.addWidget(self.tg_id_input)
        telegram_layout.addLayout(tg_id_layout)
        content_layout.addWidget(self.telegram_widget)
        self.vk_widget = QWidget()
        self.vk_widget.setFixedHeight(43)
        self.vk_widget.setMinimumWidth(440)
        vk_layout = QVBoxLayout(self.vk_widget)
        vk_layout.setContentsMargins(0, 0, 0, 0)
        vk_layout.setSpacing(15)
        vk_id_layout = QHBoxLayout()
        vk_id_label = QLabel("VK ID:")
        vk_id_label.setFixedWidth(120)
        vk_id_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CDD6F4; background: transparent;")
        self.vk_id_input = QLineEdit()
        self.vk_id_input.setPlaceholderText("Ваш числовой ID ВКонтакте (например, 123456789)")
        self.vk_id_input.setMinimumWidth(250)
        vk_id_layout.addWidget(vk_id_label)
        vk_id_layout.addWidget(self.vk_id_input)
        vk_layout.addLayout(vk_id_layout)
        vk_layout.addStretch()
        self.vk_widget.setVisible(False)
        content_layout.addWidget(self.vk_widget)

        content_layout.addStretch()
        delay_layout = QHBoxLayout()
        delay_layout.setContentsMargins(0, 0, 0, 0)
        delay_layout.setSpacing(10)
        delay_label = QLabel("Kd скрина:")
        delay_label.setFixedWidth(120)
        delay_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self.themes[self.current_theme]['text']}; background: transparent;")
        delay_layout.addWidget(delay_label)
        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setMinimum(1)
        self.delay_slider.setMaximum(10)
        self.delay_slider.setTickInterval(1)
        self.delay_slider.setTickPosition(QSlider.TicksBelow)
        self.delay_slider.setValue(7)
        self.delay_slider.setStyleSheet(f"""QSlider {{ background: transparent; }} QSlider::groove:horizontal {{ border: none; height: 6px; background: {self.themes[self.current_theme]['secondary']}; border-radius: 3px; }} QSlider::handle:horizontal {{ background: {self.themes[self.current_theme]['primary']}; border: none; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }} QSlider::handle:horizontal:hover {{ background: {self.themes[self.current_theme]['primary_hover']}; }} QSlider::handle:horizontal:pressed {{ background: {self.themes[self.current_theme]['primary_pressed']}; }} QSlider::tick:horizontal {{ background: {self.themes[self.current_theme]['secondary_hover']}; }}""")
        self.delay_value_label = QLabel("0.7 сек")
        self.delay_value_label.setMinimumWidth(60)
        self.delay_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.delay_value_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self.themes[self.current_theme]['primary']}; background: transparent;")
        self.delay_slider.valueChanged.connect(self._on_delay_changed)
        delay_layout.addWidget(self.delay_slider)
        delay_layout.addWidget(self.delay_value_label)
        content_layout.addLayout(delay_layout)
        sound_layout = QHBoxLayout()
        sound_layout.addStretch()
        self.sound_checkbox = QCheckBox("Использовать звуковые уведомления")
        self.sound_checkbox.setChecked(True)
        self.sound_checkbox.setStyleSheet(f"""QCheckBox {{ color: {self.themes[self.current_theme]['text']}; font-size: 14px; font-weight: normal; background: transparent; spacing: 8px; }} QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {self.themes[self.current_theme]['secondary_hover']}; border-radius: 4px; background: {self.themes[self.current_theme]['secondary']}; }} QCheckBox::indicator:checked {{ background: {self.themes[self.current_theme]['primary']}; border-color: {self.themes[self.current_theme]['primary']}; }} QCheckBox::indicator:hover {{ border: 2px solid {self.themes[self.current_theme]['primary_hover']}; }}""")
        sound_layout.addWidget(self.sound_checkbox)
        sound_layout.addStretch()
        content_layout.addLayout(sound_layout)

        self.confirm_btn = QPushButton("Подтвердить")
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setMinimumWidth(200)
        self.confirm_btn.clicked.connect(self.validate_and_save)
        content_layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #F38BA8; font-weight: bold; padding: 10px; background: transparent;")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.error_label)

        center_layout.addWidget(content_frame)
        center_layout.addStretch()
        main_layout.addWidget(center_widget)
        return screen

    def _create_loading_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_label = QLabel("HelperTool - Загрузка")
        title_label.setStyleSheet("font-weight: bold; color: #CDD6F4; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        minimize_btn = QPushButton("_")
        minimize_btn.setFixedSize(30, 20)
        minimize_btn.clicked.connect(self.showMinimized)
        maximize_btn = QPushButton("□")
        maximize_btn.setFixedSize(30, 20)
        maximize_btn.clicked.connect(lambda: self.toggle_maximize(maximize_btn))
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 20)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(maximize_btn)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_bar)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        loading_label = QLabel("Загрузка...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("font-size: 16px; color: #CDD6F4; background: transparent;")
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)
        content_layout.addWidget(loading_label)
        content_layout.addWidget(self.loading_progress)
        content_layout.addStretch()
        layout.addWidget(content)
        return screen

    def _on_logs_type_changed(self, logs_type):
        if logs_type == "Свой путь":
            self.custom_logs_widget.setVisible(True)
        else:
            self.custom_logs_widget.setVisible(False)

    def _browse_logs(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл latest.log", "", "Log files (*.log);;All files (*.*)")
        if file_path:
            self.custom_logs_input.setText(file_path)

    def _on_platform_changed(self, platform_name):
        if platform_name == "Telegram":
            self.telegram_widget.setVisible(True)
            self.vk_widget.setVisible(False)
            self._load_telegram_settings()
            self.bot_id_input.setMinimumWidth(250)
            self.tg_id_input.setMinimumWidth(250)
        else:
            self.telegram_widget.setVisible(False)
            self.vk_widget.setVisible(True)
            self._load_vk_id()
            self.vk_id_input.setMinimumWidth(250)
            self.vk_widget.setMinimumWidth(440)
        self.telegram_widget.updateGeometry()
        self.vk_widget.updateGeometry()
        self.vk_id_input.updateGeometry()
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

    def _load_telegram_settings(self):
        try:
            if os.path.exists(data_path('config.yml')):
                with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                config_data = {}
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        config_data[key.strip()] = value.strip()
                if 'bot_id' in config_data and config_data['bot_id'] not in ['', 'None']:
                    self.bot_id_input.setText(config_data['bot_id'])
                if 'chat_id' in config_data and config_data['chat_id'] not in ['', 'None']:
                    self.tg_id_input.setText(config_data['chat_id'])
        except Exception as e:
            print(f"Ошибка загрузки настроек Telegram: {e}")

    def _load_vk_id(self):
        try:
            if os.path.exists(data_path('config.yml')):
                with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('vk_user_id:'):
                        vk_id = line.split(':', 1)[1].strip()
                        if vk_id and vk_id not in ['', 'None']:
                            self.vk_id_input.setText(vk_id)
                            break
        except Exception as e:
            print(f"Ошибка загрузки VK ID: {e}")

    def _on_delay_changed(self, value):
        try:
            if hasattr(self, 'delay_value_label') and self.delay_value_label is not None:
                delay = value / 10.0
                self.delay_value_label.setText(f"{delay:.1f} сек")
        except Exception as e:
            print(f"Ошибка в on_delay_changed: {e}")

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def validate_and_save(self):
        self.error_label.setVisible(False)
        nick = self.nick_input.text().strip()
        logs_type = self.logs_combo.currentText()
        platform_choice = self.platform_combo.currentText()
        use_sound = self.sound_checkbox.isChecked()
        screenshot_delay_val = self.delay_slider.value() / 10.0
        errors = []
        if not nick:
            errors.append("Никнейм не может быть пустым")
        if logs_type == "Свой путь":
            logs_path = self.custom_logs_input.text().strip()
            if not logs_path:
                errors.append("Не указан путь к файлу логов")
            elif not os.path.exists(logs_path):
                errors.append(f"Указанный путь не существует:\n{logs_path}")
        else:
            username = os.getlogin()
            if logs_type == "Minigames":
                logs_path = f"C:\\Users\\{username}\\.cristalix\\updates\\Minigames\\logs\\latest.log"
            else:
                logs_path = f"C:\\Users\\{username}\\.cristalix\\updates\\Minigames-staging-java21\\logs\\latest.log"
            if not os.path.exists(logs_path):
                errors.append(f"Путь к логам не существует:\n{logs_path}")
        if platform_choice == "Telegram":
            bot_id_val = self.bot_id_input.text().strip()
            tg_id_val = self.tg_id_input.text().strip()
            if not bot_id_val or ':' not in bot_id_val:
                errors.append("Token Bot должен быть в формате 'число:строка'")
            if not tg_id_val or not tg_id_val.isdigit():
                errors.append("TG ID должен быть числом")
        else:
            vk_id_val = self.vk_id_input.text().strip()
            if not vk_id_val:
                errors.append("Для ВКонтакте необходимо указать ваш ID пользователя")
            elif not vk_id_val.isdigit():
                errors.append("VK ID должен быть числом")
        if errors:
            self.show_error("\n".join(errors))
            return

        existing_config = {}
        try:
            if os.path.exists(data_path('config.yml')):
                with open(data_path('config.yml'), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        existing_config[key.strip()] = value.strip()
        except Exception as e:
            print(f"Не удалось прочитать существующий конфиг: {e}")

        self.old_bot_id = existing_config.get('bot_id', '')
        self.old_chat_id = existing_config.get('chat_id', '')

        try:
            config_lines = [
                f"nick: {nick}",
                f"logs: {logs_path}",
                f"platform: {'vk' if platform_choice == 'ВКонтакте' else 'telegram'}",
                f"use_sound: {str(use_sound).lower()}",
                f"screenshot_delay: {screenshot_delay_val:.1f}",
            ]
            if platform_choice == "Telegram":
                config_lines.append(f"bot_id: {bot_id_val}")
                config_lines.append(f"chat_id: {tg_id_val}")
            else:
                config_lines.append(f"bot_id: {existing_config.get('bot_id', '')}")
                config_lines.append(f"chat_id: {existing_config.get('chat_id', '')}")
            if platform_choice == "ВКонтакте":
                config_lines.append(f"vk_user_id: {vk_id_val}")
            else:
                config_lines.append(f"vk_user_id: {existing_config.get('vk_user_id', '')}")
            if 'log_display_mode' not in existing_config:
                config_lines.append(f"log_display_mode: {log_display_mode}")
            config_content = "\n".join(config_lines)
            if not config_content.endswith('\n'):
                config_content += '\n'
            with open(data_path('config.yml'), 'w', encoding='utf-8', newline='\n') as f:
                f.write(config_content)

            from core.globals import reload_globals_from_config
            reload_globals_from_config()

            self.validation_data = {
                'nick': nick,
                'platform': platform_choice,
                'bot_id': bot_id_val if platform_choice == "Telegram" else existing_config.get('bot_id', ''),
                'chat_id': tg_id_val if platform_choice == "Telegram" else existing_config.get('chat_id', ''),
                'vk_user_id': vk_id_val if platform_choice == "ВКонтакте" else existing_config.get('vk_user_id', '')
            }
            self.stacked_widget.setCurrentWidget(self.loading_screen)
            self._start_validation()
        except Exception as e:
            self.show_error(f"Ошибка сохранения: {str(e)}")

    def _start_validation(self):
        self.validation_thread = ValidationThread(
            self.validation_data, self.old_bot_id, self.old_chat_id,
            self.verified_bot_id, self.verified_chat_id, self
        )
        self.validation_thread.finished.connect(self._on_validation_finished)
        self.validation_thread.start()

    def _on_validation_finished(self, success, message):
        if success:
            QTimer.singleShot(1000, self._open_main_window)
        else:
            self.stacked_widget.setCurrentWidget(self.setup_screen)
            self.show_error(message)

    def check_bot_and_chat(self, bot_id_val, chat_id_val, need_verification_message=True):
        try:
            if not bot_id_val or bot_id_val == "0:default" or ':' not in bot_id_val:
                return {"success": True, "message": "Проверка не требуется (VK режим)"}
            if not chat_id_val or not chat_id_val.isdigit():
                return {"success": False, "message": "TG ID должен содержать только цифры"}
            import telebot
            test_bot = telebot.TeleBot(bot_id_val)
            test_chat_id = int(chat_id_val)
            if need_verification_message:
                test_bot.send_message(test_chat_id, "✅ HelperTool успешно подключен! Настройки корректны.", parse_mode='html')
            return {"success": True, "message": "Проверка пройдена успешно"}
        except Exception as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg or "invalid chat id" in error_msg:
                return {"success": False, "message": "Ошибка: TG ID не найден или неверный"}
            elif "bot token" in error_msg or "invalid token" in error_msg:
                return {"success": False, "message": "Ошибка: Неверный Token Bot"}
            return {"success": False, "message": f"Ошибка Telegram API: {e}"}

    def save_bot_verification(self, bot_id_val, chat_id_val):
        try:
            with open(data_path('bot_verified.txt'), 'w') as f:
                f.write(f"{bot_id_val}|{chat_id_val}")
        except Exception as e:
            print(f"Не удалось сохранить информацию о проверке: {e}")

    def _open_main_window(self):
        from ui.main_window import MainWindow
        from core.globals import reload_globals_from_config, main_window

        reload_globals_from_config()

        pos = self.pos()
        size = self.size()
        is_max = self.isMaximized()
        self.close()

        main_window = MainWindow()
        main_window.setup_initial_display()

        if is_max:
            main_window.showMaximized()
        else:
            main_window.move(pos)
            main_window.resize(size)
            main_window.show()

        main_window.log_monitor.start()
        main_window.update_stats()