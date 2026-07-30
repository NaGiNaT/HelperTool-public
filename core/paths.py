import sys
import os


def _get_data_dir():
    if sys.platform == 'win32':
        # Windows: C:\Users\<User>\AppData\Roaming\HelperTool
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        # Mac/Linux: ~/.helpertool
        base = os.path.expanduser('~')
    return os.path.join(base, 'HelperTool')


DATA_DIR = _get_data_dir()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"[SYSTEM] Создана папка настроек: {DATA_DIR}")


def data_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)