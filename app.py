import json
import os
import sqlite3
import uuid
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_PATH = DATA_DIR / "site.db"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["RECAPTCHA_SITE_KEY"] = os.environ.get(
    "RECAPTCHA_SITE_KEY",
    "6Ldhg6MsAAAAAECQbU46n3vPdpN2ySAgm5exACJB",
)

SUPPORTED_LANGS = {
    "it": "Italiano",
    "en": "English",
    "fa": "فارسی",
}

TRANSLATIONS = {
    "site_meta_description": {
        "it": "Servizi CAF, patronato, supporto immigrazione e pratiche consolari, check-list documenti, consulenza universitaria, gestione imprese e servizi pratici in Italia.",
        "en": "CAF services, patronato, immigration and consular support, required document checklists, university consulting, business management, and practical services in Italy.",
        "fa": "خدمات CAF، پاتروناتو، امور مهاجرت و کنسولی، فهرست مدارک لازم، مشاوره دانشگاهی، مدیریت کسب‌وکار و خدمات کاربردی در ایتالیا.",
    },
    "nav_home": {"it": "Home", "en": "Home", "fa": "خانه"},
    "nav_services": {"it": "Servizi", "en": "Services", "fa": "خدمات"},
    "nav_documents": {"it": "Documenti richiesti", "en": "Required Documents", "fa": "مدارک لازم"},
    "nav_news": {"it": "News", "en": "News", "fa": "اخبار"},
    "nav_contact": {"it": "Contatti", "en": "Contact", "fa": "تماس"},
    "nav_admin": {"it": "Admin", "en": "Admin", "fa": "مدیریت"},
    "nav_client_area": {"it": "Area Cliente", "en": "Client Area", "fa": "پنل مشتری"},
    "nav_book": {"it": "Prenota Appuntamento", "en": "Book Appointment", "fa": "رزرو وقت"},
    "nav_privacy": {"it": "Privacy Policy", "en": "Privacy Policy", "fa": "سیاست حفظ حریم خصوصی"},
    "nav_gdpr": {"it": "GDPR Notice", "en": "GDPR Notice", "fa": "اطلاعیه GDPR"},
    "nav_technical_trust": {"it": "Note Legali", "en": "Legal Notice", "fa": "اطلاعیه حقوقی"},
    "footer_all_services": {"it": "Tutti i Servizi", "en": "All Services", "fa": "همه خدمات"},
    "footer_rights": {"it": "Tutti i diritti riservati.", "en": "All rights reserved.", "fa": "تمامی حقوق محفوظ است."},
    "footer_legal_heading": {"it": "Legale", "en": "Legal", "fa": "حقوقی"},
    "footer_line_rights": {
        "it": "© 2026 SM SOLUTIONS. All rights reserved.",
        "en": "© 2026 SM SOLUTIONS. All rights reserved.",
        "fa": "© 2026 SM SOLUTIONS. All rights reserved.",
    },
    "footer_contact_line": {
        "it": "cafbixio5@gmail.com | +39 06 31072585",
        "en": "cafbixio5@gmail.com | +39 06 31072585",
        "fa": "cafbixio5@gmail.com | +39 06 31072585",
    },
    "footer_legal_name": {
        "it": "Cafbixio di Subbarao",
        "en": "Cafbixio di Subbarao",
        "fa": "Cafbixio di Subbarao",
    },
    "footer_registered_office": {
        "it": "Sede Legale: Via Bixio 5, Roma | P.IVA: da comunicare",
        "en": "Sede Legale: Via Bixio 5, Roma | P.IVA: to be provided",
        "fa": "Sede Legale: Via Bixio 5, Roma | P.IVA: در دست ارائه",
    },
    "footer_summary": {
        "it": "Servizi CAF, patronato, immigrazione, consulenza universitaria, gestione imprese e servizi pratici in Italia.",
        "en": "CAF services, patronato, immigration, university consulting, business management, and practical services in Italy.",
        "fa": "خدمات CAF، پاتروناتو، مهاجرت، مشاوره دانشگاهی، مدیریت کسب‌وکار و خدمات کاربردی در ایتالیا.",
    },
    "privacy_title": {
        "it": "Privacy Policy",
        "en": "Privacy Policy",
        "fa": "سیاست حفظ حریم خصوصی",
    },
    "privacy_intro": {
        "it": "Questa informativa descrive come SM SOLUTIONS raccoglie, utilizza e conserva i dati personali inviati tramite il sito.",
        "en": "This notice explains how SM SOLUTIONS collects, uses, and stores personal data submitted through the site.",
        "fa": "این اطلاعیه توضیح می‌دهد که SM SOLUTIONS چگونه داده‌های شخصی ارسال‌شده از طریق سایت را جمع‌آوری، استفاده و نگهداری می‌کند.",
    },
    "privacy_controller_title": {
        "it": "Titolare del trattamento",
        "en": "Data controller",
        "fa": "مسئول پردازش داده",
    },
    "privacy_controller_body": {
        "it": "Cafbixio di Subbarao, Via Bixio 5, 00185 Roma. Email: info@smdoniya.com.",
        "en": "Cafbixio di Subbarao, Via Bixio 5, 00185 Roma. Email: info@smdoniya.com.",
        "fa": "Cafbixio di Subbarao، Via Bixio 5، 00185 Roma. ایمیل: info@smdoniya.com.",
    },
    "privacy_vat_label": {
        "it": "Partita IVA",
        "en": "VAT (P.IVA)",
        "fa": "شماره مالیاتی (P.IVA)",
    },
    "privacy_vat_pending": {
        "it": "Da comunicare",
        "en": "To be provided",
        "fa": "در دست ارائه",
    },
    "privacy_data_title": {
        "it": "Dati raccolti",
        "en": "Data collected",
        "fa": "داده‌های جمع‌آوری‌شده",
    },
    "privacy_data_body": {
        "it": "Nome, email, telefono, dettagli della richiesta, città, tipo di servizio e documenti caricati tramite moduli di contatto e appuntamenti.",
        "en": "Name, email, phone, request details, city, service type, and uploaded documents submitted via the contact and appointment forms.",
        "fa": "نام، ایمیل، تلفن، جزئیات درخواست، شهر، نوع خدمت و مدارک بارگذاری‌شده از طریق فرم‌های تماس و رزرو.",
    },
    "privacy_purpose_title": {
        "it": "Finalità del trattamento",
        "en": "Purpose of processing",
        "fa": "هدف پردازش",
    },
    "privacy_purpose_body": {
        "it": "Gestire richieste, organizzare appuntamenti, preparare pratiche, rispondere ai clienti e mantenere archivi operativi.",
        "en": "Handle requests, organize appointments, prepare cases, respond to clients, and maintain operational records.",
        "fa": "مدیریت درخواست‌ها، تنظیم وقت‌ها، آماده‌سازی پرونده‌ها، پاسخ‌گویی به مشتریان و نگهداری سوابق عملیاتی.",
    },
    "privacy_legal_title": {
        "it": "Base giuridica",
        "en": "Legal basis",
        "fa": "مبنای قانونی",
    },
    "privacy_legal_body": {
        "it": "Esecuzione di servizi richiesti, adempimenti precontrattuali e obblighi di legge applicabili.",
        "en": "Performance of requested services, pre-contractual steps, and applicable legal obligations.",
        "fa": "اجرای خدمات درخواستی، اقدامات پیش از قرارداد و الزامات قانونی مربوط.",
    },
    "privacy_storage_title": {
        "it": "Conservazione e sicurezza",
        "en": "Storage and security",
        "fa": "نگهداری و امنیت",
    },
    "privacy_storage_body": {
        "it": "I dati e gli allegati vengono conservati sui server del sito per il tempo necessario a gestire le richieste e rispettare gli obblighi legali.",
        "en": "Data and attachments are stored on the site servers only for the time required to manage requests and meet legal obligations.",
        "fa": "داده‌ها و پیوست‌ها فقط برای مدت لازم جهت مدیریت درخواست‌ها و رعایت الزامات قانونی روی سرورهای سایت نگهداری می‌شوند.",
    },
    "privacy_rights_title": {
        "it": "Diritti dell’interessato",
        "en": "Your rights",
        "fa": "حقوق شما",
    },
    "privacy_rights_body": {
        "it": "Puoi richiedere accesso, rettifica, cancellazione o limitazione dei dati scrivendo a info@smdoniya.com.",
        "en": "You can request access, correction, deletion, or restriction by emailing info@smdoniya.com.",
        "fa": "می‌توانید با ارسال ایمیل به info@smdoniya.com درخواست دسترسی، اصلاح، حذف یا محدودسازی داده‌ها بدهید.",
    },
    "privacy_recaptcha_title": {
        "it": "Google reCAPTCHA",
        "en": "Google reCAPTCHA",
        "fa": "Google reCAPTCHA",
    },
    "privacy_recaptcha_body": {
        "it": "Usiamo Google reCAPTCHA per prevenire abusi. Il servizio può raccogliere dati tecnici secondo le policy di Google.",
        "en": "We use Google reCAPTCHA to prevent abuse. The service may collect technical data under Google’s policies.",
        "fa": "ما از Google reCAPTCHA برای جلوگیری از سوءاستفاده استفاده می‌کنیم. این سرویس ممکن است داده‌های فنی را طبق سیاست‌های گوگل جمع‌آوری کند.",
    },
    "privacy_changes_title": {
        "it": "Aggiornamenti",
        "en": "Updates",
        "fa": "به‌روزرسانی‌ها",
    },
    "privacy_changes_body": {
        "it": "Eventuali aggiornamenti saranno pubblicati su questa pagina.",
        "en": "Any updates will be published on this page.",
        "fa": "هرگونه به‌روزرسانی در همین صفحه منتشر می‌شود.",
    },
    "gdpr_title": {"it": "GDPR", "en": "GDPR", "fa": "GDPR"},
    "gdpr_intro": {
        "it": "Questa sezione riassume i diritti previsti dal Regolamento UE 2016/679.",
        "en": "This section summarizes rights under EU Regulation 2016/679.",
        "fa": "این بخش حقوق شما را طبق مقررات اتحادیه اروپا 2016/679 خلاصه می‌کند.",
    },
    "gdpr_rights_title": {
        "it": "Diritti principali",
        "en": "Key rights",
        "fa": "حقوق اصلی",
    },
    "gdpr_rights_body": {
        "it": "Accesso, rettifica, cancellazione, limitazione, portabilità e opposizione al trattamento quando applicabile.",
        "en": "Access, correction, deletion, restriction, portability, and objection to processing where applicable.",
        "fa": "دسترسی، اصلاح، حذف، محدودسازی، قابلیت انتقال و اعتراض به پردازش در موارد قابل اعمال.",
    },
    "gdpr_contact_title": {
        "it": "Richieste GDPR",
        "en": "GDPR requests",
        "fa": "درخواست‌های GDPR",
    },
    "gdpr_contact_body": {
        "it": "Per esercitare i diritti scrivi a info@smdoniya.com indicando nome, contatto e richiesta.",
        "en": "To exercise your rights, email info@smdoniya.com with your name, contact, and request.",
        "fa": "برای اعمال حقوق خود، با ذکر نام، اطلاعات تماس و درخواست به info@smdoniya.com ایمیل بزنید.",
    },
    "gdpr_storage_title": {
        "it": "Conservazione",
        "en": "Retention",
        "fa": "مدت نگهداری",
    },
    "gdpr_storage_body": {
        "it": "Conserviamo i dati solo per il tempo necessario alla gestione delle pratiche e agli obblighi di legge.",
        "en": "We retain data only as long as necessary to manage cases and comply with legal obligations.",
        "fa": "داده‌ها فقط برای مدت لازم جهت مدیریت پرونده‌ها و رعایت الزامات قانونی نگهداری می‌شوند.",
    },
    "gdpr_third_title": {
        "it": "Fornitori terzi",
        "en": "Third-party providers",
        "fa": "ارائه‌دهندگان ثالث",
    },
    "gdpr_third_body": {
        "it": "I dati possono essere trattati da fornitori tecnici (hosting, email, reCAPTCHA) per il solo scopo di erogare il servizio.",
        "en": "Data may be processed by technical providers (hosting, email, reCAPTCHA) only to deliver the service.",
        "fa": "داده‌ها ممکن است توسط ارائه‌دهندگان فنی (هاستینگ، ایمیل، reCAPTCHA) صرفاً برای ارائه خدمات پردازش شود.",
    },
    "legal_title": {"it": "Note Legali", "en": "Legal Notice", "fa": "اطلاعیه حقوقی"},
    "legal_intro": {
        "it": "Questa pagina riporta le informazioni legali essenziali del sito.",
        "en": "This page provides the essential legal information for the site.",
        "fa": "این صفحه اطلاعات حقوقی اصلی سایت را ارائه می‌کند.",
    },
    "legal_company_title": {
        "it": "Dati societari",
        "en": "Business details",
        "fa": "اطلاعات کسب‌وکار",
    },
    "legal_company_body": {
        "it": "Cafbixio di Subbarao, Via Bixio 5, 00185 Roma. Email: info@smdoniya.com.",
        "en": "Cafbixio di Subbarao, Via Bixio 5, 00185 Roma. Email: info@smdoniya.com.",
        "fa": "Cafbixio di Subbarao، Via Bixio 5، 00185 Roma. ایمیل: info@smdoniya.com.",
    },
    "legal_services_title": {
        "it": "Servizi",
        "en": "Services",
        "fa": "خدمات",
    },
    "legal_services_body": {
        "it": "Le informazioni e i servizi sono forniti per supporto amministrativo e organizzativo; requisiti e tempi dipendono dagli enti competenti.",
        "en": "Information and services are provided for administrative and organizational support; requirements and timelines depend on the competent authorities.",
        "fa": "اطلاعات و خدمات برای پشتیبانی اداری و سازمانی ارائه می‌شود؛ الزامات و زمان‌بندی‌ها به نهادهای ذی‌صلاح بستگی دارد.",
    },
    "legal_liability_title": {
        "it": "Limitazione di responsabilità",
        "en": "Limitation of liability",
        "fa": "محدودیت مسئولیت",
    },
    "legal_liability_body": {
        "it": "Il sito non garantisce esiti o tempi delle pratiche, che dipendono da enti pubblici e terzi.",
        "en": "The site does not guarantee outcomes or timelines, which depend on public bodies and third parties.",
        "fa": "این سایت نتیجه یا زمان‌بندی قطعی را تضمین نمی‌کند زیرا وابسته به نهادهای دولتی و اشخاص ثالث است.",
    },
    "legal_contact_title": {
        "it": "Contatti legali",
        "en": "Legal contact",
        "fa": "تماس حقوقی",
    },
    "legal_contact_body": {
        "it": "Per richieste legali o amministrative scrivi a info@smdoniya.com.",
        "en": "For legal or administrative requests, email info@smdoniya.com.",
        "fa": "برای درخواست‌های حقوقی یا اداری به info@smdoniya.com ایمیل بزنید.",
    },
    "updates_title": {"it": "Ultimi Aggiornamenti", "en": "Latest Updates", "fa": "آخرین به‌روزرسانی‌ها"},
    "view_all_news": {"it": "Vedi tutte le news", "en": "View all news", "fa": "مشاهده همه اخبار"},
    "featured_service": {"it": "Servizio in Evidenza", "en": "Featured Service", "fa": "خدمت ویژه"},
    "hero_title": {
        "it": "Prepara 730, ISEE e le principali pratiche annuali da un unico centro servizi.",
        "en": "Prepare your 730, ISEE, and main annual practices from one service center.",
        "fa": "پرونده‌های 730، ISEE و مهم‌ترین امور سالانه را از یک مرکز خدمات پیگیری کنید.",
    },
    "hero_lead": {
        "it": "ciaocaf unisce CAF, patronato, immigrazione, consulenza universitaria, gestione imprese e servizi pratici in un flusso di lavoro organizzato.",
        "en": "ciaocaf combines CAF, patronato, immigration, university consulting, business management, and practical support in one structured workflow.",
        "fa": "ciaocaf خدمات CAF، پاتروناتو، مهاجرت، مشاوره دانشگاهی، مدیریت کسب‌وکار و پشتیبانی کاربردی را در یک فرایند منظم ارائه می‌کند.",
    },
    "quick_access": {"it": "Accesso Rapido", "en": "Quick Access", "fa": "دسترسی سریع"},
    "quick_access_title": {
        "it": "Inizia dal servizio che ti serve.",
        "en": "Start from the service you need.",
        "fa": "از خدمتی که نیاز دارید شروع کنید.",
    },
    "qa_book_desc": {
        "it": "Prenota il servizio e carica i tuoi documenti.",
        "en": "Book a service and upload your files.",
        "fa": "خدمت را رزرو کنید و مدارک خود را بارگذاری کنید.",
    },
    "qa_services_desc": {
        "it": "Consulta tutte le categorie e le singole pratiche.",
        "en": "Browse all categories and single practices.",
        "fa": "همه دسته‌ها و خدمات را ببینید.",
    },
    "qa_docs_desc": {
        "it": "Controlla la checklist prima dell'appuntamento.",
        "en": "Check the checklist before the appointment.",
        "fa": "پیش از وقت، فهرست مدارک را بررسی کنید.",
    },
    "qa_news_desc": {
        "it": "Leggi aggiornamenti e promemoria stagionali.",
        "en": "Read updates and seasonal reminders.",
        "fa": "به‌روزرسانی‌ها و یادآوری‌های دوره‌ای را بخوانید.",
    },
    "qa_contact_desc": {
        "it": "Apri la pagina contatti e prenotazioni.",
        "en": "Open the contact and booking guidance page.",
        "fa": "صفحه تماس و راهنمای رزرو را باز کنید.",
    },
    "one_desk": {"it": "Uno Sportello", "en": "One Desk", "fa": "یک مرکز"},
    "one_desk_desc": {
        "it": "CAF, patronato, immigrazione, admission, others e gestione imprese in un unico posto",
        "en": "CAF, patronato, immigration, admission, others, and business management in one place",
        "fa": "CAF، پاتروناتو، مهاجرت، پذیرش، سایر خدمات و مدیریت کسب‌وکار در یک مکان",
    },
    "document_ready": {"it": "Documenti Pronti", "en": "Document Ready", "fa": "مدارک آماده"},
    "document_ready_desc": {
        "it": "I documenti richiesti sono collegati direttamente a ogni pagina servizio",
        "en": "Required documents are linked directly to each service detail page",
        "fa": "مدارک لازم مستقیماً به هر صفحه خدمت متصل شده‌اند.",
    },
    "appointment_flow": {"it": "Flusso Appuntamento", "en": "Appointment Flow", "fa": "فرآیند رزرو"},
    "appointment_flow_desc": {
        "it": "Prenota, carica file e tieni ogni pratica organizzata attraverso il sito",
        "en": "Book, upload files, and keep each case organized through the site",
        "fa": "از طریق سایت وقت بگیرید، فایل بارگذاری کنید و هر پرونده را منظم نگه دارید.",
    },
    "our_services": {"it": "I Nostri Servizi", "en": "Our Services", "fa": "خدمات ما"},
    "our_services_title": {
        "it": "Aree principali organizzate come una directory professionale.",
        "en": "Main service areas organized like a professional directory.",
        "fa": "بخش‌های اصلی خدمات مانند یک فهرست حرفه‌ای سازمان‌دهی شده‌اند.",
    },
    "view_all_caf": {"it": "Vedi tutti i servizi CAF", "en": "View all CAF services", "fa": "همه خدمات CAF"},
    "view_all_patronato": {"it": "Vedi tutti i servizi patronato", "en": "View all patronato services", "fa": "همه خدمات پاتروناتو"},
    "view_all_immigration": {"it": "Vedi tutti i servizi immigrazione", "en": "View all immigration services", "fa": "همه خدمات مهاجرت"},
    "view_all_business": {"it": "Vedi tutti i servizi imprese", "en": "View all business services", "fa": "همه خدمات کسب‌وکار"},
    "news_highlights": {"it": "News in Evidenza", "en": "News Highlights", "fa": "اخبار مهم"},
    "news_highlights_title": {
        "it": "News e promemoria stagionali sui servizi.",
        "en": "News and seasonal service reminders.",
        "fa": "اخبار و یادآوری‌های فصلی خدمات.",
    },
    "how_it_works": {"it": "Come Funziona", "en": "How It Works", "fa": "نحوه کار"},
    "how_it_works_title": {
        "it": "Un flusso piu semplice per ogni pratica.",
        "en": "A simpler workflow for each practice.",
        "fa": "یک روند ساده‌تر برای هر خدمت.",
    },
    "step_choose": {"it": "Scegli il servizio", "en": "Choose the service", "fa": "خدمت را انتخاب کنید"},
    "step_choose_desc": {
        "it": "Apri la directory e individua la pratica esatta che ti serve.",
        "en": "Open the directory and identify the exact practice you need.",
        "fa": "فهرست خدمات را باز کنید و خدمت دقیق موردنیاز را پیدا کنید.",
    },
    "step_read": {"it": "Leggi la checklist", "en": "Read the checklist", "fa": "فهرست را بخوانید"},
    "step_read_desc": {
        "it": "Usa la pagina servizio per controllare i documenti richiesti prima dell'appuntamento.",
        "en": "Use the service page to review the required documents before the appointment.",
        "fa": "پیش از رزرو، مدارک لازم را در صفحه خدمت بررسی کنید.",
    },
    "step_book": {"it": "Prenota e carica file", "en": "Book and upload files", "fa": "رزرو و بارگذاری فایل"},
    "step_book_desc": {
        "it": "Invia la richiesta con data, ora e documenti di supporto.",
        "en": "Send the request with your preferred date, time, and supporting documents.",
        "fa": "درخواست را با تاریخ، زمان و مدارک پشتیبان ارسال کنید.",
    },
    "need_help": {"it": "Hai Bisogno di Aiuto?", "en": "Need Help Now?", "fa": "به کمک نیاز دارید؟"},
    "need_help_title": {
        "it": "Usa la pagina appuntamenti o apri la directory completa dei servizi.",
        "en": "Use the appointment page or open the full services directory.",
        "fa": "از صفحه رزرو وقت استفاده کنید یا فهرست کامل خدمات را باز کنید.",
    },
    "need_help_desc": {
        "it": "Il sito accompagna il cliente dalla ricerca del servizio alla preparazione documenti e alla prenotazione.",
        "en": "The site is built to move clients directly from service search to document preparation and booking.",
        "fa": "این سایت کاربر را از جست‌وجوی خدمت تا آماده‌سازی مدارک و رزرو هدایت می‌کند.",
    },
    "contact_title": {"it": "Contatti", "en": "Contact", "fa": "تماس"},
    "contact_heading": {
        "it": "Contatti Roma.",
        "en": "Rome contact details.",
        "fa": "اطلاعات تماس رم.",
    },
    "contact_lead": {
        "it": "Trova recapiti, orari ufficio e mappa della sede di Via Bixio per contatti e appuntamenti.",
        "en": "Find office contacts, opening hours, and the Via Bixio map for direct contact and appointments.",
        "fa": "اطلاعات تماس، ساعات کاری و نقشه دفتر خیابان Bixio را برای تماس مستقیم و رزرو ببینید.",
    },
    "direct_contact": {"it": "Contatto Diretto", "en": "Direct Contact", "fa": "تماس مستقیم"},
    "office_details": {"it": "Dettagli ufficio", "en": "Office details", "fa": "اطلاعات دفتر"},
    "booking_guidance": {"it": "Guida Prenotazione", "en": "Booking Guidance", "fa": "راهنمای رزرو"},
    "prepare_visit": {"it": "Prepara la visita prima di arrivare.", "en": "Prepare the visit before you come.", "fa": "پیش از مراجعه، مدارک را آماده کنید."},
    "appointments_page": {"it": "Appuntamenti", "en": "Appointments", "fa": "وقت‌ها"},
    "appointments_heading": {"it": "Prenota appuntamenti e carica i file cliente.", "en": "Book appointments and upload client files.", "fa": "وقت رزرو کنید و فایل‌های مشتری را بارگذاری کنید."},
    "appointments_lead": {"it": "Questo modulo salva ogni richiesta nel database locale e archivia i file caricati per la revisione amministrativa.", "en": "This form stores each appointment request in the local database and saves uploaded files for admin review.", "fa": "این فرم هر درخواست را در پایگاه‌داده محلی ذخیره می‌کند و فایل‌های بارگذاری‌شده را برای بررسی مدیریت نگه می‌دارد."},
    "required_documents_title": {"it": "Documenti Richiesti", "en": "Required Documents", "fa": "مدارک لازم"},
    "required_documents_heading": {"it": "Un unico hub per le checklist collegate a ogni pagina servizio.", "en": "One hub for the checklists linked to every service page.", "fa": "یک مرکز واحد برای فهرست مدارک هر صفحه خدمت."},
    "required_documents_lead": {"it": "Apri la categoria che ti serve e scegli la pratica esatta per vedere i documenti richiesti, le note sul processo e il percorso di prenotazione.", "en": "Open the category you need, then choose the exact practice to see the required documents, process notes, and booking path.", "fa": "دسته موردنیاز را باز کنید و خدمت دقیق را انتخاب کنید تا مدارک لازم، روند و مسیر رزرو را ببینید."},
    "news_page_heading": {"it": "Aggiornamenti di servizio e promemoria pratici.", "en": "Service updates and practical reminders.", "fa": "به‌روزرسانی خدمات و یادآوری‌های کاربردی."},
    "news_page_lead": {"it": "Usa questa pagina per promemoria campagna, scadenze fiscali, aggiornamenti welfare e avvisi sulla preparazione documenti.", "en": "Use this page for campaign reminders, tax-season timing, welfare updates, and document-preparation notices.", "fa": "از این صفحه برای یادآوری کمپین‌ها، زمان‌بندی مالیاتی، به‌روزرسانی‌های رفاهی و اطلاعیه‌های مدارک استفاده کنید."},
    "client_area_heading": {"it": "Uno spazio dedicato ai servizi digitali per i clienti.", "en": "A dedicated space for digital client services.", "fa": "بخشی اختصاصی برای خدمات دیجیتال مشتریان."},
    "client_area_lead": {"it": "Questa pagina puo evolvere in area online per caricamento documenti, firme digitali, follow-up appuntamenti e aggiornamenti.", "en": "This page can evolve into your online area for document uploads, digital signatures, appointment follow-up, and service updates.", "fa": "این صفحه می‌تواند به ناحیه آنلاین برای بارگذاری مدارک، امضاهای دیجیتال، پیگیری وقت‌ها و به‌روزرسانی‌ها تبدیل شود."},
    "services_page_heading": {"it": "Panoramica completa dei servizi per chi ha bisogno di supporto pratico in Italia.", "en": "Full service overview for clients who need practical help in Italy.", "fa": "نمای کلی خدمات برای افرادی که در ایتالیا به کمک عملی نیاز دارند."},
    "nav_all_services": {"it": "Tutti i Servizi", "en": "All Services", "fa": "همه خدمات"},
    "nav_caf": {"it": "CAF", "en": "CAF", "fa": "CAF"},
    "nav_patronato": {"it": "Patronato", "en": "Patronato", "fa": "Patronato"},
    "nav_immigration": {"it": "Immigrazione", "en": "Immigration", "fa": "مهاجرت"},
    "nav_admission": {"it": "Ammissioni", "en": "Admission", "fa": "پذیرش"},
    "nav_others": {"it": "Others", "en": "Others", "fa": "سایر"},
    "nav_business": {"it": "Gestione Imprese", "en": "Business", "fa": "کسب‌وکار"},
    "footer_services_heading": {"it": "Servizi", "en": "Services", "fa": "خدمات"},
    "footer_support_heading": {"it": "Supporto", "en": "Support", "fa": "پشتیبانی"},
    "footer_main_services_heading": {"it": "Servizi Principali", "en": "Key Services", "fa": "خدمات اصلی"},
    "footer_brand_subtext": {
        "it": "CAF, patronato, immigrazione e supporto documentale a Roma",
        "en": "CAF, patronato, immigration, and document support in Rome",
        "fa": "خدمات CAF، پاتروناتو، مهاجرت و پشتیبانی مدارک در رم",
    },
    "footer_bottom_note": {
        "it": "Supporto CAF, patronato, immigrazione e assistenza su appuntamento a Roma.",
        "en": "Rome office support for CAF, patronato, immigration, and appointment-based assistance.",
        "fa": "پشتیبانی CAF، پاتروناتو، مهاجرت و خدمات با وقت در رم.",
    },
    "tag_service_scope": {"it": "Ambito Servizio", "en": "Service Scope", "fa": "دامنه خدمت"},
    "tag_who_needs": {"it": "Chi ne ha bisogno", "en": "Who Needs It", "fa": "چه کسانی نیاز دارند"},
    "tag_documents": {"it": "Documenti", "en": "Documents", "fa": "مدارک"},
    "tag_process": {"it": "Processo", "en": "Process", "fa": "روند"},
    "kicker_appointment": {"it": "Appuntamento", "en": "Appointment", "fa": "رزرو"},
    "kicker_notes": {"it": "Note importanti", "en": "Important Notes", "fa": "نکات مهم"},
    "kicker_reference": {"it": "Riferimenti", "en": "Reference Basis", "fa": "مبنای مرجع"},
    "appointment_use_form": {"it": "Usa il modulo appuntamenti e scegli", "en": "Use the appointment form and choose", "fa": "از فرم رزرو استفاده کنید و"},
    "appointment_as_type": {"it": "come tipologia di servizio.", "en": "as the service type.", "fa": "را به عنوان نوع خدمت انتخاب کنید."},
    "appointment_or_closest": {"it": "o l'opzione piu vicina.", "en": "or the closest related option.", "fa": "یا نزدیک‌ترین گزینه را انتخاب کنید."},
    "button_book": {"it": "Prenota", "en": "Book", "fa": "رزرو"},
    "button_open": {"it": "Apri", "en": "Open", "fa": "باز کردن"},
    "label_phone": {"it": "Telefono", "en": "Phone", "fa": "تلفن"},
    "label_email": {"it": "Email", "en": "Email", "fa": "ایمیل"},
    "label_address": {"it": "Indirizzo", "en": "Address", "fa": "آدرس"},
    "label_office_hours": {"it": "Orari ufficio", "en": "Office Hours", "fa": "ساعات کاری"},
    "label_google_maps": {"it": "Google Maps", "en": "Google Maps", "fa": "نقشه گوگل"},
    "label_open_maps": {"it": "Apri su Google Maps", "en": "Open in Google Maps", "fa": "باز کردن در گوگل مپس"},
    "label_browse_services": {"it": "Sfoglia tutti i servizi", "en": "Browse all services", "fa": "مشاهده همه خدمات"},
    "label_contact_form": {"it": "Modulo contatto", "en": "Contact Form", "fa": "فرم تماس"},
    "label_full_name": {"it": "Nome e cognome", "en": "Full name", "fa": "نام و نام خانوادگی"},
    "label_message": {"it": "Messaggio", "en": "Message", "fa": "پیام"},
    "label_upload_optional": {"it": "Carica documenti (opzionale)", "en": "Upload documents (optional)", "fa": "بارگذاری مدارک (اختیاری)"},
    "button_send_message": {"it": "Invia messaggio", "en": "Send message", "fa": "ارسال پیام"},
    "label_phone_whatsapp": {"it": "Telefono / WhatsApp", "en": "Phone / WhatsApp", "fa": "تلفن / واتساپ"},
    "label_service_type": {"it": "Tipo di servizio", "en": "Service Type", "fa": "نوع خدمت"},
    "label_select_service": {"it": "Seleziona un servizio", "en": "Select a service", "fa": "انتخاب خدمت"},
    "group_caf_services": {"it": "Servizi CAF", "en": "CAF Services", "fa": "خدمات CAF"},
    "group_patronato_services": {"it": "Servizi Patronato", "en": "Patronato Services", "fa": "خدمات پاتروناتو"},
    "group_immigration_consular": {"it": "Immigrazione e Consolare", "en": "Immigration & Consular", "fa": "مهاجرت و کنسولی"},
    "group_admission_services": {"it": "Servizi Ammissione", "en": "Admission Services", "fa": "خدمات پذیرش"},
    "group_business_services": {"it": "Servizi Imprese", "en": "Business Services", "fa": "خدمات کسب‌وکار"},
    "group_other_services": {"it": "Altri Servizi", "en": "Other Services", "fa": "سایر خدمات"},
    "label_city": {"it": "Citta", "en": "City", "fa": "شهر"},
    "label_upload_documents": {"it": "Carica documenti", "en": "Upload Documents", "fa": "بارگذاری مدارک"},
    "label_upload_hint": {"it": "Seleziona tutti i documenti insieme (Ctrl/Cmd o Shift).", "en": "Select all documents at once (Ctrl/Cmd or Shift).", "fa": "همه مدارک را یکجا انتخاب کنید (Ctrl/Cmd یا Shift)."},
    "label_add_document": {"it": "Aggiungi un altro file", "en": "Add another file", "fa": "افزودن فایل دیگر"},
    "label_case_notes": {"it": "Note pratica", "en": "Case Notes", "fa": "یادداشت پرونده"},
    "label_case_notes_placeholder": {"it": "Descrivi la pratica, documenti mancanti o urgenza.", "en": "Describe the case, missing documents, or urgency.", "fa": "شرح پرونده، مدارک ناقص یا فوریت."},
    "button_save_appointment": {"it": "Invia richiesta appuntamento", "en": "Save Appointment Request", "fa": "ثبت درخواست وقت"},
    "appointments_details": {"it": "Dettagli prenotazione", "en": "Booking Details", "fa": "جزئیات رزرو"},
    "appointments_detail_required": {"it": "I campi obbligatori vengono verificati prima del salvataggio", "en": "Required fields are validated before saving", "fa": "فیلدهای ضروری قبل از ثبت بررسی می‌شوند"},
    "appointments_detail_multiple": {"it": "Puoi allegare piu file nella stessa richiesta", "en": "Multiple files can be attached in one request", "fa": "امکان ارسال چند فایل در یک درخواست"},
    "appointments_detail_admin": {"it": "Le richieste sono visibili nella dashboard admin dopo l'accesso", "en": "Records are visible from the admin dashboard after sign-in", "fa": "پس از ورود، درخواست‌ها در داشبورد مدیریت دیده می‌شوند"},
    "appointments_detail_allowed": {"it": "File consentiti: PDF, JPG, PNG, DOC, DOCX", "en": "Allowed files: PDF, JPG, PNG, DOC, DOCX", "fa": "فایل‌های مجاز: PDF, JPG, PNG, DOC, DOCX"},
    "services_directory_kicker": {"it": "Directory Servizi", "en": "Services Directory", "fa": "فهرست خدمات"},
    "services_tag_tax": {"it": "Fisco / Dichiarazioni", "en": "Tax / Declarations", "fa": "مالیات / اظهارنامه"},
    "services_tag_welfare": {"it": "Modelli INPS / Welfare", "en": "INPS Forms / Welfare", "fa": "فرم‌های INPS / رفاه"},
    "services_tag_home": {"it": "Casa / Anagrafe", "en": "Home / Registry", "fa": "خانه / ثبت احوال"},
    "services_tag_immigration": {"it": "Immigrazione / Consolare", "en": "Immigration / Consular", "fa": "مهاجرت / کنسولی"},
    "services_tag_study": {"it": "Studio / Universita", "en": "Study / University", "fa": "تحصیل / دانشگاه"},
    "services_tag_business": {"it": "Autonomi / Imprese", "en": "Self-Employed / Business", "fa": "خویش‌فرما / کسب‌وکار"},
    "services_tag_other": {"it": "Altro", "en": "Other", "fa": "سایر"},
    "caf_appointment_flow": {"it": "Flusso Appuntamento", "en": "Appointment Flow", "fa": "روند رزرو"},
    "caf_appointment_detail": {"it": "Il cliente puo scegliere il servizio CAF esatto e caricare i documenti prima della visita.", "en": "Clients can choose the exact CAF service and upload documents before the visit.", "fa": "می‌توانید خدمت دقیق CAF را انتخاب و مدارک را قبل از مراجعه بارگذاری کنید."},
    "caf_booking_types": {"it": "Tipologie di prenotazione disponibili", "en": "Available Booking Types", "fa": "انواع رزرو"},
    "caf_book_button": {"it": "Prenota appuntamento CAF", "en": "Book CAF Appointment", "fa": "رزرو وقت CAF"},
    "immigration_consular_tag": {"it": "Consolare", "en": "Consular", "fa": "کنسولی"},
    "immigration_consular_kicker": {"it": "Supporto consolare incluso", "en": "Consular Support Included", "fa": "شامل خدمات کنسولی"},
    "immigration_consular_detail": {"it": "È possibile prenotare passaporto, OCI e rinuncia passaporto dalla stessa area immigrazione.", "en": "Book passport, OCI, and passport surrender support from the same immigration area.", "fa": "امکان رزرو پاسپورت، OCI و انصراف از پاسپورت در همین بخش وجود دارد."},
    "immigration_consular_services": {"it": "Servizi consolari", "en": "Consular Services", "fa": "خدمات کنسولی"},
    "immigration_book_button": {"it": "Prenota appuntamento immigrazione", "en": "Book Immigration Appointment", "fa": "رزرو وقت مهاجرت"},
    "embassy_services_intro": {"it": "Questa pagina è la directory dei servizi consolari. Ogni servizio ha la sua pagina dedicata, nello stesso stile dei servizi CAF.", "en": "This page is the consular services directory. Each service has its own page, matching the CAF service style.", "fa": "این صفحه فهرست خدمات کنسولی است. هر خدمت صفحه اختصاصی دارد."},
    "embassy_tag": {"it": "Consolare", "en": "Consular", "fa": "کنسولی"},
    "booking_kicker": {"it": "Prenotazione", "en": "Booking", "fa": "رزرو"},
    "embassy_booking_detail": {"it": "Il cliente puo selezionare il servizio consolare nel modulo appuntamenti e caricare i documenti prima della visita.", "en": "Clients can select the consular service in the appointment form and upload documents before the visit.", "fa": "خدمت کنسولی را در فرم رزرو انتخاب و مدارک را قبل از مراجعه بارگذاری کنید."},
    "embassy_available_services": {"it": "Servizi consolari disponibili", "en": "Available Consular Services", "fa": "خدمات کنسولی موجود"},
    "embassy_book_button": {"it": "Prenota appuntamento consolare", "en": "Book Consular Appointment", "fa": "رزرو وقت کنسولی"},
    "client_area_current_tag": {"it": "Uso attuale", "en": "Current Use", "fa": "وضعیت فعلی"},
    "client_area_future_tag": {"it": "Uso futuro", "en": "Future Use", "fa": "آینده"},
    "client_area_current_desc": {"it": "I clienti possono già prenotare appuntamenti e caricare file dal modulo di prenotazione.", "en": "Clients can already book appointments and upload files through the booking form.", "fa": "مشتریان می‌توانند از طریق فرم رزرو وقت بگیرند و مدارک را بارگذاری کنند."},
    "client_area_open_appointments": {"it": "Apri modulo appuntamenti", "en": "Open appointment form", "fa": "باز کردن فرم رزرو"},
    "client_area_future_desc": {"it": "In futuro questa area potrà collegarsi a storico file, firme e aggiornamenti appuntamenti.", "en": "This area can later connect to file history, signed forms, and appointment-status updates.", "fa": "در آینده این بخش به سابقه مدارک، فرم‌های امضا شده و وضعیت وقت متصل می‌شود."},
    "client_area_open_documents": {"it": "Apri hub documenti", "en": "Open document hub", "fa": "باز کردن مرکز مدارک"},
    "client_area_online_kicker": {"it": "Servizi online", "en": "Online Services", "fa": "خدمات آنلاین"},
    "client_area_online_item1": {"it": "Prenotare appuntamenti per tipologia di servizio", "en": "Book appointments by service type", "fa": "رزرو وقت بر اساس نوع خدمت"},
    "client_area_online_item2": {"it": "Verificare i documenti richiesti prima della visita", "en": "Review required documents before the visit", "fa": "بررسی مدارک لازم قبل از مراجعه"},
    "client_area_online_item3": {"it": "Preparare i file per pratiche fiscali, welfare, immigrazione e imprese", "en": "Prepare files for tax, welfare, immigration, and business cases", "fa": "آماده‌سازی فایل‌ها برای مالیات، رفاه، مهاجرت و کسب‌وکار"},
    "client_area_future_kicker": {"it": "Espansioni future", "en": "Future Expansion", "fa": "گسترش‌های آینده"},
    "client_area_future_item1": {"it": "Accesso allo storico documenti", "en": "Document-history access", "fa": "دسترسی به سابقه مدارک"},
    "client_area_future_item2": {"it": "Flussi firma digitale", "en": "Digital signature workflows", "fa": "روند امضای دیجیتال"},
    "client_area_future_item3": {"it": "Aggiornamenti stato pratica e promemoria", "en": "Client status updates and reminders", "fa": "به‌روزرسانی وضعیت پرونده و یادآوری‌ها"},
    "home_open_caf": {"it": "Apri servizi CAF", "en": "Open CAF services", "fa": "باز کردن خدمات CAF"},
    "home_open_patronato": {"it": "Apri servizi Patronato", "en": "Open Patronato services", "fa": "باز کردن خدمات پاتروناتو"},
    "home_open_immigration": {"it": "Apri servizi Immigrazione", "en": "Open Immigration services", "fa": "باز کردن خدمات مهاجرت"},
    "required_docs_kicker": {"it": "Come usare questa pagina", "en": "How To Use This Page", "fa": "نحوه استفاده از این صفحه"},
    "required_docs_steps_detail": {"it": "Ogni pagina servizio contiene documenti richiesti, note di processo e un pulsante prenotazione collegato al modulo appuntamenti.", "en": "Each detail page contains required documents, process notes, and a booking button connected to the appointment form.", "fa": "هر صفحه خدمت شامل مدارک لازم، نکات روند و دکمه رزرو متصل به فرم است."},
    "required_docs_best_kicker": {"it": "Best Practice", "en": "Best Practice", "fa": "بهترین روش"},
    "required_docs_prepare_detail": {"it": "Si ottengono risultati migliori quando documenti, ricevute, traduzioni e atti specifici sono organizzati prima della prenotazione.", "en": "Better results come when identity documents, receipts, translations, and service-specific records are organized before booking.", "fa": "نتیجه بهتر زمانی است که مدارک هویتی، رسیدها، ترجمه‌ها و مدارک خاص خدمت قبل از رزرو آماده باشند."},
    "nav_all_services": {"it": "Tutti i Servizi", "en": "All Services", "fa": "همه خدمات"},
    "nav_caf": {"it": "CAF", "en": "CAF", "fa": "CAF"},
    "nav_patronato": {"it": "Patronato", "en": "Patronato", "fa": "Patronato"},
    "nav_immigration": {"it": "Immigrazione", "en": "Immigration", "fa": "مهاجرت"},
    "nav_admission": {"it": "Ammissioni", "en": "Admission", "fa": "پذیرش"},
    "nav_others": {"it": "Others", "en": "Others", "fa": "سایر"},
    "nav_business": {"it": "Gestione Imprese", "en": "Business", "fa": "کسب‌وکار"},
    "footer_services_heading": {"it": "Servizi", "en": "Services", "fa": "خدمات"},
    "footer_support_heading": {"it": "Supporto", "en": "Support", "fa": "پشتیبانی"},
    "footer_main_services_heading": {"it": "Servizi Principali", "en": "Key Services", "fa": "خدمات اصلی"},
    "footer_brand_subtext": {
        "it": "CAF, patronato, immigrazione e supporto documentale a Roma",
        "en": "CAF, patronato, immigration, and document support in Rome",
        "fa": "خدمات CAF، پاتروناتو، مهاجرت و پشتیبانی مدارک در رم",
    },
    "footer_bottom_note": {
        "it": "Supporto CAF, patronato, immigrazione e assistenza su appuntamento a Roma.",
        "en": "Rome office support for CAF, patronato, immigration, and appointment-based assistance.",
        "fa": "پشتیبانی CAF، پاتروناتو، مهاجرت و خدمات با وقت در رم.",
    },
    "who_needs": {"it": "Chi ne ha bisogno", "en": "Who Needs This", "fa": "چه کسانی نیاز دارند"},
    "required_documents": {"it": "Documenti richiesti", "en": "Required Documents", "fa": "مدارک لازم"},
    "how_support_works": {"it": "Come funziona il supporto", "en": "How Support Works", "fa": "روند پشتیبانی"},
    "book_caf_service": {"it": "Prenota questo servizio CAF.", "en": "Book this CAF service.", "fa": "رزرو این خدمت CAF"},
    "book_patronato_service": {"it": "Prenota questo servizio patronato.", "en": "Book this patronato service.", "fa": "رزرو این خدمت پاتروناتو"},
    "book_immigration_service": {"it": "Prenota questo servizio immigrazione.", "en": "Book this immigration service.", "fa": "رزرو این خدمت مهاجرت"},
    "book_embassy_service": {"it": "Prenota questo servizio consolare.", "en": "Book this consular service.", "fa": "رزرو این خدمت کنسولی"},
    "book_admission_service": {"it": "Prenota questo servizio di consulenza educativa.", "en": "Book this educational consulting service.", "fa": "رزرو مشاوره آموزشی"},
    "caf_main_services": {"it": "Servizi CAF principali", "en": "Main CAF Services", "fa": "خدمات اصلی CAF"},
    "caf_admin_support": {"it": "Supporto CAF amministrativo", "en": "Administrative CAF Support", "fa": "پشتیبانی اداری CAF"},
    "caf_book_specific": {"it": "Prenota direttamente il supporto CAF.", "en": "Book specific CAF support directly.", "fa": "رزرو مستقیم پشتیبانی CAF"},
    "patronato_main_services": {"it": "Servizi patronato principali", "en": "Main Patronato Services", "fa": "خدمات اصلی پاتروناتو"},
    "patronato_additional_support": {"it": "Supporto patronato aggiuntivo", "en": "Additional Patronato Support", "fa": "پشتیبانی تکمیلی پاتروناتو"},
    "immigration_permesso_residency": {"it": "Permesso e residenza", "en": "Permesso and Residency", "fa": "اجازه اقامت و سکونت"},
    "immigration_family_status": {"it": "Supporto famiglia e status", "en": "Family and Status Support", "fa": "پشتیبانی خانواده و وضعیت"},
    "immigration_passport_oci": {"it": "Supporto passaporto e OCI", "en": "Passport and OCI Support", "fa": "پشتیبانی پاسپورت و OCI"},
    "immigration_embassy_note": {"it": "I servizi consolari sono inclusi qui.", "en": "Consular services are grouped here.", "fa": "خدمات کنسولی در این بخش قرار دارند."},
    "embassy_services_heading": {
        "it": "Pagine servizio per passaporto, OCI e rinuncia.",
        "en": "Service pages for passport, OCI, and surrender.",
        "fa": "صفحات خدمات برای پاسپورت، OCI و انصراف",
    },
    "embassy_book_direct": {
        "it": "Prenota direttamente il supporto consolare.",
        "en": "Book consular support directly.",
        "fa": "رزرو مستقیم پشتیبانی کنسولی",
    },
    "home_latest_news": {"it": "Ultime news servizi", "en": "Latest service news", "fa": "آخرین اخبار خدمات"},
    "home_core_services": {"it": "Servizi principali piu richiesti.", "en": "Core services clients ask for most.", "fa": "خدمات اصلی پرتقاضا"},
    "home_core_caf": {"it": "CAF", "en": "CAF", "fa": "CAF"},
    "home_core_patronato": {"it": "Patronato", "en": "Patronato", "fa": "Patronato"},
    "home_core_immigration": {"it": "Immigrazione", "en": "Immigration", "fa": "مهاجرت"},
    "home_core_business_others": {"it": "Imprese e altri servizi", "en": "Business and Others", "fa": "کسب‌وکار و سایر خدمات"},
    "home_rome_office": {"it": "Sede di Roma", "en": "Rome office", "fa": "دفتر رم"},
    "contact_find_office": {"it": "Trova l'ufficio a Roma", "en": "Find the office in Rome", "fa": "یافتن دفتر در رم"},
    "contact_send_request": {
        "it": "Invia la richiesta e carica i documenti.",
        "en": "Send your request and upload documents.",
        "fa": "درخواست را ارسال و مدارک را بارگذاری کنید.",
    },
    "required_docs_steps_heading": {
        "it": "Inizia dalla categoria, poi apri la pratica.",
        "en": "Start with the category, then open the exact practice.",
        "fa": "از دسته شروع کنید و سپس خدمت دقیق را باز کنید.",
    },
    "required_docs_prepare_heading": {
        "it": "Prepara i documenti prima dell'appuntamento.",
        "en": "Prepare documents before the appointment.",
        "fa": "قبل از وقت مدارک را آماده کنید.",
    },
    "services_browse_heading": {"it": "Sfoglia i servizi per categoria.", "en": "Browse services by practical category.", "fa": "مرور خدمات بر اساس دسته"},
    "services_caf_tax": {"it": "CAF e supporto fiscale", "en": "CAF and tax support", "fa": "CAF و پشتیبانی مالیاتی"},
    "services_patronato_family": {"it": "Patronato e supporto famiglia", "en": "Patronato and family support", "fa": "پاتروناتو و پشتیبانی خانواده"},
    "services_home_municipal": {"it": "Casa e pratiche comunali", "en": "Home and municipal paperwork", "fa": "امور منزل و شهرداری"},
    "services_permesso_citizen": {
        "it": "Permesso, cittadinanza e servizi consolari",
        "en": "Permesso, citizenship, and consular services",
        "fa": "اجازه اقامت، شهروندی و خدمات کنسولی",
    },
    "services_admission": {"it": "Consulenza ammissioni", "en": "Admission consulting", "fa": "مشاوره پذیرش"},
    "services_business": {"it": "Gestione imprese", "en": "Business management", "fa": "مدیریت کسب‌وکار"},
    "services_everyday": {"it": "Servizi di supporto quotidiano", "en": "Everyday support services", "fa": "خدمات پشتیبانی روزمره"},
    "client_area_workflow": {"it": "Flusso appuntamenti e documenti", "en": "Appointment and document workflow", "fa": "روند وقت و مدارک"},
    "client_area_followup": {"it": "Area follow-up digitale", "en": "Digital follow-up area", "fa": "بخش پیگیری دیجیتال"},
    "admission_consulting": {"it": "Consulenza iscrizione universitaria", "en": "University Application Consulting", "fa": "مشاوره پذیرش دانشگاه"},
    "admission_help_with": {"it": "In cosa aiutiamo", "en": "What We Help With", "fa": "چه مواردی را پوشش می‌دهیم"},
    "admin_signin_heading": {
        "it": "Accedi per vedere le richieste.",
        "en": "Sign in to view appointment records.",
        "fa": "برای مشاهده درخواست‌ها وارد شوید.",
    },
    "admin_dashboard_heading": {
        "it": "Richieste salvate e file caricati.",
        "en": "Stored appointment records and uploaded files.",
        "fa": "درخواست‌های ذخیره‌شده و فایل‌های بارگذاری‌شده.",
    },
    "admin_dashboard_empty": {
        "it": "Nessuna richiesta salvata.",
        "en": "No appointment submissions have been saved.",
        "fa": "هیچ درخواستی ذخیره نشده است.",
    },
}


