import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app


OUTPUT_DIR = BASE_DIR / "shared-hosting-static"

PAGES = {
    "/": "index.html",
    "/services": "services.html",
    "/news": "news.html",
    "/contact": "contact.html",
    "/appointments": "appointments.html",
    "/required-documents": "required-documents.html",
    "/caf-services": "caf-services.html",
    "/patronato-services": "patronato-services.html",
    "/immigration-services": "immigration-services.html",
    "/admission-services": "admission-services.html",
    "/support-services": "support-services.html",
    "/business-services": "business-services.html",
    "/client-area": "client-area.html",
}

LANG_SWITCHER_RE = re.compile(r'<div class="language-switcher">.*?</div>', re.DOTALL)
FORM_RE = re.compile(r"<form[^>]*>.*?</form>", re.DOTALL)


STATIC_APPOINTMENT_FORM = """
<form class="appointment-form" action="contact-form.php" method="post">
  <label for="full_name">Full name</label>
  <input id="full_name" name="full_name" type="text" required>

  <label for="email">Email</label>
  <input id="email" name="email" type="email" required>

  <label for="phone">Phone</label>
  <input id="phone" name="phone" type="tel" required>

  <label for="service">Service needed</label>
  <select id="service" name="service">
    <option>CAF</option>
    <option>Patronato</option>
    <option>Immigration</option>
    <option>Admission</option>
    <option>Gestione Imprese</option>
    <option>Others</option>
  </select>

  <label for="message">Message</label>
  <textarea id="message" name="message" rows="5" required></textarea>

  <button class="btn" type="submit">Send request</button>
</form>
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_static_assets() -> None:
    src = Path(__file__).resolve().parent.parent / "static"
    dest = OUTPUT_DIR / "static"
    if dest.exists():
        for root, _, files in os.walk(dest):
            for name in files:
                os.remove(Path(root) / name)
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dest / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            (dest / rel / name).write_bytes((Path(root) / name).read_bytes())


def transform_html(html: str, route: str) -> str:
    html = LANG_SWITCHER_RE.sub("", html)
    if route == "/appointments":
        html = FORM_RE.sub(STATIC_APPOINTMENT_FORM.strip(), html, count=1)
    return html


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_static_assets()
    client = app.test_client()
    for route, filename in PAGES.items():
        response = client.get(route)
        if response.status_code != 200:
            continue
        html = response.get_data(as_text=True)
        html = transform_html(html, route)
        write_file(OUTPUT_DIR / filename, html)


if __name__ == "__main__":
    main()
