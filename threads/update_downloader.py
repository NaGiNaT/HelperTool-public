import os
import sys
import tempfile
import requests
from PyQt5.QtCore import QThread, pyqtSignal


class UpdateDownloaderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.isRunning():
            self.wait(2000)

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))

            tmp_dir = tempfile.gettempdir()
            filename = "HelperTool_Update.exe"
            filepath = os.path.join(tmp_dir, filename)

            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.should_stop:
                        f.close()
                        os.remove(filepath)
                        return
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = int(downloaded * 100 / total)
                        self.progress.emit(percent)

            self.finished.emit(True, filepath)

        except Exception as e:
            self.finished.emit(False, str(e))