def get_lang() -> str:
    lang = session.get("lang", "en")
    return lang if lang in SUPPORTED_LANGS else "en"


def t(key: str) -> str:
    lang = get_lang()
    values = TRANSLATIONS.get(key, {})
    return values.get(lang) or values.get("en") or key


CAF_SERVICES = {
    "isee": {
        "name": "ISEE",
        "image": "service-images/custom/isee.png",
        "summary": "Support for ISEE document preparation and appointment-ready file organization.",
        "who_needs_it": [
            "Families applying for benefits linked to household economic status",
            "Students who need ISEE-related support for university or services",
            "Households that need an updated DSU/ISEE for ongoing administrative use",
        ],
        "documents": [
            "Identity document and codice fiscale for the declarant and household members",
            "Redditi, CU/730/Modello Redditi, and information on pensions or benefits received by the household",
            "Saldo and giacenza media for bank or postal accounts, plus property and rental data used in the DSU",
        ],
        "process": [
            "Review the household situation and the type of ISEE needed",
            "Organize the documents required for the DSU",
            "Check whether pre-filled or updated data must be verified",
            "Prepare the file for submission or assisted processing",
        ],
        "notes": [
            "ISEE rules and DSU requirements can change over time",
            "Some specific cases need more than the standard mini declaration",
            "Seasonal reminders highlight ISEE 2025 and ISEE 2026 updates at the start of the year",
            "ISEE availability updates are announced at the start of each campaign",
        ],
        "official_basis": [
            "INPS explains DSU and ISEE updates and availability of precompiled functionality",
        ],
    },
    "730": {
        "name": "730",
        "image": "service-images/custom/730.png",
        "summary": "Assistance for 730 declaration paperwork and related supporting documents.",
        "who_needs_it": [
            "Workers and pensioners using the 730 declaration route",
            "Taxpayers who want help reviewing precompiled tax data",
            "Clients who need support checking deductible or credit-related documents",
            "Students who work and receive a CU and want to check for refunds or detrazioni",
        ],
        "documents": [
            "Documento di identita and codice fiscale of the taxpayer and spouse or dependants if included",
            "CU, pension certifications, and any income records used for the dichiarazione precompilata or ordinary 730",
            "Receipts for detrazioni and deduzioni such as medical expenses, rent, mortgage interest, school, insurance, and family charges",
            "Medical expense receipts, rental contract, and mortgage interest statements",
            "Education expenses for primary, secondary, high school, and university programs",
            "Insurance receipts (life, accident, disability/work incapacity, natural disaster)",
            "Funeral expenses, personal care expenses, and pet medical expenses",
            "Sports activity expenses for children and kindergarten expenses",
            "Donations to charitable organizations (ONLUS) and social security premiums",
            "Household service costs (colf/badanti), home renovation expenses, and apartment expenses",
        ],
        "process": [
            "Review whether the 730 is the right declaration route",
            "Confirm eligibility and precompiled availability before starting",
            "Check precompiled or client-provided data",
            "Organize deductions, credits, and supporting documents",
            "Prepare the file for assisted declaration submission",
        ],
        "notes": [
            "Pre-filled 730 data is typically available from April 15 and the submission window runs to September 30",
            "Who can use the 730: employees, pensioners, substitute-income recipients, cooperatives/agriculture/fishing workers, and Catholic priests",
            "Who cannot use the 730: Partita IVA holders, complex partnership income cases, and people with only foreign income",
            "Advantages: fast refund via salary or pension, no tax calculations, and no tax payment at submission in most cases",
            "Students without income usually do not need the 730; working students with a CU can use it for refunds and detrazioni",
            "If there is no sostituto d'imposta, an IBAN is needed to receive any refund",
            "The Agenzia delle Entrate provides precompiled returns that still need checking",
            "Final required documents vary by the taxpayer’s case",
        ],
        "official_basis": [
            "Agenzia delle Entrate explains the precompiled declaration and 730 workflow",
        ],
    },
    "imu": {
        "name": "IMU",
        "image": "service-images/custom/imu.png",
        "summary": "Support for IMU-related paperwork and payment preparation.",
        "who_needs_it": [
            "Property owners or taxpayers dealing with IMU obligations",
            "Clients who need help organizing payment-related documents",
        ],
        "documents": [
            "Documento di identita and codice fiscale of the taxpayer",
            "Cadastral data, visura, rogito, succession, or other documents identifying the property and ownership share",
            "Previous IMU or F24 payments, municipal rates, and any exemption or residence documentation relevant to the property",
        ],
        "process": [
            "Review the property and tax context",
            "Organize the data needed for the payment or review",
            "Prepare the supporting documents and payment workflow",
        ],
        "notes": [
            "IMU obligations depend on the type of property and municipality context",
        ],
        "official_basis": [
            "IMU is part of the standard tax and local-payment support usually connected with F24 workflows",
        ],
    },
    "red-icric": {
        "name": "RED / ICRIC",
        "summary": "Support for RED and ICRIC documentation and case preparation.",
        "who_needs_it": [
            "Pension or benefit holders involved in RED or ICRIC-related declarations",
            "Clients who need help organizing recurring declaration updates",
        ],
        "documents": [
            "Documento di identita, codice fiscale, and pension or benefit identification data",
            "Income declarations or supporting statements requested in the annual RED campaign",
            "Medical or responsibility declarations required for ICRIC or related invalidity-linked checks",
        ],
        "process": [
            "Identify whether the case relates to RED or ICRIC responsibilities",
            "Check the relevant supporting information",
            "Prepare the file for the applicable declaration or assisted transmission workflow",
        ],
        "notes": [
            "INPS campaign processes can require authorized channels or assisted operators",
        ],
        "official_basis": [
            "INPS provides dedicated RED and invalidity-related service areas for authorized intermediaries",
        ],
    },
    "cambio-residenza": {
        "name": "Cambio Residenza",
        "summary": "Support for change of residence paperwork and related municipal document preparation.",
        "who_needs_it": [
            "Residents changing address or municipal registration details",
            "Clients who need help collecting the paperwork for residence updates",
        ],
        "documents": [
            "Identity documents and codice fiscale of the applicant and family members moving",
            "Deed, registered rental contract, hospitality declaration, or owner authorization for the new address",
            "Vehicle data, family-status information, and any municipality-specific forms or attachments",
        ],
        "process": [
            "Review the residence-change situation",
            "Collect the documents linked to the new address or registration",
            "Prepare the file for the municipal or assisted submission process",
        ],
        "notes": [
            "Exact documents can vary depending on local municipal requirements",
            "In Rome, Modesta Valenti procedures may apply to clients without a fixed residence",
        ],
        "official_basis": [
            "Residence changes are commonly tied to municipal registry processes and supporting documentation",
        ],
    },
    "f24": {
        "name": "F24",
        "image": "service-images/custom/f24.png",
        "summary": "Assistance for F24 preparation and payment-related document organization.",
        "who_needs_it": [
            "Taxpayers who need to prepare or review F24 payments",
            "Clients making tax, contribution, or local-levy payments through F24",
        ],
        "documents": [
            "Codice fiscale and an identity document of the payer",
            "Tributo codes, ente code, reference period, and amounts due for the tax or contribution being paid",
            "Any previous F24, avviso di pagamento, or assessment notice needed to compile the model correctly",
        ],
        "process": [
            "Review the payment purpose and tax codes involved",
            "Prepare the F24-related supporting information",
            "Check deadlines and payment setup details",
        ],
        "notes": [
            "Agenzia delle Entrate offers F24 Web and telematic workflows for payments",
        ],
        "official_basis": [
            "Agenzia delle Entrate describes F24 Web as a free online way to compile and transmit F24 payments",
        ],
    },
    "bonus": {
        "name": "Bonus",
        "summary": "Support for bonus-related documentation and eligibility file preparation.",
        "who_needs_it": [
            "Families or individuals applying for benefit or bonus-related measures",
            "Clients who need help preparing the supporting documents for bonus requests",
        ],
        "documents": [
            "Documento di identita and codice fiscale of the applicant and household members when required",
            "ISEE or DSU documentation if the bonus is tied to household economic status",
            "Service-specific proofs such as rental, utility, family, disability, or school documents depending on the bonus requested",
        ],
        "process": [
            "Identify the type of bonus or allowance involved",
            "Check the required eligibility and support documents",
            "Prepare the file for assisted submission or follow-up",
        ],
        "notes": [
            "Bonus requirements vary depending on the specific scheme and timing",
            "Bonus affitto (rent contribution) requirements typically include ISEE thresholds, SPID/CIE/CNS, a rental contract, and a valid residence permit",
            "Bonus bollette reminders note that an updated ISEE is needed for energy-bill contributions",
        ],
        "official_basis": [
            "Many bonus-related procedures rely on household, income, and identity documentation",
        ],
    },
    "spid": {
        "name": "SPID",
        "summary": "Assistance for SPID activation readiness and supporting identity document checks.",
        "who_needs_it": [
            "Citizens who need digital identity access to public services",
            "Clients who want help preparing the documents before activation with an identity provider",
        ],
        "documents": [
            "Identity document",
            "Tax code",
            "Email address, mobile number, and if requested the health card or CIE/CNS needed by the chosen identity provider",
        ],
        "process": [
            "Identify the most suitable recognition method",
            "Check that identity and contact information are ready",
            "Prepare the user for activation with an authorized identity provider",
        ],
        "notes": [
            "SPID is used to access public-administration and participating private services",
            "Final activation depends on the chosen identity provider",
        ],
        "official_basis": [
            "SPID is the official digital identity system for access to Italian public services",
        ],
    },
    "pec": {
        "name": "PEC",
        "summary": "Support for PEC setup readiness and document organization for certified email-related needs.",
        "who_needs_it": [
            "Clients who need a PEC address for administrative, fiscal, or professional procedures",
            "Users who need help preparing identity and contact data before activation",
        ],
        "documents": [
            "Identity document",
            "Tax code",
            "Email address, mobile number, and where required the business or professional data used for activation",
        ],
        "process": [
            "Check the intended use of the PEC address",
            "Prepare the identity and registration information",
            "Assist with activation readiness and supporting setup steps",
        ],
        "notes": [
            "Final PEC activation depends on the provider chosen by the client",
            "PEC activation is typically completed quickly once documents are ready",
        ],
        "official_basis": [
            "PEC is commonly used in Italy for certified communications in administrative and business contexts",
        ],
    },
    "modello-redditi": {
        "name": "Modello Redditi",
        "image": "service-images/custom/modello-redditi.png",
        "summary": "Support for Modello Redditi documentation and preparation of related tax files.",
        "who_needs_it": [
            "Taxpayers whose situation is better matched to Modello Redditi than the 730 route",
            "Clients who need help collecting and organizing tax documents for filing",
        ],
        "documents": [
            "Documento di identita and codice fiscale of the taxpayer and any family members included in the declaration",
            "Income, withholding, and foreign or special-tax records not manageable through the ordinary 730 route",
            "Receipts and documents for deductions, credits, property income, investments, and any fiscal positions declared in the model",
        ],
        "process": [
            "Review the taxpayer profile and declaration route",
            "Organize the supporting tax documents",
            "Prepare the file for assisted declaration support",
        ],
        "notes": [
            "The right declaration route depends on the taxpayer’s specific situation",
        ],
        "official_basis": [
            "Public SmartCAF descriptions list Modello Redditi among supported services",
        ],
    },
    "successioni": {
        "name": "Successioni",
        "image": "service-images/custom/successioni.png",
        "summary": "Support for succession-related document collection and file organization.",
        "who_needs_it": [
            "Families handling succession paperwork",
            "Clients who need help preparing supporting documents for succession-related procedures",
        ],
        "documents": [
            "Identity documents and codice fiscale of heirs and deceased person, plus death certificate",
            "Family-status certificates, wills or declarations of heirship, and details of the estate shares",
            "Property deeds, cadastral data, bank or postal balances, and any debts or deductible funeral expenses linked to the succession",
        ],
        "process": [
            "Review the type of succession-related need",
            "Organize the personal, family, and property records involved",
            "Prepare the file for assisted succession handling steps",
        ],
        "notes": [
            "Succession cases can become document-heavy and may involve multiple authorities",
        ],
        "official_basis": [
            "Public SmartCAF app descriptions list succession services among supported areas",
        ],
    },
}

