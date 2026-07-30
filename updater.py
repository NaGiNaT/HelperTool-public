import requests
from config import VERSION, GITHUB_REPO


def check_for_update():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return False, VERSION, ""

        data = response.json()
        latest_tag = data["tag_name"].lstrip("v")

        if latest_tag != VERSION:
            download_url = ""
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break
            return True, latest_tag, download_url

        return False, VERSION, ""

    except Exception:
        return False, VERSION, ""


def get_release_page_url():
    return f"https://github.com/{GITHUB_REPO}/releases/latest"