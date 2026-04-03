import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import (
    ADMISSION_SERVICES,
    BUSINESS_SERVICES,
    CAF_SERVICES,
    EMBASSY_SERVICES,
    IMMIGRATION_SERVICES,
    PATRONATO_SERVICES,
    SUPPORT_SERVICES,
    app,
)


OUTPUT_DIR = BASE_DIR / "shared-hosting-static"

PAGES = {
    "/": "index.html",
    "/services": "services.html",
    "/news": "news.html",
    "/contact": "contact.html",
    "/appointments": "appointments.html",
    "/required-documents": "required-documents.html",
    "/privacy": "privacy.html",
    "/gdpr": "gdpr.html",
    "/legal": "legal.html",
    "/caf-services": "caf-services.html",
    "/patronato-services": "patronato-services.html",
    "/immigration-services": "immigration-services.html",
    "/admission-services": "admission-services.html",
    "/support-services": "support-services.html",
    "/business-services": "business-services.html",
    "/client-area": "client-area.html",
}

LINK_MAP = {
    "/services": "services.html",
    "/news": "news.html",
    "/contact": "contact.html",
    "/appointments": "appointments.html",
    "/required-documents": "required-documents.html",
    "/privacy": "privacy.html",
    "/gdpr": "gdpr.html",
    "/legal": "legal.html",
    "/caf-services": "caf-services.html",
    "/patronato-services": "patronato-services.html",
    "/immigration-services": "immigration-services.html",
    "/admission-services": "admission-services.html",
    "/support-services": "support-services.html",
    "/business-services": "business-services.html",
    "/client-area": "client-area.html",
}

DETAIL_LINK_MAP = {}

APPOINTMENT_FORM_SNIPPET = (
    '<form class="contact-form appointment-form" method="post" enctype="multipart/form-data">'
)
APPOINTMENT_FORM_SNIPPET_V3 = (
    '<form class="contact-form appointment-form" method="post" enctype="multipart/form-data" '
    'data-recaptcha-action="appointment">'
)
APPOINTMENT_FORM_SNIPPET_V3_AJAX = (
    '<form class="contact-form appointment-form" method="post" enctype="multipart/form-data" '
    'data-recaptcha-action="appointment" data-ajax="true">'
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def register_detail_pages() -> None:
    service_groups = [
        ("caf-services", CAF_SERVICES),
        ("patronato-services", PATRONATO_SERVICES),
        ("immigration-services", IMMIGRATION_SERVICES),
        ("embassy-services", EMBASSY_SERVICES),
        ("admission-services", ADMISSION_SERVICES),
        ("support-services", SUPPORT_SERVICES),
        ("business-services", BUSINESS_SERVICES),
    ]
    for prefix, services in service_groups:
        for slug in services.keys():
            route = f"/{prefix}/{slug}"
            filename = f"{prefix}-{slug}.html"
            PAGES[route] = filename
            DETAIL_LINK_MAP[route] = filename


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
    for path, filename in LINK_MAP.items():
        html = html.replace(f'href="{path}"', f'href="{filename}"')
    for path, filename in DETAIL_LINK_MAP.items():
        html = html.replace(f'href="{path}"', f'href="{filename}"')
    html = html.replace('href="/set-language/it"', 'href="/it/index.html"')
    html = html.replace('href="/set-language/en"', 'href="/en/index.html"')
    html = html.replace('href="/set-language/fa"', 'href="/fa/index.html"')
    if route == "/appointments":
        html = html.replace(
            APPOINTMENT_FORM_SNIPPET,
            '<form class="contact-form appointment-form" action="contact-form.php" method="post" enctype="multipart/form-data">',
        )
        html = html.replace(
            APPOINTMENT_FORM_SNIPPET_V3,
            '<form class="contact-form appointment-form" action="contact-form.php" method="post" '
            'enctype="multipart/form-data" data-recaptcha-action="appointment">',
        )
        html = html.replace(
            APPOINTMENT_FORM_SNIPPET_V3_AJAX,
            '<form class="contact-form appointment-form" action="contact-form.php" method="post" '
            'enctype="multipart/form-data" data-recaptcha-action="appointment" data-ajax="true">',
        )
    if route == "/contact":
        html = html.replace('action="/contact"', 'action="contact-form.php"')
    return html


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    register_detail_pages()
    copy_static_assets()
    client = app.test_client()
    langs = ["en", "it", "fa"]
    for lang in langs:
        client.get(f"/set-language/{lang}")
        for route, filename in PAGES.items():
            response = client.get(route)
            if response.status_code != 200:
                continue
            html = response.get_data(as_text=True)
            html = transform_html(html, route)
            lang_dir = OUTPUT_DIR / lang
            write_file(lang_dir / filename, html)
            if lang == "en":
                write_file(OUTPUT_DIR / filename, html)


if __name__ == "__main__":
    main()