IMMIGRATION_SERVICES = {
    "kit-soggiorno": {
        "name": "Kit Soggiorno Filling",
        "summary": "Support for filling the kit soggiorno and preparing the required documents.",
        "who_needs_it": [
            "Applicants handling a permit-of-stay process that uses the postal kit workflow",
            "Clients who want help organizing forms before submission",
        ],
        "documents": [
            "Completed permit kit forms, a valid passport with photocopies of all used pages, and current permit if renewing",
            "Marca da bollo and postal payment receipts required for the permit procedure",
            "Case-specific documents such as work contract, enrollment certificate, family papers, housing proof, or income proof depending on permit type",
        ],
        "process": [
            "Review the type of permit or renewal case",
            "Check the documents and forms required for the kit",
            "Prepare the file before the client proceeds to submission or appointment steps",
        ],
        "notes": [
            "Exact requirements depend on the permit category",
            "Official instructions and costs should always be checked on the immigration portal",
            "The kit can be completed in-office to avoid post office delays",
        ],
        "official_basis": [
            "Portale Immigrazione provides official guidance, office search, and cost information for the permit workflow",
        ],
    },
    "residence-permit": {
        "name": "Residence Permit Document Support",
        "summary": "Help organizing residence permit files and supporting paperwork.",
        "who_needs_it": [
            "Clients preparing for residence permit-related appointments or submissions",
            "Applicants who need help organizing a complete file",
        ],
        "documents": [
            "Passport, current permesso di soggiorno, four passport photos where requested, and copies of the identity pages",
            "Receipts showing postal filing or appointment booking plus any payment slips required by the Questura workflow",
            "Supporting documents linked to the permit basis, such as work, study, family, accommodation, health insurance, or income records",
        ],
        "process": [
            "Review the permit category and stage of the case",
            "Check document completeness and consistency",
            "Prepare the file for assisted follow-up or appointment readiness",
        ],
        "notes": [
            "Required documents vary materially by permit type and applicant status",
        ],
        "official_basis": [
            "Official permit workflows are tied to immigration-portal and public-authority procedures",
        ],
    },
    "document-translation": {
        "name": "Document Translation Support",
        "summary": "Support for translated documents and related file preparation.",
        "who_needs_it": [
            "Clients with foreign-language documents for immigration, study, or consular cases",
            "Applicants who need help organizing translated files before submission",
        ],
        "documents": [
            "Original documents to be translated and clear copies of each page",
            "Identity document of the applicant and any request form required by the receiving authority or translator",
            "Any legalization, apostille, or authority-specific checklist showing how the translated document must be presented",
        ],
        "process": [
            "Review which documents need translation support",
            "Organize originals, copies, and translated versions",
            "Prepare the file so it is usable for the relevant process",
        ],
        "notes": [
            "Some procedures require specific translation or legalization standards",
        ],
        "official_basis": [
            "Translation needs are process-dependent and should be matched to the receiving authority’s rules",
        ],
    },
    "international-documents": {
        "name": "International Document Support",
        "summary": "General support for international paperwork connected to migration and cross-border cases.",
        "who_needs_it": [
            "Clients with cross-border paperwork beyond one specific immigration form",
            "Applicants needing help preparing international document sets",
        ],
        "documents": [
            "Passport or identity document and the applicant's residence details",
            "Foreign civil-status, education, or administrative documents that will be presented in Italy or abroad",
            "Translations, apostille or legalization papers, and appointment confirmations required by the authority receiving the file",
        ],
        "process": [
            "Identify the authority or process involved",
            "Organize the document pack by use and priority",
            "Prepare the file for appointment or follow-up steps",
        ],
        "notes": [
            "International cases often combine immigration, translation, and consular elements",
        ],
        "official_basis": [
            "International document support should always be aligned with the authority receiving the file",
        ],
    },
    "ricongiungimento-familiare": {
        "name": "Ricongiungimento Familiare",
        "summary": "Support organizing family reunification files and related immigration documents.",
        "who_needs_it": [
            "Families preparing family reunification-related paperwork",
            "Clients who need help collecting relationship and residence-supporting documents",
        ],
        "documents": [
            "Passport copies of family members and documents proving the family relationship, duly legalized and translated where required",
            "Residence permit of the sponsor, accommodation suitability certificate, and proof of income",
            "Family-status records, housing papers, and any nulla osta or portal documents required for the reunification file",
        ],
        "process": [
            "Review the family reunification case type",
            "Check the documents linked to the family members involved",
            "Prepare the file for assisted submission or appointment readiness",
        ],
        "notes": [
            "Family reunification cases can require multiple linked documents for different persons",
            "In-office consultation is recommended for the full reunification procedure",
        ],
        "official_basis": [
            "Family reunification is a standard immigration case area requiring structured document support",
        ],
    },
    "flussi": {
        "name": "Flussi",
        "summary": "Support for flussi-related case preparation and document organization.",
        "who_needs_it": [
            "Clients or families involved in flussi-related procedures",
            "Applicants who need help preparing the supporting documents before filing",
        ],
        "documents": [
            "Passport copy of the worker and identity details of the employer or sponsor",
            "Draft work contract, housing declaration, and employer income or company documents required for the decree flow",
            "Any online application receipts, quota references, or supporting records linked to the relevant decreto flussi",
        ],
        "process": [
            "Review the flussi-related route and timing",
            "Check supporting documents and any sponsor-related records",
            "Prepare the file for assisted handling",
        ],
        "notes": [
            "Flussi-related procedures are highly timing-sensitive and document-specific",
        ],
        "official_basis": [
            "Flussi procedures require careful file preparation and timing awareness",
        ],
    },
    "cittadinanza": {
        "name": "Cittadinanza",
        "summary": "Support organizing citizenship-related documents and case files.",
        "who_needs_it": [
            "Applicants preparing citizenship-related paperwork",
            "Families who need help collecting a complete citizenship support file",
        ],
        "documents": [
            "Passport or identity document, residence permit where applicable, and current residence certificates",
            "Birth certificate, criminal record certificates, and any marriage or family-status certificates required by the citizenship path",
            "Translations, legalizations, payment receipt, and the online application submission documents required by the Ministry workflow",
        ],
        "process": [
            "Review the citizenship path involved",
            "Organize personal, family, and residence-related records",
            "Prepare the file for assisted follow-up or digital handling",
        ],
        "notes": [
            "Citizenship cases can be document-heavy and may require translated records",
        ],
        "official_basis": [
            "Citizenship procedures are official public-administration processes with significant documentation needs",
        ],
    },
    "conversione-permesso": {
        "name": "Conversione Permesso",
        "summary": "Support for conversion-related residence permit document preparation.",
        "who_needs_it": [
            "Clients converting a permit from one basis to another",
            "Applicants who need help organizing the supporting file before follow-up steps",
        ],
        "documents": [
            "Current passport and valid residence permit with copies",
            "Documents proving the basis for the new status, such as work contract, study completion, or family documents",
            "Quota or portal receipts, payment receipts, and any accommodation or income proof required for the conversion route",
        ],
        "process": [
            "Review the current permit and intended conversion route",
            "Organize the supporting documents needed for the new status",
            "Prepare the case file for assisted handling",
        ],
        "notes": [
            "Required documents depend on both the existing and target permit basis",
            "Students can request conversion even before finishing their studies",
        ],
        "official_basis": [
            "Permit conversions are a standard immigration support area with case-specific documentation",
        ],
    },
    "asilo-politico": {
        "name": "Asilo Politico (Protezione Internazionale)",
        "summary": "Support organizing documents and guidance for asylum and international protection procedures.",
        "who_needs_it": [
            "Applicants requesting asylum or international protection",
            "Clients who want help preparing the initial file and supporting evidence",
        ],
        "documents": [
            "Passport or identity documents (if available) and any existing residence-permit records",
            "Police reports, personal statements, or evidence supporting the protection request",
            "Appointment receipts or any documentation issued by the competent office handling the protection case",
        ],
        "process": [
            "Review the applicant's protection request and current status",
            "Organize identity and supporting evidence documents",
            "Prepare the file for assisted follow-up or appointment readiness",
        ],
        "notes": [
            "Asylum procedures are supported with guidance from consultants and legal partners where needed",
        ],
        "official_basis": [
            "Protection requests require careful document organization before submission",
        ],
    },
}

