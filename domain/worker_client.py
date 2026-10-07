import os

import requests


WORKER_URL = "https://helpertool-send.hiflexhelp.workers.dev"
APP_SECRET = "MNviKL4O9kEQ7fhiXWSGOYGwQge_3n"


def load_app_secret() -> str:
    return APP_SECRET


def _raise_for_response(response: requests.Response, action: str):
    if response.status_code == 200:
        return
    detail = (response.text or "").strip().replace("\n", " ")[:180]
    raise RuntimeError(f"Функция не приняла {action}: {response.status_code} {detail}".strip())


def send_tg_log(text: str):
    response = requests.post(
        WORKER_URL,
        json={"action": "tg_log", "text": text},
        headers={"Authorization": f"Bearer {load_app_secret()}"},
        timeout=30,
    )
    _raise_for_response(response, "копию в лог")


def send_vk_message(peer_id: str, text: str, photo_path: str = None):
    headers = {"Authorization": f"Bearer {load_app_secret()}"}
    if photo_path:
        with open(photo_path, "rb") as photo:
            response = requests.post(
                WORKER_URL,
                data={"action": "vk_message", "peer_id": str(peer_id), "text": text},
                files={"photo": (os.path.basename(photo_path), photo, "image/png")},
                headers=headers,
                timeout=60,
            )
    else:
        response = requests.post(
            WORKER_URL,
            json={"action": "vk_message", "peer_id": str(peer_id), "text": text},
            headers=headers,
            timeout=30,
        )
    _raise_for_response(response, "сообщение ВК")
