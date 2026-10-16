import webbrowser
import urllib.parse
import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def open_google_search(word: str) -> None:
    url = "https://www.google.com/search?q=" + urllib.parse.quote(word)
    webbrowser.open(url)


def check_word(word: str) -> tuple[bool, str]:
    """
    Returns (found: bool, suggestion: str).
    found=True means Google returned results normally.
    suggestion is non-empty when Google shows "もしかして: XXX".
    """
    url = "https://www.google.com/search?q=" + urllib.parse.quote(word) + "&hl=ja"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")

        # "一致する情報は見つかりませんでした"
        no_results = any(
            "一致する情報は見つかりませんでした" in (el.get_text() or "")
            for el in soup.find_all(["div", "p"])
        )
        if no_results:
            return False, ""

        # "もしかして: XXX"
        spell = soup.find("a", {"class": "gL9Hy"}) or soup.find("span", {"class": "spell_orig"})
        if spell:
            return True, spell.get_text(strip=True)

        return True, ""
    except Exception as e:
        return True, f"(検索エラー: {e})"