EMBASSY_SERVICES = {
    "passport-application": {
        "name": "Passport Application Support",
        "summary": "Assistance preparing passport application files and required supporting documents.",
        "who_needs_it": [
            "Applicants preparing a passport-related case through the consular workflow",
            "Clients who want help organizing supporting documents before submission",
        ],
        "documents": [
            "Completed online application printout, current passport in original, and copies of the relevant passport pages",
            "Recent photographs matching mission specifications and proof of legal stay or residence in Italy",
            "Case-specific support such as address proof, spouse or minor documents, or police report and annexures for lost or damaged passports",
        ],
        "process": [
            "Check the service category and required paperwork",
            "Review form readiness and supporting documents",
            "Prepare the file before appointment or submission steps",
        ],
        "notes": [
            "Final requirements must be checked against the competent mission/provider instructions",
        ],
        "official_basis": [
            "Official mission/provider pages publish service steps and supporting-document expectations",
        ],
    },
    "oci-card": {
        "name": "OCI Card Application Support",
        "summary": "Support organizing OCI application files and pre-submission documentation.",
        "who_needs_it": [
            "Applicants preparing an OCI card case",
            "Clients who need help matching foreign and identity documents in one file set",
        ],
        "documents": [
            "Current foreign passport with at least six months validity and copy of legal residence status where required",
            "Proof of Indian origin such as old Indian passport, domicile or nativity certificate, or parents' or grandparents' Indian documents",
            "Photo, signature, and relationship documents such as birth or marriage certificates when the OCI claim is through parents or spouse",
        ],
        "process": [
            "Review the client’s OCI case profile",
            "Organize supporting documents and digital files",
            "Prepare the application pack before submission",
        ],
        "notes": [
            "OCI requirements can be very document-specific and should be verified against official instructions",
        ],
        "official_basis": [
            "Official mission/provider channels define OCI process steps and file expectations",
        ],
    },
    "passport-surrender": {
        "name": "Passport Surrender Support",
        "summary": "Help preparing passport surrender files and reducing documentation errors.",
        "who_needs_it": [
            "Applicants who need to prepare a passport surrender-related file",
            "Clients who want help reducing documentation mistakes before submission",
        ],
        "documents": [
            "Duly filled surrender or renunciation application and the original last Indian passport",
            "Current foreign passport and proof of acquired foreign nationality, such as naturalization certificate or citizenship certificate",
            "Photographs, declaration forms, and copies of the relevant passport and nationality pages required by the mission or provider",
        ],
        "process": [
            "Review the case and supporting documents",
            "Prepare forms and copies in the required format",
            "Organize the file for appointment or submission follow-up",
        ],
        "notes": [
            "Final requirements and fees should be checked with the competent official channel",
        ],
        "official_basis": [
            "Official mission/provider channels define surrender-related documentation and workflow",
        ],
    },
    "visa-services": {
        "name": "Visa Services Support",
        "summary": "Assistance preparing visa applications and supporting document packs.",
        "who_needs_it": [
            "Applicants preparing visa requests such as eVisa, tourist, transit, medical, or student visas",
            "Clients who need help organizing consular appointment documentation",
        ],
        "documents": [
            "Completed visa application form and passport with required validity",
            "Photographs, travel itinerary, and accommodation or invitation documents as required",
            "Financial proof, insurance, and supporting documents linked to the visa category",
        ],
        "process": [
            "Review the visa type and checklist",
            "Organize supporting documents and translations where needed",
            "Prepare the file for appointment or submission",
        ],
        "notes": [
            "Support is available for multiple visa categories including eVisa and student visas",
        ],
        "official_basis": [
            "Consular websites publish the official visa requirements and checklists",
        ],
    },
    "citizenship": {
        "name": "Citizenship (India) Support",
        "summary": "Support organizing citizenship-related documents for consular procedures.",
        "who_needs_it": [
            "Applicants preparing consular citizenship-related documentation",
            "Clients who need help organizing supporting identity and family documents",
        ],
        "documents": [
            "Passport and identity documents plus proof of legal stay where required",
            "Birth, marriage, or family-status certificates linked to the citizenship case",
            "Translations, legalization, and appointment receipts required by the mission or provider",
        ],
        "process": [
            "Review the citizenship-related request",
            "Organize identity and family documents",
            "Prepare the file for consular submission",
        ],
        "notes": [
            "Citizenship support is available alongside passport and OCI services",
        ],
        "official_basis": [
            "Consular procedures define the official document requirements",
        ],
    },
}

