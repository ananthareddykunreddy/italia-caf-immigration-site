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
            "Identity documents and tax codes for household members",
            "Income and financial documentation used for DSU preparation",
            "Property, account, or household information relevant to the declaration",
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
            "Identity and tax information",
            "Income and withholding documents",
            "Receipts or records for deductions, detractions, and household data",
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
            "Identity and tax code details",
            "Property information and relevant municipal/tax data",
            "Previous payment or assessment records when applicable",
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
            "Identity and fiscal information",
            "Income or responsibility declaration documents relevant to the campaign",
            "Supporting records related to the specific declaration type",
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
            "Identity documents",
            "Address and residence-related supporting documents",
            "Any municipal or family-status records required by the case",
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
            "Identity and tax details",
            "Payment references, codes, and related tax/contribution data",
            "Any prior F24 or payment-support records relevant to the case",
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
            "Identity and household information",
            "ISEE or other eligibility-related documents when required",
            "Supporting records linked to the specific bonus",
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
            "Contact details and any information required by the chosen identity provider",
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
            "Contact information required for activation",
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
            "Identity and tax information for the household",
            "Family-status and child-related records",
            "ISEE or other supporting documents where relevant to the case",
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
            "Identity and tax details",
            "Income and fiscal-supporting documents",
            "Documents for deductions, credits, and tax positions relevant to the case",
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
            "Identity documents",
            "Family and inheritance-related records",
            "Property or registry-supporting documents where applicable",
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
            "Identity and permit-related records",
            "Supporting documents required for the specific permit case",
            "Photocopies and file organization for submission",
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
            "Permit-related identity and supporting records",
            "Case-specific documents linked to study, work, family, or renewal",
            "Copies, translations, or supporting forms when needed",
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
            "Original documents",
            "Translated versions when available",
            "Supporting copies or certification-related records depending on the use case",
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
            "Identity and case-specific records",
            "Cross-border or foreign-issued supporting documents",
            "Copies, translations, or consular paperwork depending on the case",
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
            "Identity and family relationship records",
            "Residence and accommodation-related documents",
            "Supporting immigration paperwork for the family case",
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
            "Identity records",
            "Work or sponsor-related supporting documents",
            "Any documents linked to the flussi procedure involved",
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
            "Identity and civil-status records",
            "Residence and supporting administrative documents",
            "Any translations, copies, or linked records required by the case",
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
            "Current permit-related documents",
            "Identity and supporting records linked to the new permit basis",
            "Any work, study, or family-related documents required for the conversion",
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
            "Identity and current passport-related records",
            "Photographs and case-specific supporting documents",
            "Scans or upload-ready copies where required",
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
            "Identity and nationality-related documents",
            "Photo, signature, and supporting records required for the OCI case",
            "Scans and copies prepared to the required format",
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
            "Current and former nationality/passport records as required",
            "Supporting identity and case documents",
            "Copies, forms, and scanned documents needed for the process",
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
            "Identity and fiscal documents",
            "Employment and termination-related records",
            "Supporting documents required for the specific unemployment case",
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
            "Identity and family-status records",
            "Household and benefit-related supporting documents",
            "Any income or supporting files relevant to the case",
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
            "Identity and fiscal details",
            "Employment information",
            "Any supporting records linked to the resignation process",
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
            "Identity and family records",
            "Employment or welfare-supporting documents where relevant",
            "Any maternity-related case documents required for follow-up",
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
            "Identity and health-related records relevant to the case",
            "Supporting administrative documents",
            "Any records required for the recognition or follow-up workflow",
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
            "Identity records",
            "Family or support-related documentation",
            "Any case-specific administrative records connected to the request",
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
            "Identity and fiscal records",
            "Contribution or employment-related documents where applicable",
            "Supporting pension-related case records",
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
            "Identity and fiscal details",
            "Employment or collaboration records",
            "Termination and supporting case documents",
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
            "Identity and household documents",
            "Income or family-supporting records where relevant",
            "Any ADI-related supporting documentation required by the case",
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
            "Academic records and personal identity documents",
            "Program-specific forms or supporting files",
            "Language, profile, or statement documents when required",
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
            "Academic certificates and transcripts",
            "Identity and travel records",
            "Translations or supporting copies where required",
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
            "Identity and fiscal records",
            "Address and activity-related information",
            "Supporting business-start information where needed",
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
            "Identity and fiscal details",
            "Business or invoicing-related records",
            "Any provider or system information used for invoicing setup",
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
            "Identity and tax information",
            "CU-related fiscal documents",
            "Supporting income or withholding records where needed",
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
            "Identity and business-related records",
            "Company or activity-supporting documents",
            "Any registration or chamber-related paperwork involved in the case",
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
            "Identity and business-related information",
            "Activity and premises-supporting documents where relevant",
            "Any administrative forms or records linked to the SCIA case",
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
            "Original documents",
            "Translated versions where available",
            "Supporting copies and identity records linked to the process",
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
            "Identity and contact details",
            "Any appointment or registration-related records",
            "Supporting immigration or residence documents where relevant",
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
            "Identity documents",
            "Income or guarantee-related records where relevant",
            "Housing or contract-supporting documents",
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
            "Identity records",
            "Vehicle-related documents",
            "Any prior insurance or ownership-supporting records",
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
            "Identity records",
            "Residence or immigration-related records where relevant",
            "Any supporting administrative documents tied to the case",
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
        "name": "Account Registration (Glovo / Deliveroo)",
        "summary": "Support for app-account registration readiness and related document organization.",
        "who_needs_it": [
            "Clients who need help preparing the documents used for platform account registration",
            "Applicants organizing identity, contact, or work-related information for account setup",
        ],
        "documents": [
            "Identity and contact details",
            "Any platform-required supporting documents",
            "Work-related records where needed by the registration process",
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
            "The uploaded list includes account registration support for Glovo and Deliveroo",
        ],
    },
}


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
    return {"business_name": "ciaocaf"}


ensure_directories()
init_db()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/services")
def services():
    return render_template("services.html")


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
    return render_template("embassy_services.html", embassy_services=EMBASSY_SERVICES)


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
        title="Business Services | ciaocaf",
        eyebrow="Business Services",
        heading="Business and enterprise support from your uploaded list.",
        lead="These services cover business setup and administrative management items listed in your uploaded note.",
        category_label="Business",
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
        page_title=f'{service["name"]} | Business Services | ciaocaf',
        eyebrow="Business Service",
        category_label="Business",
        booking_label="Book this business service.",
        service=service,
    )


@app.route("/support-services")
def support_services():
    return render_template(
        "generic_services.html",
        title="Support Services | ciaocaf",
        eyebrow="Support Services",
        heading="Additional practical support services from your uploaded list.",
        lead="These services cover translation, legalization, housing, insurance, health-card, and account-registration support.",
        category_label="Support",
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
        page_title=f'{service["name"]} | Support Services | ciaocaf',
        eyebrow="Support Service",
        category_label="Support",
        booking_label="Book this support service.",
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
