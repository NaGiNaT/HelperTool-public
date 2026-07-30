import random
import re
import datetime
import time as tm
import pyautogui as pag
from tzlocal import get_localzone
from PyQt5.QtCore import QThread, pyqtSignal

from core.helpers import pressing_key, add_timezone_to_str
from core.globals import my_id, screenshot_delay


class MuteActionsThread(QThread):
    finished_signal = pyqtSignal(str, str, str, str, str, str, str)

    def __init__(self, line: str, my_full_nickname: str, temp_nick: str, warns: str):
        super().__init__()
        self.line = line
        self.my_full_nickname = my_full_nickname
        self.temp_nick = temp_nick
        self.warns = warns
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.isRunning():
            self.wait(1000)

    def run(self):
        if self.should_stop:
            return
        tm.sleep(0.2)
        if self.should_stop:
            return

        pressing_key('t')
        current_date = datetime.datetime.now(get_localzone()).strftime("%d.%m.%Y")

        if self.should_stop:
            return
        global screenshot_delay
        tm.sleep(screenshot_delay)

        if self.should_stop:
            return
        screenshot = pag.screenshot()
        randid = int(datetime.datetime.now().timestamp() * 1000) + random.randint(1, 999)
        screenshot.save(f'./screenshot_{randid}.png')

        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})', self.line)
        timesi = time_match.group(1) if time_match else "00:00:00"
        last_time = add_timezone_to_str(timesi)

        if not self.should_stop:
            self.finished_signal.emit(
                str(my_id), self.my_full_nickname, str(randid),
                self.temp_nick, self.warns, current_date, last_time
            )


class WarnActionsThread(QThread):
    finished_signal = pyqtSignal(str, str, str, str, str, str, str)

    def __init__(self, line: str, my_full_nickname: str, temp_nick: str, warns: str):
        super().__init__()
        self.line = line
        self.my_full_nickname = my_full_nickname
        self.temp_nick = temp_nick
        self.warns = warns
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.isRunning():
            self.wait(1000)

    def run(self):
        if self.should_stop:
            return
        tm.sleep(0.2)
        if self.should_stop:
            return

        pressing_key('t')
        current_date = datetime.datetime.now(get_localzone()).strftime("%d.%m.%Y")

        if self.should_stop:
            return
        global screenshot_delay
        tm.sleep(screenshot_delay)

        if self.should_stop:
            return
        screenshot = pag.screenshot()
        randid = int(datetime.datetime.now().timestamp() * 1000) + random.randint(1, 999)
        screenshot.save(f'./screenshot_{randid}.png')

        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})', self.line)
        timesi = time_match.group(1) if time_match else "00:00:00"
        last_time = add_timezone_to_str(timesi)

        if not self.should_stop:
            self.finished_signal.emit(
                str(my_id), self.my_full_nickname, str(randid),
                self.temp_nick, self.warns, current_date, last_time
            )


class KickActionsThread(QThread):
    finished_signal = pyqtSignal(str, str, str, str, str, str)

    def __init__(self, my_full_nickname: str, temp_nick: str, warns: str,
                 current_date: str, last_time: str):
        super().__init__()
        self.my_full_nickname = my_full_nickname
        self.temp_nick = temp_nick
        self.warns = warns
        self.current_date = current_date
        self.last_time = last_time
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.isRunning():
            self.wait(1000)

    def run(self):
        if not self.should_stop:
            self.finished_signal.emit(
                str(my_id), self.my_full_nickname, self.temp_nick,
                self.warns, self.current_date, self.last_time
            )


class ScreenshotThread(QThread):
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self):
        super().__init__()
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        if self.isRunning():
            self.wait(1000)

    def run(self):
        if self.should_stop:
            return
        try:
            filename = f'screenshot_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            if not self.should_stop:
                screenshot = pag.screenshot()
                screenshot.save(filename)
            if not self.should_stop:
                self.finished_signal.emit(True, f"[SYSTEM] Скриншот создан: {filename}", filename)
        except Exception as e:
            if not self.should_stop:
                self.finished_signal.emit(False, f"[ERROR] Ошибка при создании скриншота: {e}", "")