PATRONATO_SERVICES = {
    "disoccupazione": {
        "name": "DISCO-NASPI",
        "summary": "Support for unemployment-related paperwork and file preparation.",
        "who_needs_it": [
            "Workers dealing with unemployment-related administrative procedures",
            "Clients who need help organizing the documents for unemployment support cases",
        ],
        "documents": [
            "SPID, CIE, or CNS for online filing, plus identity document and codice fiscale",
            "Employment termination data, UNILAV or employer communications, and the latest employment contract information",
            "IBAN and any documents requested to prove recent work periods or contributory status for the unemployment measure involved",
        ],
        "process": [
            "Review the unemployment-related situation",
            "Check the required supporting documents",
            "Prepare the file for assisted follow-up or submission readiness",
        ],
        "notes": [
            "Exact requirements depend on the specific unemployment-related measure involved",
            "NASPI and DIS-COLL support is available for workers whose contract ended or who were dismissed",
        ],
        "official_basis": [
            "Patronato-style support commonly covers unemployment and related welfare paperwork",
        ],
    },
    "assegno-unico-patronato": {
        "name": "Assegno Unico Universale",
        "summary": "Patronato-side support for family-benefit paperwork and follow-up organization.",
        "who_needs_it": [
            "Families managing child-related support requests",
            "Clients who need help preparing family and welfare documentation",
        ],
        "documents": [
            "SPID, CIE, or CNS for online filing, plus identity and codice fiscale details of the parent",
            "Codice fiscale of the children, custody or separation documents if applicable, and family-status information",
            "IBAN and ISEE if the family wants the amount linked to the economic indicator",
        ],
        "process": [
            "Review the family case and type of support needed",
            "Organize the documents linked to the application or update",
            "Prepare the file for assisted handling",
        ],
        "notes": [
            "Requirements vary depending on the family situation and applicable rules",
            "An updated ISEE by February 28 helps keep full amounts for 2025",
        ],
        "official_basis": [
            "Patronato offices commonly assist with family-benefit related documentation",
        ],
    },
    "dimissioni": {
        "name": "Dimissioni",
        "summary": "Support for resignation-related digital or administrative filing preparation.",
        "who_needs_it": [
            "Workers who need help understanding resignation-related administrative steps",
            "Clients who want support preparing the data and documents before filing",
        ],
        "documents": [
            "SPID or CIE to access the official resignation portal",
            "Identity document, last employment contract, and latest payslip",
            "PEC email address of the employer when required for the resignation filing",
            "Employment contract data, employer details, and the worker's personal and contact information",
            "Any supporting records for protected categories, maternity-related suspension, or assisted filing when applicable",
        ],
        "process": [
            "Review the resignation situation",
            "Prepare the relevant employment and identity information",
            "Assist with the filing-readiness workflow",
        ],
        "notes": [
            "Some resignation procedures use dedicated digital workflows",
        ],
        "official_basis": [
            "Patronato-oriented assistance often covers resignation filing support",
        ],
    },
    "maternita": {
        "name": "Maternita",
        "summary": "Support organizing maternity-related welfare or administrative paperwork.",
        "who_needs_it": [
            "Clients preparing maternity-related documentation",
            "Families needing help with maternity support files",
        ],
        "documents": [
            "Identity document, codice fiscale, and medical certification of pregnancy or birth data depending on the benefit requested",
            "Employment information, INPS position details, and IBAN for payment where applicable",
            "Any leave, employer, or family documentation required for the specific maternity or parental benefit",
        ],
        "process": [
            "Review the maternity-related case",
            "Organize identity, family, and employment-related documents",
            "Prepare the file for assisted administrative handling",
        ],
        "notes": [
            "Required documents vary depending on the type of maternity-related request",
        ],
        "official_basis": [
            "Patronato services commonly include maternity-related support procedures",
        ],
    },
    "invalidita-civile": {
        "name": "Invalidita Civile",
        "summary": "Support for civil invalidity-related documentation and case preparation.",
        "who_needs_it": [
            "Clients preparing civil invalidity-related documentation",
            "Families helping a relative with disability-related administrative support",
        ],
        "documents": [
            "Identity document, codice fiscale, and the introductory medical certificate used to start the INPS procedure",
            "Specialist medical reports and health documentation supporting the disability claim",
            "Residence and contact details plus any delegation or guardian documents when another person files the case",
        ],
        "process": [
            "Review the case type and stage",
            "Organize the administrative and supporting records",
            "Prepare the file for assisted follow-up",
        ],
        "notes": [
            "Health and disability procedures can have specialized document requirements",
        ],
        "official_basis": [
            "Patronato services frequently include civil-invalidity related support",
        ],
    },
    "legge-104": {
        "name": "104",
        "summary": "Support for documentation connected to Law 104 related administrative needs.",
        "who_needs_it": [
            "Clients preparing files linked to Law 104-related benefits or protections",
            "Families organizing supporting documents for assistance procedures",
        ],
        "documents": [
            "Identity document and codice fiscale of the disabled person and, if relevant, the family member requesting benefits",
            "Medical and invalidity recognition documents linked to the handicap assessment",
            "Employment or care-related records when the request concerns permits, leave, or family assistance benefits",
        ],
        "process": [
            "Review the purpose of the Law 104-related request",
            "Organize supporting documents and declarations",
            "Prepare the file for assisted handling or follow-up",
        ],
        "notes": [
            "Document requirements vary depending on the specific request or benefit",
        ],
        "official_basis": [
            "Law 104-related support is a common patronato assistance area",
        ],
    },
    "pensione": {
        "name": "Pensione",
        "summary": "Support for pension-related paperwork and file preparation.",
        "who_needs_it": [
            "Clients preparing pension-related administrative requests",
            "Families or workers who need help organizing pension support files",
        ],
        "documents": [
            "Identity document, codice fiscale, and pension or contribution statement",
            "Employment history, contributory records, and any ricongiunzione or totalization documents where relevant",
            "IBAN and supporting civil-status or family documents when required for survivor or family-linked pension cases",
        ],
        "process": [
            "Review the pension-related situation",
            "Organize the contribution and personal records involved",
            "Prepare the file for assisted handling or follow-up",
        ],
        "notes": [
            "Pension procedures differ depending on the specific pension path or status",
        ],
        "official_basis": [
            "Patronato services commonly include pension-related assistance",
        ],
    },
    "naspi-dis-coll": {
        "name": "NASPI / DIS-COLL",
        "summary": "Support for NASPI or DIS-COLL-related unemployment documentation and case preparation.",
        "who_needs_it": [
            "Workers or collaborators preparing NASPI or DIS-COLL-related paperwork",
            "Clients who need help organizing unemployment support files",
        ],
        "documents": [
            "SPID, CIE, or CNS for the online procedure, plus identity document and codice fiscale",
            "Employment or collaboration contract data and the termination date or cause",
            "IBAN, employer details, and any supporting documents used to prove the right to NASPI or DIS-COLL",
        ],
        "process": [
            "Review the unemployment support route involved",
            "Organize the identity, employment, and termination documents",
            "Prepare the file for assisted handling",
        ],
        "notes": [
            "The applicable support measure depends on the person’s work situation",
        ],
        "official_basis": [
            "Public patronato-style service lists commonly separate general unemployment help from NASPI or DIS-COLL support",
        ],
    },
    "adi": {
        "name": "ADI",
        "summary": "Support for ADI-related administrative documentation and case preparation.",
        "who_needs_it": [
            "Clients needing help organizing ADI-related documentation",
            "Families preparing files for benefit or support-related administrative steps",
        ],
        "documents": [
            "ISEE in force, identity documents, and codice fiscale of all household members",
            "DSU-linked information, residence details, and any documents proving disability, minors, age, or care burden where relevant",
            "IBAN and documentation requested by INPS or social services for activation or follow-up of the ADI path",
        ],
        "process": [
            "Review the family or household case",
            "Prepare the relevant supporting records",
            "Organize the documentation for assisted follow-up",
        ],
        "notes": [
            "Exact requirements depend on the applicable ADI framework and case details",
        ],
        "official_basis": [
            "Public patronato-style service lists commonly include ADI support",
        ],
    },
}

