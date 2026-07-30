import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QMetaType
from PyQt5.QtGui import QTextCursor, QIcon
import tkinter.messagebox

from config import check_config
from updater import check_for_update, get_release_page_url
from core.paths import ensure_data_dir, data_path
from core.helpers import gui_print, cleanup, create_empty_config
from core.globals import gui_ready
from ui.setup_window import SetupWindow


if __name__ == "__main__":
    try:
        ensure_data_dir()

        try:
            check_config()
        except Exception as config_error:
            tkinter.messagebox.showerror(
                "Ошибка конфигурации",
                f"Не удалось загрузить данные!\n\nПроверьте подключение к интернету.\n\n{config_error}"
            )
            sys.exit(1)

        app = QApplication(sys.argv)

        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'path', 'icon.ico')
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"[WARNING] Файл иконки не найден: {e}")

        try:
            if not QMetaType.isRegistered(QMetaType.type('QTextCursor')):
                QMetaType.registerType(QTextCursor)
        except Exception:
            pass

        create_empty_config()

        gui_ready = True

        has_update, new_version, _ = check_for_update()
        if has_update:
            print(f"[SYSTEM] Доступна новая версия: {new_version}")
            print(f"[SYSTEM] Скачайте: {get_release_page_url()}")

        setup_window = SetupWindow()
        setup_window.show()

        exit_code = app.exec_()
        from core.globals import main_window
        if main_window and hasattr(main_window, 'log_monitor'):
            main_window.log_monitor.stop()

        sys.exit(exit_code)

    except Exception as e:
        print(f"[ERROR] GUI crashed: {e}")
        import traceback
        traceback.print_exc()
        cleanup()