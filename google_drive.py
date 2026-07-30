import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from cryptography.fernet import Fernet
from core.paths import resource_path

_GOOGLE_KEY_ENCRYPTION_KEY = b'mjAIZ6-f8LqZqDsGVsK3GH01Pmn3MBYnxipiLpbKYsk='

def _load_service_account_credentials():
    """Расшифровывает google_key.enc и загружает credentials"""
    with open(resource_path('google_key.enc'), 'rb') as f:
        encrypted_data = f.read()
    
    fernet = Fernet(_GOOGLE_KEY_ENCRYPTION_KEY)
    decrypted = fernet.decrypt(encrypted_data)
    
    return service_account.Credentials.from_service_account_info(
        eval(decrypted.decode('utf-8'))
    )

def download_file(file_id):
    credentials = _load_service_account_credentials()
    service = build('drive', 'v3', credentials=credentials)

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    return fh.getvalue()