ADMISSION_SERVICES = {
    "university-applications": {
        "name": "University Application Consulting",
        "summary": "Educational consulting for students applying to universities in Italy, including profile review and application planning.",
        "who_needs_it": [
            "Students comparing courses or universities in Italy",
            "Applicants who need help organizing academic and admissions documents",
            "Families seeking educational consulting before choosing a university pathway",
        ],
        "documents": [
            "Passport or identity document, academic transcripts, diploma or degree certificates",
            "Language certificates, CV, statement of purpose, and letters of recommendation if required by the university",
            "Any pre-enrolment, Universitaly, portfolio, or program-specific forms requested by the target institution",
        ],
        "process": [
            "Identify the target program or institution",
            "Review the admissions timeline and file requirements",
            "Prepare the application pack and next-step checklist",
        ],
        "notes": [
            "Admission requirements vary by university and program",
        ],
        "official_basis": [
            "Applicants should always confirm the final checklist with the target university",
        ],
    },
    "borsa-di-studio": {
        "name": "Borsa di Studio",
        "summary": "Support for scholarship applications and document preparation for eligible students.",
        "who_needs_it": [
            "Students applying for regional or municipal scholarships",
            "Families preparing supporting documents for scholarship applications",
        ],
        "documents": [
            "Identity document and codice fiscale of the student",
            "ISEE documentation within the required threshold",
            "School or university enrollment confirmation and any required forms",
        ],
        "process": [
            "Check the scholarship window and eligibility criteria",
            "Collect identity, enrollment, and ISEE documents",
            "Prepare the file for online submission",
        ],
        "notes": [
            "Scholarship deadlines and ISEE thresholds apply to Rome-based programs",
        ],
        "official_basis": [
            "Scholarship applications depend on the issuing authority's requirements",
        ],
    },
    "student-document-support": {
        "name": "University Admission Document Support",
        "summary": "Educational consulting support for organizing academic, translated, and application-related documents for university admissions.",
        "who_needs_it": [
            "Students with complex university application files",
            "Applicants who need help arranging translated or certified academic documents",
        ],
        "documents": [
            "Original diploma, transcript, and syllabus or declaration documents requested by the target university",
            "Passport, tax code if already available, and any prior visa or residence documents relevant to the admission path",
            "Official translations, legalization or apostille, and declarations of value or CIMEA statements where the institution requires them",
        ],
        "process": [
            "Review the student’s target use for the documents",
            "Organize originals, translations, and copies",
            "Prepare the file for submission or appointment support",
        ],
        "notes": [
            "Document expectations depend on the institution and purpose",
        ],
        "official_basis": [
            "Final admissions document rules come from the receiving institution",
        ],
    },
}

