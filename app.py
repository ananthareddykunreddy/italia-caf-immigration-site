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
    "footer_all_services": {"it": "Tutti i Servizi", "en": "All Services", "fa": "همه خدمات"},
    "footer_rights": {"it": "Tutti i diritti riservati.", "en": "All rights reserved.", "fa": "تمامی حقوق محفوظ است."},
    "footer_summary": {
        "it": "Servizi CAF, patronato, immigrazione, consulenza universitaria, gestione imprese e servizi pratici in Italia.",
        "en": "CAF services, patronato, immigration, university consulting, business management, and practical services in Italy.",
        "fa": "خدمات CAF، پاتروناتو، مهاجرت، مشاوره دانشگاهی، مدیریت کسب‌وکار و خدمات کاربردی در ایتالیا.",
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
        "it": "Contatti CAF Bixio Roma.",
        "en": "CAF Bixio Rome contact details.",
        "fa": "اطلاعات تماس CAF Bixio رم.",
    },
    "contact_lead": {
        "it": "Trova recapiti, orari ufficio e mappa della sede di Via Bixio per contatti e appuntamenti.",
        "en": "Find office contacts, opening hours, and the Via Bixio map for direct contact and appointments.",
        "fa": "اطلاعات تماس، ساعات کاری و نقشه دفتر خیابان Bixio را برای تماس مستقیم و رزرو ببینید.",
    },
    "direct_contact": {"it": "Contatto Diretto", "en": "Direct Contact", "fa": "تماس مستقیم"},
    "office_details": {"it": "Dettagli ufficio CAF Bixio", "en": "CAF Bixio office details", "fa": "اطلاعات دفتر CAF Bixio"},
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
        ],
        "official_basis": [
            "INPS explains DSU and ISEE updates and availability of precompiled functionality",
        ],
    },
    "730": {
        "name": "730",
        "summary": "Assistance for 730 declaration paperwork and related supporting documents.",
        "who_needs_it": [
            "Workers and pensioners using the 730 declaration route",
            "Taxpayers who want help reviewing precompiled tax data",
            "Clients who need support checking deductible or credit-related documents",
        ],
        "documents": [
            "Documento di identita and codice fiscale of the taxpayer and spouse or dependants if included",
            "CU, pension certifications, and any income records used for the dichiarazione precompilata or ordinary 730",
            "Receipts for detrazioni and deduzioni such as medical expenses, rent, mortgage interest, school, insurance, and family charges",
        ],
        "process": [
            "Review whether the 730 is the right declaration route",
            "Check precompiled or client-provided data",
            "Organize deductions, credits, and supporting documents",
            "Prepare the file for assisted declaration submission",
        ],
        "notes": [
            "The Agenzia delle Entrate provides precompiled returns that still need checking",
            "Final required documents vary by the taxpayer’s case",
        ],
        "official_basis": [
            "Agenzia delle Entrate explains the precompiled declaration and 730 workflow",
        ],
    },
    "imu": {
        "name": "IMU",
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
        ],
        "official_basis": [
            "Residence changes are commonly tied to municipal registry processes and supporting documentation",
        ],
    },
    "f24": {
        "name": "F24",
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
        ],
        "official_basis": [
            "PEC is commonly used in Italy for certified communications in administrative and business contexts",
        ],
    },
    "assegno-unico": {
        "name": "Assegno Unico",
        "summary": "Support organizing family and household documents for Assegno Unico-related assistance.",
        "who_needs_it": [
            "Families checking household documentation for child-related support requests",
            "Clients who need help preparing files connected to family-benefit procedures",
        ],
        "documents": [
            "SPID/CIE/CNS for online filing or identity and codice fiscale details of the applicant",
            "Codice fiscale of each child, family-status data, and any custody or separation documentation where relevant",
            "IBAN for payment and ISEE when the family wants the amount calculated with the economic indicator",
        ],
        "process": [
            "Review the household situation and relevant support route",
            "Organize the supporting family and income documentation",
            "Prepare the file for assisted follow-up or submission readiness",
        ],
        "notes": [
            "Exact required documents can depend on the household case and current rules",
        ],
        "official_basis": [
            "Public SmartCAF descriptions list Assegno Unico among its supported services",
        ],
    },
    "modello-redditi": {
        "name": "Modello Redditi",
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
        ],
        "official_basis": [
            "Permit conversions are a standard immigration support area with case-specific documentation",
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
}

PATRONATO_SERVICES = {
    "disoccupazione": {
        "name": "Disoccupazione",
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
        ],
        "official_basis": [
            "Patronato-style support commonly covers unemployment and related welfare paperwork",
        ],
    },
    "assegno-unico-patronato": {
        "name": "Assegno Unico",
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
        "name": "Certificazione Unica",
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
        ],
        "process": [
            "Review the platform and account requirements",
            "Organize the supporting registration information",
            "Prepare the user for the next registration step",
        ],
        "notes": [
            "Platform requirements vary by service and account type",
        ],
        "official_basis": [
            "The uploaded list includes account registration support for Glovo, Deliveroo, and Just Eat",
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
        "business_name": "ciaocaf",
        "current_lang": lang,
        "available_languages": SUPPORTED_LANGS,
        "text_direction": "rtl" if lang == "fa" else "ltr",
        "t": t,
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


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/client-area")
def client_area():
    return render_template("client_area.html")


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

        if not all([full_name, email, phone, service_type, preferred_date, preferred_time, city]):
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
