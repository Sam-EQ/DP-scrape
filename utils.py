from bs4 import BeautifulSoup
import hashlib


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["style", "script", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return "\n".join(line for line in text.splitlines() if line.strip())


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()