BUSINESS_SERVICES = {
    "partita-iva": {
        "name": "P. IVA",
        "summary": "Support for opening and organizing paperwork connected to P. IVA-related administrative needs.",
        "who_needs_it": [
            "Individuals starting a self-employed or business-related path",
            "Clients who need help organizing the basic file for P. IVA-related procedures",
        ],
        "documents": [
            "Documento di identita, codice fiscale, and residence or registered-address details",
            "Description of the activity with the correct ATECO code and the chosen tax regime data",
            "Where relevant, professional register data, PEC, and any authorization or business-start documents needed for the opening declaration",
        ],
        "process": [
            "Review the intended business or self-employment activity",
            "Prepare the identity and activity information",
            "Organize the file for assisted handling of the P. IVA-related process",
        ],
        "notes": [
            "The exact workflow depends on the business model and administrative route involved",
            "Consultations are available for opening or reviewing Partita IVA cases",
        ],
        "official_basis": [
            "The uploaded list includes P. IVA among the business-management services",
        ],
    },
    "fattura-elettronica": {
        "name": "Fattura Elettronica",
        "summary": "Support for electronic invoicing-related setup and document organization.",
        "who_needs_it": [
            "Individuals or businesses managing invoice-related administrative workflows",
            "Clients who need help understanding electronic invoicing documentation",
        ],
        "documents": [
            "Partita IVA, codice fiscale, and company or sole-trader registry details",
            "PEC or codice destinatario used for receiving electronic invoices",
            "Customer and supplier fiscal data plus the credentials or delegations needed for the chosen invoicing platform",
        ],
        "process": [
            "Review the invoicing context and practical needs",
            "Organize the business and fiscal records involved",
            "Prepare the file and supporting information for assisted setup or follow-up",
        ],
        "notes": [
            "Electronic invoicing setups differ depending on the business and software workflow used",
        ],
        "official_basis": [
            "The uploaded list includes Fattura Elettronica among business services",
        ],
    },
    "certificazione-unica": {
        "name": "UNICO",
        "summary": "Support for Certificazione Unica-related file organization and follow-up.",
        "who_needs_it": [
            "Clients who need help organizing Certificazione Unica-related tax documents",
            "Businesses or individuals reviewing CU-related records",
        ],
        "documents": [
            "Withholding agent data, codice fiscale, and company or employer identification details",
            "Income, withholding, social security, and tax data for the workers or collaborators covered by the CU",
            "Recipient personal details and any adjustments or conguaglio information needed to issue the certification",
        ],
        "process": [
            "Review the CU-related situation",
            "Organize supporting tax records",
            "Prepare the file for assisted handling or related tax workflows",
        ],
        "notes": [
            "CU-related work may connect with broader tax declaration support",
        ],
        "official_basis": [
            "The uploaded list includes CU/CUD-related support among business or fiscal services",
        ],
    },
    "camera-di-commercio": {
        "name": "Camera di Commercio",
        "summary": "Support for Chamber of Commerce-related paperwork and administrative file preparation.",
        "who_needs_it": [
            "Businesses or individuals dealing with chamber-related procedures",
            "Clients who need help organizing commercial registration paperwork",
        ],
        "documents": [
            "Identity document, codice fiscale, and company or sole-trader registration data",
            "Constitutive deed, statutes, or business-start forms when the practice concerns registration or changes",
            "Any delegated forms, digital-signature files, and supporting attachments required for the Registro Imprese filing",
        ],
        "process": [
            "Review the chamber-related need",
            "Organize identity, business, and administrative records",
            "Prepare the file for assisted follow-up",
        ],
        "notes": [
            "The exact chamber workflow depends on the business action required",
        ],
        "official_basis": [
            "The uploaded list includes Camera di Commercio among business services",
        ],
    },
    "scia": {
        "name": "SCIA",
        "summary": "Support for SCIA-related document preparation and administrative organization.",
        "who_needs_it": [
            "Clients preparing an activity-start or administrative-notice file",
            "Businesses needing help organizing SCIA-supporting documents",
        ],
        "documents": [
            "Identity document and company details of the person filing the SCIA",
            "Technical or professional requisites, floor plans, and premises-availability documents when the activity requires them",
            "Sector-specific declarations, attachments, and any accompanying permits or notifications required by the SUAP procedure",
        ],
        "process": [
            "Review the business activity and administrative scope",
            "Collect the supporting documents tied to the activity",
            "Prepare the file for assisted SCIA-related handling",
        ],
        "notes": [
            "SCIA requirements depend on the type of activity and local administration",
        ],
        "official_basis": [
            "The uploaded list includes SCIA among business-management services",
        ],
    },
    "riduzione-contributi-inps": {
        "name": "Riduzione Contributi INPS",
        "summary": "Support for artisans and shopkeepers requesting INPS contribution reductions.",
        "who_needs_it": [
            "Artigiani or commercianti applying for contribution reductions",
            "Clients who need help organizing documents for the INPS reduction request",
        ],
        "documents": [
            "Identity document and codice fiscale",
            "INPS position or registration details",
            "Any documents requested by INPS to confirm eligibility for the reduction",
        ],
        "process": [
            "Review the applicant's business status and eligibility",
            "Collect the INPS position data and supporting documents",
            "Prepare the file for assisted submission or follow-up",
        ],
        "notes": [
            "Contribution reductions can reach 35 percent with a February deadline",
        ],
        "official_basis": [
            "INPS procedures require documented eligibility for contribution reductions",
        ],
    },
    "corso-sab-ex-rec": {
        "name": "Corso SAB (ex REC)",
        "summary": "Support for the administrative side of the SAB qualification for food and beverage activities.",
        "who_needs_it": [
            "Clients starting or managing food and beverage businesses",
            "Applicants who need help organizing documents for SAB course enrollment",
        ],
        "documents": [
            "Identity document and codice fiscale",
            "Residence details and contact information",
            "Any enrollment or payment documentation required by the training provider",
        ],
        "process": [
            "Confirm the business activity and SAB requirement",
            "Organize enrollment documents",
            "Prepare the file for assisted registration support",
        ],
        "notes": [
            "SAB (ex REC) course support is available for food and beverage activities",
        ],
        "official_basis": [
            "Local rules and training providers define SAB documentation requirements",
        ],
    },
}

SUPPORT_SERVICES = {
    "traduzioni-legalizzazione": {
        "name": "Traduzioni e Legalizzazione Documenti",
        "summary": "Support organizing translated and legalization-related document workflows.",
        "who_needs_it": [
            "Clients preparing foreign or multilingual documents for official use",
            "Applicants who need help managing translation and legalization steps",
        ],
        "documents": [
            "Original or certified-copy documents to be translated, legalized, or apostilled",
            "Identity document of the applicant and any delegation if another person deposits or collects the documents",
            "Translated versions, appointment receipts, and authority-specific request forms where the receiving office requires them",
        ],
        "process": [
            "Review which documents need translation or legalization support",
            "Organize originals, copies, and translated files",
            "Prepare the case file for the relevant authority or appointment",
        ],
        "notes": [
            "Requirements depend on the authority receiving the documents",
        ],
        "official_basis": [
            "The uploaded list explicitly includes translations and document legalization support",
        ],
    },
    "test-lingua-a2": {
        "name": "Test Lingua Italiana A2",
        "summary": "Support for preparing the administrative side of Italian language test related needs.",
        "who_needs_it": [
            "Clients who need help understanding the administrative steps around the A2 language test",
            "Applicants preparing documents linked to language-related requirements",
        ],
        "documents": [
            "Identity document and codice fiscale",
            "Residence permit or residence documentation if the exam is being used for an immigration procedure",
            "Exam registration confirmation, payment receipt, and any institution-specific application form",
        ],
        "process": [
            "Review the purpose of the A2 language test in the client’s case",
            "Organize the supporting administrative documents",
            "Prepare the file for registration or follow-up support",
        ],
        "notes": [
            "Testing procedures depend on the institution or authority involved",
        ],
        "official_basis": [
            "The uploaded list includes Test Lingua Italiana A2 as a separate support service",
        ],
    },
    "esenzione-tari": {
        "name": "Esenzione TARI",
        "summary": "Support for TARI exemption requests and related document preparation.",
        "who_needs_it": [
            "Residents requesting TARI exemption or reductions",
            "Clients who need help organizing the documents for the municipal application",
        ],
        "documents": [
            "SPID for online access and identity document with codice fiscale",
            "AMA or municipal user number where required",
            "ISEE documentation within the required threshold",
        ],
        "process": [
            "Check the municipality-specific exemption requirements",
            "Organize identity and ISEE documents",
            "Prepare the file for online submission or assisted follow-up",
        ],
        "notes": [
            "TARI exemption requests follow ISEE thresholds and February deadlines",
        ],
        "official_basis": [
            "Municipal exemption procedures rely on identity and ISEE documentation",
        ],
    },
    "domanda-mensa": {
        "name": "Domanda Mensa (Agevolazione Tariffaria)",
        "summary": "Support for school canteen fee-reduction applications and document readiness.",
        "who_needs_it": [
            "Families applying for school meal fee reductions",
            "Clients preparing school-year application documents",
        ],
        "documents": [
            "Identity document and codice fiscale of the applicant and student",
            "ISEE documentation for the household",
            "School enrollment details and any municipality-specific forms",
        ],
        "process": [
            "Confirm the school-year window and eligibility criteria",
            "Collect identity and ISEE documents",
            "Prepare the file for online submission",
        ],
        "notes": [
            "2025/26 school-year applications typically open from March to September",
        ],
        "official_basis": [
            "School meal fee reductions are tied to ISEE documentation and municipal procedures",
        ],
    },
    "asilo-nido-iscrizione": {
        "name": "Iscrizione Asilo Nido",
        "summary": "Support for enrollment in educational services (asilo nido) and related documents.",
        "who_needs_it": [
            "Families enrolling children in early education services",
            "Clients who need help with online enrollment and document preparation",
        ],
        "documents": [
            "Identity document and codice fiscale of the child and parents",
            "ISEE documentation and residence details when required",
            "Enrollment forms or online application confirmations",
        ],
        "process": [
            "Verify the enrollment window and age requirements",
            "Organize identity and ISEE documents",
            "Prepare the file for online enrollment support",
        ],
        "notes": [
            "Online enrollment windows apply for the 2025/26 school year",
        ],
        "official_basis": [
            "Enrollment requirements depend on municipality and school-service rules",
        ],
    },
    "appartamenti-affitto-garanzie": {
        "name": "Appartamenti / Affitto / Garanzie",
        "summary": "Support organizing housing-related paperwork, rental information, and guarantee documents.",
        "who_needs_it": [
            "Clients looking for help with rental-related documentation",
            "People who need support understanding housing paperwork before signing or applying",
        ],
        "documents": [
            "Identity documents and codice fiscale of the tenant or guarantor",
            "Employment contract, payslips, tax return, or guarantor income documents commonly requested by landlords or agencies",
            "Rental proposal, existing contract, residence permit if applicable, and any deposit or guarantee documentation",
        ],
        "process": [
            "Review the housing or rental situation",
            "Organize the documents required for the next housing step",
            "Prepare the file for rental or guarantee-related follow-up",
        ],
        "notes": [
            "Housing requirements vary by landlord, agency, and contract situation",
            "Bonus affitto requirements include ISEE thresholds, a rental contract, and SPID/CIE/CNS",
        ],
        "official_basis": [
            "The uploaded list includes apartment, rent, and guarantee support",
        ],
    },
    "assicurazione-auto-moto": {
        "name": "Assicurazione Auto / Moto",
        "summary": "Support organizing identity and vehicle documents for insurance-related assistance.",
        "who_needs_it": [
            "Vehicle owners who need help organizing documents before an insurance-related step",
            "Clients who want support preparing the file for auto or moto insurance follow-up",
        ],
        "documents": [
            "Identity document, codice fiscale, and driving licence of the insured person or vehicle owner",
            "Vehicle registration document and any certificate of ownership or plate details",
            "Previous insurance policy, attestato di rischio, and any documents relating to additional drivers or claims history",
        ],
        "process": [
            "Review the vehicle and insurance context",
            "Organize the identity and vehicle records",
            "Prepare the file for assisted follow-up",
        ],
        "notes": [
            "Insurance offers and requirements vary by provider",
        ],
        "official_basis": [
            "The uploaded list includes insurance support for auto and moto",
        ],
    },
    "tessera-sanitaria-codice-fiscale": {
        "name": "Tessera Sanitaria / Codice Fiscale",
        "summary": "Support for health-card and tax-code related administrative paperwork.",
        "who_needs_it": [
            "Clients who need help organizing identity and health-related administrative documents",
            "Applicants handling health-card or tax-code support steps",
        ],
        "documents": [
            "Passport or identity document and codice fiscale if already assigned",
            "Residence permit or residence-registration documents where the office requires proof of legal stay in Italy",
            "Health registration forms, family-status data, or delegation documents depending on whether the request is for codice fiscale, duplicate card, or health-card issue",
        ],
        "process": [
            "Review the requested administrative action",
            "Collect the supporting identity and residence documents",
            "Prepare the file for assisted follow-up",
        ],
        "notes": [
            "Requirements vary depending on the person’s status and the office involved",
        ],
        "official_basis": [
            "The uploaded list explicitly includes tessera sanitaria and codice fiscale support",
        ],
    },
    "account-registration-apps": {
        "name": "Account Registration (Glovo / Deliveroo / Just Eat)",
        "summary": "Support for app-account registration readiness and related document organization.",
        "who_needs_it": [
            "Clients who need help preparing the documents used for platform account registration",
            "Applicants organizing identity, contact, or work-related information for account setup",
        ],
        "documents": [
            "Identity document, tax code, and contact details used to create the rider or courier account",
            "Residence permit for non-EU citizens and driving licence plus vehicle insurance when the platform and vehicle type require them",
            "IBAN, vehicle information, and any platform onboarding forms or tax-registration details requested by Glovo, Deliveroo, or Just Eat",
            "When applicable, Modello AA9/12 and visura camerale documentation",
        ],
        "process": [
            "Review the platform and account requirements",
            "Organize the supporting registration information",
            "Prepare the user for the next registration step",
        ],
        "notes": [
            "Platform requirements vary by service and account type",
            "Support is available for Glovo updates and Uber Eats-related employment claims",
        ],
        "official_basis": [
            "The uploaded list includes account registration support for Glovo, Deliveroo, and Just Eat",
        ],
    },
    "rider-compensation": {
        "name": "Rider Claims (TFR / Wage Differences)",
        "summary": "Support for riders seeking guidance on TFR or unpaid wage differences from platform work.",
        "who_needs_it": [
            "Former riders of Uber Eats or other delivery platforms with unpaid compensation questions",
            "Clients who need help organizing documents for labor-related support",
        ],
        "documents": [
            "Identity document and codice fiscale",
            "Proof of platform work such as contracts, emails, or app history",
            "Payment records, payslips, or bank statements showing received amounts",
        ],
        "process": [
            "Review the rider's work history and claims",
            "Organize supporting employment and payment records",
            "Prepare the file for assisted follow-up or referral",
        ],
        "notes": [
            "Uber Eats ended operations in Italy in July 2023 and riders may be entitled to TFR or wage differences",
        ],
        "official_basis": [
            "Labor-related claims depend on the individual work history and supporting documents",
        ],
    },
    "abbonamento-agevolazione": {
        "name": "Abbonamento Agevolazione",
        "summary": "Support for reduced-fare subscription applications and the related document preparation.",
        "who_needs_it": [
            "Clients applying for transport or service subscriptions with agevolazione requirements",
            "Students, workers, seniors, or families who need help organizing the documents for discounted subscriptions",
        ],
        "documents": [
            "Identity document and codice fiscale of the applicant",
            "ISEE or any certificate proving the eligibility band when the agevolazione is income-based",
            "Student, disability, residence, or family-status documents if the reduced subscription depends on a specific category",
        ],
        "process": [
            "Review which subscription or reduced-fare scheme the client is applying for",
            "Check the identity, eligibility, and category-specific supporting documents",
            "Prepare the file for online application, office submission, or assisted follow-up",
        ],
        "notes": [
            "Required documents vary depending on the transport provider or public body managing the agevolazione",
            "Annual Metrobus card discounts and applications typically open in late February",
        ],
        "official_basis": [
            "Agevolated subscription schemes usually require identity, fiscal data, and proof of eligibility such as ISEE, student status, disability, or residence documentation",
        ],
    },
}

