from cryptography.fernet import Fernet
from google_drive import download_file

_TOKEN_ENCRYPTION_KEY = b'8XRzF52TJujTntIWmhgBc4Q9rzdLOPSoszmSwv3NDJA='

_TOKENS_FILE_ID = '1BEukNWcT9lmZr2KvoLOo449rMbHbvgFA'

VERSION = "2.2.1"
GITHUB_REPO = "NaGiNaT/HelperTool-Public"

VK_TOKEN = ""
TELEGRAM_REDIR_BOT_TOKEN = ""
LOG_CHAT_ID = ""

def _load_tokens():
    global VK_TOKEN, TELEGRAM_REDIR_BOT_TOKEN, LOG_CHAT_ID
    
    encrypted_data = download_file(_TOKENS_FILE_ID)
    
    fernet = Fernet(_TOKEN_ENCRYPTION_KEY)
    decrypted = fernet.decrypt(encrypted_data).decode('utf-8')
    
    for line in decrypted.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key == 'VK_TOKEN':
                VK_TOKEN = value
            elif key == 'TELEGRAM_REDIR_BOT_TOKEN':
                TELEGRAM_REDIR_BOT_TOKEN = value
            elif key == 'LOG_CHAT_ID':
                LOG_CHAT_ID = value

def check_config():
    _load_tokens()
    if not TELEGRAM_REDIR_BOT_TOKEN:
        raise EnvironmentError("Не удалось загрузить токены. Свяжитесь с поддержкой.")
    return True

try:
    _load_tokens()
except Exception as e:
    pass