NEWS_ITEMS = [
    {
        "title": "Abbonamento Agevolazione",
        "date": "March 2026",
        "summary": "Reduced-fare transport subscriptions often require updated identity, residence, ISEE, or category-specific supporting documents before submission.",
        "cta": "Check the required documents before booking an agevolazione appointment.",
    },
    {
        "title": "730 Campaign Support",
        "date": "March 2026",
        "summary": "Prepare your 730 file early with income records, deductible expense receipts, and any family documents that affect detrazioni or credits.",
        "cta": "Book a tax appointment before the peak filing period starts.",
    },
    {
        "title": "ISEE and Family Benefits",
        "date": "March 2026",
        "summary": "Updated DSU and ISEE files are often needed for assegni, school-related requests, and other family or welfare measures.",
        "cta": "Use the required-documents page to check what to bring for your household case.",
    },
    {
        "title": "Permesso and Citizenship Files",
        "date": "March 2026",
        "summary": "Immigration cases move faster when passport copies, permit records, translations, and payment receipts are organized before submission.",
        "cta": "Choose the exact immigration service and upload supporting documents when booking.",
    },
]


def service_directory():
    return [
        {
            "label": "CAF Services",
            "endpoint": "caf_service_detail",
            "services": CAF_SERVICES,
        },
        {
            "label": "Patronato Services",
            "endpoint": "patronato_service_detail",
            "services": PATRONATO_SERVICES,
        },
        {
            "label": "Immigration Services",
            "endpoint": "immigration_service_detail",
            "services": IMMIGRATION_SERVICES,
        },
        {
            "label": "Consular Services",
            "endpoint": "embassy_service_detail",
            "services": EMBASSY_SERVICES,
        },
        {
            "label": "Admission Services",
            "endpoint": "admission_service_detail",
            "services": ADMISSION_SERVICES,
        },
        {
            "label": "Gestione Imprese",
            "endpoint": "business_service_detail",
            "services": BUSINESS_SERVICES,
        },
        {
            "label": "Others",
            "endpoint": "support_service_detail",
            "services": SUPPORT_SERVICES,
        },
    ]


def ensure_directories() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db() -> None:
    db = sqlite3.connect(DATABASE_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service_type TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            preferred_time TEXT NOT NULL,
            city TEXT NOT NULL,
            notes TEXT,
            uploaded_files TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            uploaded_files TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


@app.teardown_appcontext
def close_db(_exception) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def store_uploaded_files(files) -> list[dict]:
    stored_files = []
    for incoming_file in files:
        if not incoming_file or not incoming_file.filename:
            continue

        if not allowed_file(incoming_file.filename):
            continue

        original_name = secure_filename(incoming_file.filename)
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        incoming_file.save(UPLOAD_DIR / unique_name)
        stored_files.append({"stored_name": unique_name, "original_name": original_name})

    return stored_files


def admin_logged_in() -> bool:
    return bool(session.get("admin_logged_in"))


def require_admin():
    if not admin_logged_in():
        flash("Please sign in to view records.", "error")
        return redirect(url_for("admin_login"))
    return None


@app.context_processor
def inject_globals():
    lang = get_lang()
    return {
        "business_name": "sm solutions",
        "current_lang": lang,
        "available_languages": SUPPORTED_LANGS,
        "text_direction": "rtl" if lang == "fa" else "ltr",
        "t": t,
        "recaptcha_site_key": app.config["RECAPTCHA_SITE_KEY"],
    }


ensure_directories()
init_db()


@app.route("/")
def home():
    return render_template("home.html", news_items=NEWS_ITEMS)


@app.route("/set-language/<lang>")
def set_language(lang: str):
    if lang in SUPPORTED_LANGS:
        session["lang"] = lang
    return redirect(request.referrer or url_for("home"))


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/required-documents")
def required_documents():
    return render_template("required_documents.html", service_directory=service_directory())


@app.route("/news")
def news():
    return render_template("news.html", news_items=NEWS_ITEMS)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()

        if not full_name or not email or not phone or not message:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("contact"))

        uploaded_files = store_uploaded_files(request.files.getlist("documents"))
        db = get_db()
        db.execute(
            """
            INSERT INTO contact_messages (
                full_name, email, phone, message, uploaded_files
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                phone,
                message,
                json.dumps(uploaded_files),
            ),
        )
        db.commit()
        flash("Thank you! Your message has been saved.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/client-area")
def client_area():
    return render_template("client_area.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/gdpr")
def gdpr():
    return render_template("gdpr.html")


@app.route("/legal")
def legal():
    return render_template("legal.html")


@app.route("/caf-services")
def caf_services():
    return render_template("caf_services.html", caf_services=CAF_SERVICES)


@app.route("/caf-services/<slug>")
def caf_service_detail(slug: str):
    service = CAF_SERVICES.get(slug)
    if not service:
        return redirect(url_for("caf_services"))
    return render_template("caf_service_detail.html", service=service, slug=slug)


@app.route("/embassy-services")
def embassy_services():
    return redirect(url_for("immigration_services"))


@app.route("/embassy-services/<slug>")
def embassy_service_detail(slug: str):
    service = EMBASSY_SERVICES.get(slug)
    if not service:
        return redirect(url_for("embassy_services"))
    return render_template("embassy_service_detail.html", service=service, slug=slug)


@app.route("/patronato-services")
def patronato_services():
    return render_template("patronato_services.html", patronato_services=PATRONATO_SERVICES)


@app.route("/patronato-services/<slug>")
def patronato_service_detail(slug: str):
    service = PATRONATO_SERVICES.get(slug)
    if not service:
        return redirect(url_for("patronato_services"))
    return render_template("patronato_service_detail.html", service=service, slug=slug)


@app.route("/immigration-services")
def immigration_services():
    return render_template("immigration_services.html", immigration_services=IMMIGRATION_SERVICES)


@app.route("/immigration-services/<slug>")
def immigration_service_detail(slug: str):
    service = IMMIGRATION_SERVICES.get(slug)
    if not service:
        return redirect(url_for("immigration_services"))
    return render_template("immigration_service_detail.html", service=service, slug=slug)


@app.route("/admission-services")
def admission_services():
    return render_template("admission_services.html", admission_services=ADMISSION_SERVICES)


@app.route("/admission-services/<slug>")
def admission_service_detail(slug: str):
    service = ADMISSION_SERVICES.get(slug)
    if not service:
        return redirect(url_for("admission_services"))
    return render_template("admission_service_detail.html", service=service, slug=slug)


@app.route("/business-services")
def business_services():
    return render_template(
        "generic_services.html",
        title="Gestione Imprese | ciaocaf",
        eyebrow="Gestione Imprese",
        heading="Business setup and enterprise support from your uploaded list.",
        lead="These services cover business setup and administrative management items listed in your uploaded note.",
        category_label="Impresa",
        services=BUSINESS_SERVICES,
        detail_endpoint="business_service_detail",
    )


@app.route("/business-services/<slug>")
def business_service_detail(slug: str):
    service = BUSINESS_SERVICES.get(slug)
    if not service:
        return redirect(url_for("business_services"))
    return render_template(
        "generic_service_detail.html",
        page_title=f'{service["name"]} | Gestione Imprese | ciaocaf',
        eyebrow="Gestione Imprese",
        category_label="Impresa",
        booking_label="Book this gestione imprese service.",
        service=service,
    )


@app.route("/support-services")
def support_services():
    return render_template(
        "generic_services.html",
        title="Others | ciaocaf",
        eyebrow="Others",
        heading="Additional practical services grouped under Others.",
        lead="These services cover translation, legalization, housing, insurance, health-card, and account-registration support.",
        category_label="Others",
        services=SUPPORT_SERVICES,
        detail_endpoint="support_service_detail",
    )


@app.route("/support-services/<slug>")
def support_service_detail(slug: str):
    service = SUPPORT_SERVICES.get(slug)
    if not service:
        return redirect(url_for("support_services"))
    return render_template(
        "generic_service_detail.html",
        page_title=f'{service["name"]} | Others | ciaocaf',
        eyebrow="Others",
        category_label="Others",
        booking_label="Book this service from Others.",
        service=service,
    )


@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service_type = request.form.get("service_type", "").strip()
        preferred_date = request.form.get("preferred_date", "").strip()
        preferred_time = request.form.get("preferred_time", "").strip()
        city = request.form.get("city", "").strip()
        notes = request.form.get("notes", "").strip()

        if not all([full_name, email, phone, service_type, city]):
            flash("Please complete all required appointment fields.", "error")
            return redirect(url_for("appointments"))

        uploaded_files = store_uploaded_files(request.files.getlist("documents"))
        db = get_db()
        db.execute(
            """
            INSERT INTO appointments (
                full_name, email, phone, service_type, preferred_date,
                preferred_time, city, notes, uploaded_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                phone,
                service_type,
                preferred_date,
                preferred_time,
                city,
                notes,
                json.dumps(uploaded_files),
            ),
        )
        db.commit()
        flash("Appointment request saved successfully.", "success")
        return redirect(url_for("appointments"))

    return render_template("appointments.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        supplied_password = request.form.get("password", "")
        expected_password = os.environ.get("ADMIN_PASSWORD", "change-me-now")
        if supplied_password == expected_password:
            session["admin_logged_in"] = True
            flash("Signed in successfully.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Incorrect password.", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("home"))


@app.route("/admin/dashboard")
def admin_dashboard():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response

    rows = get_db().execute(
        """
        SELECT id, full_name, email, phone, service_type, preferred_date,
               preferred_time, city, notes, uploaded_files, created_at
        FROM appointments
        ORDER BY datetime(created_at) DESC, id DESC
        """
    ).fetchall()

    appointments_data = []
    for row in rows:
        item = dict(row)
        item["uploaded_files"] = json.loads(item["uploaded_files"] or "[]")
        appointments_data.append(item)

    return render_template("admin_dashboard.html", appointments=appointments_data)


@app.route("/admin/uploads/<path:filename>")
def admin_upload(filename: str):
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8001")),
        debug=False,
    )
