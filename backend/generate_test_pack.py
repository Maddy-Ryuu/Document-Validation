"""
generate_test_pack.py
Generates the synthetic test document pack for Phase 2 of AICTE Application Validation.
Creates realistic, high quality, multi-page PDFs strictly marked with synthetic notices.
"""

import os
import io
import hashlib
import random
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFilter

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = os.path.join(BASE_DIR, "test-data")
STANDARD_DIR = os.path.join(TEST_DATA_DIR, "standard-pack")
VARIANTS_DIR = os.path.join(TEST_DATA_DIR, "variants")

os.makedirs(STANDARD_DIR, exist_ok=True)
os.makedirs(VARIANTS_DIR, exist_ok=True)

# Standard colors & styling (RGB normalized 0.0 - 1.0)
COLOR_PRIMARY = (0.05, 0.22, 0.45)     # Deep Navy #0D3873
COLOR_TEXT_MAIN = (0.13, 0.13, 0.12)   # Dark Charcoal #20201E
COLOR_TEXT_MUTED = (0.42, 0.44, 0.47)  # Grey #6B7078
COLOR_BORDER = (0.85, 0.84, 0.81)      # Subtle Border #D9D6CF
COLOR_WARNING = (0.85, 0.20, 0.15)     # Muted Red for Synth Banner
COLOR_BG_CARD = (0.97, 0.96, 0.95)     # Light warm panel #F7F6F3
COLOR_WHITE = (1.0, 1.0, 1.0)
COLOR_ACCENT = (0.94, 0.47, 0.21)      # Saffron/Orange #F07836

SYNTHETIC_HEADER = "SYNTHETIC TEST DOCUMENT — NOT AN OFFICIAL RECORD"
SYNTHETIC_FOOTER = "Generated strictly for automated testing & validation benchmarking. Fictional institutional data only."


def draw_document_decorations(page, title, subtitle="", doc_ref=""):
    width = 595
    height = 842

    # Outer decorative border
    page.draw_rect(fitz.Rect(20, 20, width - 20, height - 20), color=COLOR_BORDER, width=0.8)
    page.draw_rect(fitz.Rect(24, 24, width - 24, height - 24), color=COLOR_BORDER, width=0.4)

    # Top Synthetic Warning Banner
    page.draw_rect(fitz.Rect(25, 25, width - 25, 48), color=COLOR_WARNING, fill=(0.98, 0.92, 0.92), width=0.5)
    page.insert_text(
        fitz.Point(35, 41),
        f"*** {SYNTHETIC_HEADER} ***",
        fontsize=9,
        fontname="helv",
        color=COLOR_WARNING
    )

    # Header block
    page.draw_rect(fitz.Rect(35, 58, width - 35, 115), color=None, fill=COLOR_BG_CARD)
    page.draw_line(fitz.Point(35, 115), fitz.Point(width - 35, 115), color=COLOR_PRIMARY, width=1.5)

    # Header title & subtitle
    page.insert_text(fitz.Point(45, 82), title, fontsize=14, fontname="hebo", color=COLOR_PRIMARY)
    if subtitle:
        page.insert_text(fitz.Point(45, 98), subtitle, fontsize=9.5, fontname="helv", color=COLOR_TEXT_MUTED)
    if doc_ref:
        page.insert_text(fitz.Point(width - 240, 80), f"REF: {doc_ref}", fontsize=8.5, fontname="hebo", color=COLOR_PRIMARY)

    # Watermark diagonally in center (MuPDF rotate must be an integer multiple of 90: 0, 90, 180, 270)
    wm_point = fitz.Point(75, 450)
    page.insert_text(wm_point, "SYNTHETIC TEST RECORD — NOT OFFICIAL", fontsize=20, fontname="hebo", color=(0.91, 0.90, 0.88), rotate=0)

    # Footer
    page.draw_line(fitz.Point(35, height - 50), fitz.Point(width - 35, height - 50), color=COLOR_BORDER, width=0.5)
    page.insert_text(fitz.Point(35, height - 38), SYNTHETIC_FOOTER, fontsize=7.5, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(width - 110, height - 38), "Page 1 of 1", fontsize=7.5, fontname="helv", color=COLOR_TEXT_MUTED)


def render_key_value_table(page, start_y, rows, col1_w=180, col2_w=330):
    curr_y = start_y
    left_x = 40
    row_h = 24
    for i, (k, v) in enumerate(rows):
        rect = fitz.Rect(left_x, curr_y, left_x + col1_w + col2_w, curr_y + row_h)
        bg = COLOR_BG_CARD if i % 2 == 1 else COLOR_WHITE
        page.draw_rect(rect, color=COLOR_BORDER, fill=bg, width=0.4)
        
        page.insert_text(fitz.Point(left_x + 8, curr_y + 16), str(k), fontsize=9, fontname="hebo", color=COLOR_PRIMARY)
        page.insert_text(fitz.Point(left_x + col1_w + 8, curr_y + 16), str(v), fontsize=9, fontname="helv", color=COLOR_TEXT_MAIN)
        curr_y += row_h
    return curr_y + 15


# -------------------------------------------------------------
# 1. Standard Document 1: Institution Profile
# -------------------------------------------------------------
def make_doc_01_institution_profile(output_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "APEX INSTITUTE OF TECHNOLOGY & ADVANCED STUDIES",
        "Statutory Institutional Profile & Governance Dossier (Academic Year 2026-2027)",
        "APEX-INST-2026-REG"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "1. GENERAL REGISTRATION & ESTABLISHMENT DETAILS", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_1 = [
        ("Name of the Institution:", "Apex Institute of Technology & Advanced Studies"),
        ("AICTE Permanent ID:", "1-3329014521"),
        ("Application Reference Number:", "AICTE-2026-88412"),
        ("Sponsoring Society / Trust:", "Apex Educational & Charitable Research Foundation"),
        ("Society Registration Number:", "BOM/TRUST/SOC-5491/2012"),
        ("Institution Category & Type:", "Engineering & Technology (Private - Self Financed)"),
        ("Established Year / Session:", "2014 | Commenced Academic Programs: 2014-2015"),
        ("Campus Address & Locus:", "Plot No. 42-B, Knowledge City, Phase II, Sector 9"),
        ("City, District & State:", "Pune, District Pune, Maharashtra - 411057"),
        ("Affiliating University:", "Savitribai Phule Pune University (SPPU)"),
    ]
    y = render_key_value_table(page, y + 10, fields_1)

    page.insert_text(fitz.Point(40, y), "2. LAND NORMS, CAMPUS INFRASTRUCTURE & SANCTIONS", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_2 = [
        ("Total Contiguous Land Area:", "5.25 Acres (Single Contiguous Parcel)"),
        ("Revenue Survey / Khasra No.:", "Survey No: 142/2A and 142/2B, Haveli Taluka"),
        ("Total Built-up Instructional Area:", "14,850 Sq. Meters (RCC Multi-storey Complex)"),
        ("Administrative Carpet Area:", "3,420 Sq. Meters"),
        ("Amenities & Sports Area:", "2,680 Sq. Meters"),
        ("Sanctioning Authority:", "Town & Country Planning Dept / PCMC Municipal Corp"),
        ("Sanction Order Ref & Date:", "Order No: PCMC/BP/2021-9984 | Dated: 14-06-2021"),
        ("Fire Safety NOC Number:", "NOC No: CFO/PMR/2025/FIRE-44819 | Valid until: 15-05-2027"),
    ]
    y = render_key_value_table(page, y + 10, fields_2)

    page.insert_text(fitz.Point(40, y), "3. AUTHORIZED STATUTORY SIGNATORIES", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_3 = [
        ("Head of Institution / Director:", "Dr. Arvind R. Kulkarni, Ph.D. (IIT Bombay)"),
        ("AICTE Faculty Identifier:", "AICTE-FAC-2018-9941"),
        ("Contact Official Email:", "director@apex-tech-synthetic.ac.in"),
        ("Contact Official Mobile:", "+91 98230 00000 (Fictional Verification Desk)"),
        ("Date of Dossier Verification:", "Dated: 12-01-2026"),
    ]
    y = render_key_value_table(page, y + 10, fields_3)

    # Signatory box
    page.draw_rect(fitz.Rect(380, y + 5, 555, y + 65), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(390, y + 22), "Verified and Certified by:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(390, y + 36), "Dr. Arvind R. Kulkarni", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(390, y + 48), "Director & Member Secretary", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
    page.insert_text(fitz.Point(390, y + 58), "[DIGITALLY ATTESTED TEST COPY]", fontsize=7, fontname="helv", color=COLOR_WARNING)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 2. Standard Document 2: Previous Extension of Approval (EoA) Record
# -------------------------------------------------------------
def make_doc_02_eoa_record(output_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION",
        "Western Regional Office, Industrial Assurance Building, Churchgate, Mumbai - 400020",
        "F.No. Western/1-3329014521/2025/EOA"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "LETTER OF EXTENSION OF APPROVAL (EoA) 2025-2026", fontsize=11, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_hdr = [
        ("Order Letter Number:", "Order No: AICTE/WRO/2025-26/1-3329014521/EOA"),
        ("Date of Issue:", "Dated: 28-04-2025"),
        ("Valid Academic Period:", "Valid until: 30-06-2026"),
        ("AICTE Permanent Institute ID:", "1-3329014521"),
        ("Name of the Institution:", "Apex Institute of Technology & Advanced Studies"),
        ("Applicant Body / Trust:", "Apex Educational & Charitable Research Foundation"),
        ("Campus Location / Address:", "Plot No. 42-B, Knowledge City, Phase II, Pune, Maharashtra - 411057"),
        ("Regional Office:", "Western Regional Office (WRO), Mumbai"),
    ]
    y = render_key_value_table(page, y + 10, fields_hdr)

    page.insert_text(fitz.Point(40, y), "APPROVED COURSES & INTAKE CAPACITY FOR 2025-2026", fontsize=10, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)
    y += 12

    # Course table header
    t_left = 40
    page.draw_rect(fitz.Rect(t_left, y, 555, y + 20), color=COLOR_BORDER, fill=COLOR_PRIMARY)
    page.insert_text(fitz.Point(t_left + 6, y + 14), "Programme / Level", fontsize=8.5, fontname="hebo", color=COLOR_WHITE)
    page.insert_text(fitz.Point(t_left + 140, y + 14), "Course / Specialization", fontsize=8.5, fontname="hebo", color=COLOR_WHITE)
    page.insert_text(fitz.Point(t_left + 350, y + 14), "Affiliating Body", fontsize=8.5, fontname="hebo", color=COLOR_WHITE)
    page.insert_text(fitz.Point(t_left + 450, y + 14), "Approved Intake", fontsize=8.5, fontname="hebo", color=COLOR_WHITE)
    y += 20

    courses = [
        ("UG - Engineering", "Computer Science & Engineering", "SPPU Pune", "180 Seats"),
        ("UG - Engineering", "Electronics & Telecommunication", "SPPU Pune", "120 Seats"),
        ("UG - Engineering", "Mechanical & Mechatronics Engg", "SPPU Pune", "60 Seats"),
        ("PG - Engineering", "M.Tech in Artificial Intelligence", "SPPU Pune", "24 Seats"),
        ("PG - Management", "MBA (General Management)", "SPPU Pune", "60 Seats"),
    ]
    for i, (lvl, c_name, affil, intake) in enumerate(courses):
        bg = COLOR_BG_CARD if i % 2 == 1 else COLOR_WHITE
        page.draw_rect(fitz.Rect(t_left, y, 555, y + 20), color=COLOR_BORDER, fill=bg, width=0.4)
        page.insert_text(fitz.Point(t_left + 6, y + 14), lvl, fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
        page.insert_text(fitz.Point(t_left + 140, y + 14), c_name, fontsize=8, fontname="hebo", color=COLOR_PRIMARY)
        page.insert_text(fitz.Point(t_left + 350, y + 14), affil, fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
        page.insert_text(fitz.Point(t_left + 450, y + 14), intake, fontsize=8.5, fontname="hebo", color=COLOR_TEXT_MAIN)
        y += 20

    y += 15
    page.insert_text(fitz.Point(40, y), "STATUTORY COMPLIANCE CLAUSES & CONDITIONS", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_BORDER, width=0.8)
    y += 14

    paragraphs = [
        "1. The institution shall adhere strictly to the faculty-cadre ratio (1:15 for UG and 1:12 for PG) as mandated by AICTE norms.",
        "2. The institution shall ensure complete compliance with Anti-Ragging regulations and operate the Internal Complaints Committee (ICC).",
        "3. Deficiencies, if observed during subsequent unannounced surprise inspection visits, will warrant immediate penal action.",
    ]
    for p in paragraphs:
        page.insert_text(fitz.Point(45, y), p, fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
        y += 14

    y += 10
    page.draw_rect(fitz.Rect(360, y, 555, y + 55), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(370, y + 18), "Issued by Order of the Council:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(370, y + 32), "Prof. Rajeev Sharma", fontsize=9, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(370, y + 44), "Member Secretary / Advisor (AICTE)", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 3. Standard Document 3: Affidavit or Undertaking
# -------------------------------------------------------------
def make_doc_03_affidavit(output_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "BEFORE THE COMPETENT NOTARY PUBLIC AT PUNE, MAHARASHTRA",
        "Statutory Form-A Non-Judicial Affidavit / Sworn Undertaking under AICTE Regulations",
        "AFF-2026-APEX-NOTARY-091"
    )

    y = 135
    # Stamp mock
    page.draw_rect(fitz.Rect(40, y, 555, y + 42), color=(0.75, 0.60, 0.20), fill=(0.99, 0.98, 0.90), width=0.8)
    page.insert_text(fitz.Point(50, y + 18), "GOVERNMENT OF MAHARASHTRA e-STAMP CERTIFICATE: IN-MH99214482012", fontsize=8.5, fontname="hebo", color=(0.55, 0.40, 0.10))
    page.insert_text(fitz.Point(50, y + 32), "Stamp Duty Paid: INR 500/- | Description: Affidavit u/s AICTE Act 1987 | First Party: Dr. Arvind R. Kulkarni", fontsize=7.5, fontname="helv", color=COLOR_TEXT_MAIN)
    y += 55

    page.insert_text(fitz.Point(40, y), "SWORN AFFIDAVIT OF COMPLIANCE & ACCURACY", fontsize=11, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)
    y += 16

    legal_text = (
        "I, Dr. Arvind R. Kulkarni, son of Late Sh. R. V. Kulkarni, aged about 56 years, resident of Flat 402, "
        "Sai Residency, Baner, Pune - 411045, in my official capacity as Director of Apex Institute of Technology & Advanced "
        "Studies (AICTE Permanent ID: 1-3329014521) running under Apex Educational & Charitable Research Foundation, "
        "do hereby solemnly affirm and state on oath as follows:"
    )
    rect_intro = fitz.Rect(40, y, 555, y + 45)
    page.insert_textbox(rect_intro, legal_text, fontsize=8.5, fontname="helv", color=COLOR_TEXT_MAIN)
    y += 50

    clauses = [
        ("1. Identity & Authority:", "That the deponent is the authorized signatory empowered by Trust Resolution dated 10-01-2026 to submit institutional records for Academic Year 2026-2027."),
        ("2. Genuine Credentials:", "That all particulars, financial records, land documents, building plans, and faculty qualifications uploaded under Application ID AICTE-2026-88412 are authentic, complete and true."),
        ("3. Infrastructure Norms:", "That the institute possesses 5.25 Acres contiguous land and 14,850 Sq. Meters of approved instructional built-up area without any financial or legal lien."),
        ("4. Cadre & Compensation:", "That faculty salaries are disbursed through bank accounts in compliance with 7th Central Pay Commission (CPC) scale and cadre ratios."),
        ("5. Penal Consequences:", "That if any uploaded information or uploaded document is found forged, counterfeit or materially misleading, the Council shall have unfettered authority to revoke approval."),
    ]
    y = render_key_value_table(page, y, clauses, col1_w=150, col2_w=360)

    # Verification block
    page.insert_text(fitz.Point(40, y), "VERIFICATION STATEMENT", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    y += 14
    v_text = "Verified at Pune on this 15th day of January, 2026 that contents of Paragraphs 1 through 5 are true to deponent's knowledge. No material fact has been suppressed."
    page.insert_textbox(fitz.Rect(40, y, 555, y + 30), v_text, fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    y += 35

    # Notary & Deponent columns
    page.draw_rect(fitz.Rect(40, y, 270, y + 60), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(48, y + 16), "DEPONENT SIGNATURE & SEAL:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(48, y + 32), "Dr. Arvind R. Kulkarni", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(48, y + 46), "Director, Apex Institute of Technology", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)

    page.draw_rect(fitz.Rect(290, y, 555, y + 60), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(298, y + 16), "ATTESTED BY NOTARY PUBLIC:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(298, y + 32), "Adv. S. K. Deshmukh (Govt of India Notary)", fontsize=9, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(298, y + 46), "Notary Reg No: NOT-MAH-9941/2018 | Dated: 15-01-2026", fontsize=7.5, fontname="helv", color=COLOR_TEXT_MAIN)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 4. Standard Document 4: No Objection Certificate (Fire Safety NOC)
# -------------------------------------------------------------
def make_doc_04_noc(output_path, is_expired=False):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "OFFICE OF THE CHIEF FIRE OFFICER",
        "PUNE METROPOLITAN REGION DEVELOPMENT AUTHORITY (PMRDA) — FIRE BRIGADE HQ",
        "PMRDA/FIRE/NOC-44819"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "FIRE SAFETY COMPLIANCE CERTIFICATE / NO OBJECTION CERTIFICATE (NOC)", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    issue_d = "16-05-2022" if is_expired else "16-05-2024"
    valid_d = "15-05-2023" if is_expired else "15-05-2027"

    fields_noc = [
        ("NOC Reference Number:", "NOC No: CFO/PMR/2025/FIRE-44819"),
        ("Issuing Authority:", "Chief Fire Officer, Fire & Emergency Services PMRDA"),
        ("Date of Issue:", f"Dated: {issue_d}"),
        ("Validity Period:", f"Valid until: {valid_d}"),
        ("Premises / Building Inspected:", "Apex Institute of Technology & Advanced Studies"),
        ("Site / Parcel Location:", "Plot No. 42-B, Knowledge City, Phase II, Pune - 411057"),
        ("Survey / Khasra Identification:", "Survey No: 142/2A and 142/2B, Haveli Taluka"),
        ("Building Height & Construction:", "Ground + 4 Storeys (Height: 14.85 Meters, Type-A Institutional)"),
        ("Total Inspected Carpet Area:", "14,850 Sq. Meters (Instructional & Lab Blocks)"),
    ]
    y = render_key_value_table(page, y + 10, fields_noc)

    page.insert_text(fitz.Point(40, y), "INSPECTION FINDINGS & FIRE PROTECTION SYSTEMS VERIFIED", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_BORDER, width=0.8)
    y += 14

    protections = [
        ("Wet Riser & Downcomer System:", "Installed with 150mm internal risers, landing valves and hose reels on each floor."),
        ("Underground & Overhead Water Reserves:", "Static Fire Water Tank of 150,000 Liters and Terrace Tank of 25,000 Liters operational."),
        ("Automatic Sprinkler & Smoke Detection:", "Photoelectric smoke detectors installed in all server rooms, seminar halls, and laboratories."),
        ("Emergency Exits & Staircase Clearances:", "Two independent 2.0-meter fire-rated staircases provided with outward opening doors."),
    ]
    y = render_key_value_table(page, y, protections, col1_w=200, col2_w=310)

    y += 10
    page.draw_rect(fitz.Rect(340, y, 555, y + 60), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(350, y + 16), "Issued under Seal of Authority:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(350, y + 30), "V. S. Thorat, CFO", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(350, y + 44), "Chief Fire Officer, Fire & Emergency Services", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
    page.insert_text(fitz.Point(350, y + 54), "Pune Metropolitan Region Development Authority", fontsize=7.5, fontname="helv", color=COLOR_TEXT_MUTED)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 5. Standard Document 5: Accreditation Certificate (NAAC)
# -------------------------------------------------------------
def make_doc_05_accreditation(output_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "NATIONAL ASSESSMENT AND ACCREDITATION COUNCIL (NAAC)",
        "An Autonomous Institution of the University Grants Commission, P.O. Box 1075, Bengaluru - 560072",
        "NAAC/A&A/2023/MH-AIT-9921"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "CERTIFICATE OF ACCREDITATION (INSTITUTIONAL GRADE)", fontsize=11, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_naac = [
        ("Accreditation Certificate Number:", "Order No: NAAC/CERT/MH-AIT/2023/77102"),
        ("Name of Accredited Institution:", "Apex Institute of Technology & Advanced Studies"),
        ("Institutional Permanent AICTE ID:", "1-3329014521"),
        ("Campus Location:", "Knowledge City, Phase II, Pune, Maharashtra - 411057"),
        ("Cumulative Grade Point Average (CGPA):", "3.42 out of 4.00 Grade Scale"),
        ("Accreditation Grade Awarded:", "Grade 'A+' (Very Good Performance)"),
        ("Date of Accreditation Assessment:", "Dated: 18-09-2023"),
        ("Certificate Validity Period:", "Valid until: 17-09-2028 (Cycle 2 Accreditation)"),
        ("Issuing Authority & Body:", "Executive Committee, National Assessment and Accreditation Council"),
    ]
    y = render_key_value_table(page, y + 10, fields_naac)

    page.insert_text(fitz.Point(40, y), "CRITERIA-WISE INSTITUTIONAL PERFORMANCE SUMMARY", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_BORDER, width=0.8)
    y += 14

    criteria = [
        ("Criterion I - Curricular Aspects:", "Grade Point Score: 3.55 / 4.00"),
        ("Criterion II - Teaching-Learning & Evaluation:", "Grade Point Score: 3.48 / 4.00"),
        ("Criterion III - Research, Innovations & Extension:", "Grade Point Score: 3.25 / 4.00"),
        ("Criterion IV - Infrastructure & Learning Resources:", "Grade Point Score: 3.60 / 4.00"),
        ("Criterion V - Student Support & Progression:", "Grade Point Score: 3.35 / 4.00"),
    ]
    y = render_key_value_table(page, y, criteria, col1_w=240, col2_w=270)

    y += 10
    page.draw_rect(fitz.Rect(340, y, 555, y + 60), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(350, y + 16), "By Authority of Executive Committee:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(350, y + 30), "Prof. S. C. Sharma", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(350, y + 44), "Director & Member Secretary, NAAC", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
    page.insert_text(fitz.Point(350, y + 54), "Bengaluru, Karnataka - India", fontsize=7.5, fontname="helv", color=COLOR_TEXT_MUTED)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 6. Standard Document 6: Faculty Qualification Records
# -------------------------------------------------------------
def make_doc_06_faculty_records(output_path, missing_director=False):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "APEX INSTITUTE OF TECHNOLOGY & ADVANCED STUDIES",
        "Statutory Core Faculty Qualification Roster & Cadre Distribution (AY 2026-2027)",
        "FAC-ROSTER-2026-AY"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "CORE FACULTY CADRE & QUALIFICATION REGISTER", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    # If missing_director is True, we intentionally omit principal_director_name
    inst_name_val = "Apex Institute of Technology & Advanced Studies"
    fields_roster = [
        ("Institution Name:", inst_name_val),
        ("AICTE Permanent Institute ID:", "1-3329014521"),
        ("Application Reference:", "AICTE-2026-88412"),
    ]
    if not missing_director:
        fields_roster.append(("Principal / Director Name:", "Dr. Arvind R. Kulkarni"))
    else:
        # Deliberately missing field!
        pass

    fields_roster.extend([
        ("Total Sanctioned Core Faculty:", "68 Full-Time Regular Faculty Members"),
        ("Faculty with Doctorate (Ph.D.):", "28 Faculty Members (41.2% Research Density)"),
        ("Declared Cadre Ratio (Prof : Asso : Asst):", "1 : 2 : 6 (Meets AICTE Handbook Mandate)"),
        ("Roster Verification Date:", "Dated: 14-01-2026"),
    ])
    y = render_key_value_table(page, y + 10, fields_roster)

    page.insert_text(fitz.Point(40, y), "REPRESENTATIVE HEADS OF DEPARTMENT & SENIOR FACULTY", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_BORDER, width=0.8)
    y += 12

    # Table of faculty
    t_left = 40
    page.draw_rect(fitz.Rect(t_left, y, 555, y + 18), color=COLOR_BORDER, fill=COLOR_PRIMARY)
    page.insert_text(fitz.Point(t_left + 6, y + 13), "Faculty Name & ID", fontsize=8, fontname="hebo", color=COLOR_WHITE)
    page.insert_text(fitz.Point(t_left + 150, y + 13), "Cadre / Designation", fontsize=8, fontname="hebo", color=COLOR_WHITE)
    page.insert_text(fitz.Point(t_left + 280, y + 13), "Highest Qualification", fontsize=8, fontname="hebo", color=COLOR_WHITE)
    page.insert_text(fitz.Point(t_left + 420, y + 13), "Department", fontsize=8, fontname="hebo", color=COLOR_WHITE)
    y += 18

    faculty_list = [
        ("Dr. Arvind R. Kulkarni (FAC-9941)", "Director / Professor", "Ph.D. (Computer Engg, IIT Bombay)", "Computer Science"),
        ("Dr. Sunita M. Joshi (FAC-8812)", "Professor & HOD", "Ph.D. (VLSI Design, IISc Bangalore)", "Electronics & Telecomm"),
        ("Dr. Ramesh V. Patil (FAC-7734)", "Professor & HOD", "Ph.D. (Thermal Engg, VNIT)", "Mechanical Engg"),
        ("Dr. Meera N. Iyer (FAC-6621)", "Associate Professor", "Ph.D. (Machine Learning, Pune Univ)", "Computer Science"),
        ("Prof. Anand K. Shinde (FAC-5509)", "Assistant Professor", "M.Tech (Digital Systems, COEP)", "Electronics & Telecomm"),
        ("Dr. Priya S. Nair (FAC-4498)", "Associate Professor", "Ph.D. (Management Studies, IIM-I)", "Management (MBA)"),
    ]
    for i, (fname, desig, qual, dept) in enumerate(faculty_list):
        bg = COLOR_BG_CARD if i % 2 == 1 else COLOR_WHITE
        page.draw_rect(fitz.Rect(t_left, y, 555, y + 18), color=COLOR_BORDER, fill=bg, width=0.4)
        page.insert_text(fitz.Point(t_left + 6, y + 13), fname, fontsize=7.5, fontname="hebo", color=COLOR_PRIMARY)
        page.insert_text(fitz.Point(t_left + 150, y + 13), desig, fontsize=7.5, fontname="helv", color=COLOR_TEXT_MAIN)
        page.insert_text(fitz.Point(t_left + 280, y + 13), qual, fontsize=7.5, fontname="helv", color=COLOR_TEXT_MAIN)
        page.insert_text(fitz.Point(t_left + 420, y + 13), dept, fontsize=7.5, fontname="helv", color=COLOR_TEXT_MAIN)
        y += 18

    y += 15
    page.draw_rect(fitz.Rect(340, y, 555, y + 55), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(350, y + 16), "Attested by Registrar / Director:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(350, y + 30), "Registrar & Academic Dean", fontsize=9, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(350, y + 44), "Apex Institute of Technology & Advanced Studies", fontsize=7.5, fontname="helv", color=COLOR_TEXT_MAIN)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 7. Standard Document 7: Payment Receipt
# -------------------------------------------------------------
def make_doc_07_payment_receipt(output_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "AICTE E-GOVERNANCE ONLINE PAYMENT GATEWAY",
        "Centralized Regulatory Processing Fee Transaction Voucher (AY 2026-2027)",
        "TXN-AICTE-2026-993812"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "ELECTRONIC CHALLAN & TRANSACTION CONFIRMATION RECEIPT", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_pay = [
        ("Transaction Reference Number:", "TXN-AICTE-2026-993812"),
        ("Order / Challan Number:", "Order No: CHL-2026-MH-449102"),
        ("Transaction Date & Time:", "Dated: 10-01-2026 14:22:38 IST"),
        ("Payment Mode & Gateway:", "Bharatkosh / SBI Multi-Option Payment System (NEFT/RTGS)"),
        ("Bank Reference Number (UTR):", "SBIN20260110998341"),
        ("Applicant Institution Name:", "Apex Institute of Technology & Advanced Studies"),
        ("AICTE Permanent Institute ID:", "1-3329014521"),
        ("Application Reference Number:", "AICTE-2026-88412"),
        ("Regulatory Purpose / Head:", "Extension of Approval (EoA) & Course Continuation Processing Fee"),
        ("Total Fee Amount Paid:", "INR 3,50,000/- (Rupees Three Lakh Fifty Thousand Only)"),
        ("Transaction Status:", "SUCCESS / SETTLED (Cleared to AICTE Central Regulatory Account)"),
    ]
    y = render_key_value_table(page, y + 10, fields_pay)

    page.insert_text(fitz.Point(40, y), "ACCOUNTING HEAD BREAKDOWN", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_BORDER, width=0.8)
    y += 14

    items = [
        ("Institutional Scrutiny Fee (Technical UG):", "INR 2,00,000.00"),
        ("Post-Graduate Technical Programme Assessment:", "INR 1,00,000.00"),
        ("Management Studies Verification Fee:", "INR 50,000.00"),
        ("Applicable Goods & Services Tax (Exempted u/s 12AA):", "INR 0.00"),
        ("Net Total Remitted:", "INR 3,50,000.00"),
    ]
    y = render_key_value_table(page, y, items, col1_w=300, col2_w=210)

    y += 10
    page.draw_rect(fitz.Rect(320, y, 555, y + 60), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(330, y + 16), "System-Generated Confirmation:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(330, y + 30), "Finance & Accounts Officer", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(330, y + 44), "Central Portal Gateway, AICTE New Delhi", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
    page.insert_text(fitz.Point(330, y + 54), "[AUTHENTICATED PAYMENT GATEWAY RECORD]", fontsize=7, fontname="helv", color=COLOR_PRIMARY)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 8. Variant: Mismatched Institution Identifier
# -------------------------------------------------------------
def make_doc_variant_mismatch(output_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION",
        "Western Regional Office, Industrial Assurance Building, Churchgate, Mumbai - 400020",
        "F.No. Western/1-9999999999/2025/EOA"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "LETTER OF EXTENSION OF APPROVAL (EoA) 2025-2026 [MISMATCH TEST]", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    # In this variant, institution identifier and name belong to another fictional entity
    fields_mismatch = [
        ("Order Letter Number:", "Order No: AICTE/WRO/2025-26/1-9999999999/EOA"),
        ("Date of Issue:", "Dated: 28-04-2025"),
        ("Valid Academic Period:", "Valid until: 30-06-2026"),
        ("AICTE Permanent Institute ID:", "1-9999999999"),  # MISMATCH! Target application is 1-3329014521
        ("Name of the Institution:", "Zenith Polytechnic & Technology Campus"),  # MISMATCH! Target is Apex Institute
        ("Applicant Body / Trust:", "Zenith Rural Education Trust"),
        ("Campus Location / Address:", "Plot 99, Sector 4, Nashik, Maharashtra - 422001"),
        ("Regional Office:", "Western Regional Office (WRO), Mumbai"),
    ]
    y = render_key_value_table(page, y + 10, fields_mismatch)

    page.insert_text(fitz.Point(40, y), "APPROVED COURSES & INTAKE CAPACITY", fontsize=10, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_BORDER, width=0.8)
    y += 12

    courses = [
        ("Diploma Civil Engineering (Approved Intake):", "60 Seats (MSBTE Affiliated)"),
        ("Diploma Electrical Engineering (Approved Intake):", "60 Seats (MSBTE Affiliated)"),
    ]
    y = render_key_value_table(page, y, courses, col1_w=240, col2_w=270)

    y += 15
    page.draw_rect(fitz.Rect(340, y, 555, y + 55), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(350, y + 16), "Issued by Regional Officer:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(350, y + 30), "Regional Officer, WRO Mumbai", fontsize=9, fontname="hebo", color=COLOR_PRIMARY)

    doc.save(output_path)
    doc.close()


# -------------------------------------------------------------
# 9. Variant: Scanned Raster PDF for OCR Engine Testing
# -------------------------------------------------------------
def make_doc_variant_scanned_ocr(output_path):
    # First create a vector PDF in memory
    mem_doc = fitz.open()
    page = mem_doc.new_page(width=595, height=842)
    draw_document_decorations(
        page,
        "STATE DISASTER MANAGEMENT & FIRE RESCUE SERVICES",
        "Office of the Divisional Fire Officer, Pune Metropolitan Region Division",
        "SCANNED-NOC-FIRE-2025-081"
    )

    y = 135
    page.insert_text(fitz.Point(40, y), "FIRE SAFETY CERTIFICATE & STATUTORY COMPLIANCE CLEARANCE", fontsize=10.5, fontname="hebo", color=COLOR_PRIMARY)
    page.draw_line(fitz.Point(40, y + 3), fitz.Point(555, y + 3), color=COLOR_ACCENT, width=1)

    fields_scan = [
        ("NOC Reference Number:", "NOC No: CFO/PMR/2025/FIRE-44819"),
        ("Issuing Authority:", "Chief Fire Officer, Fire & Emergency Services PMRDA"),
        ("Date of Issue:", "Dated: 16-05-2024"),
        ("Validity Period:", "Valid until: 15-05-2027"),
        ("Applicant Institution:", "Apex Institute of Technology & Advanced Studies"),
        ("AICTE Permanent ID:", "1-3329014521"),
        ("Premises Address:", "Plot No. 42-B, Knowledge City, Phase II, Pune - 411057"),
        ("Survey / Khasra No.:", "Survey No: 142/2A and 142/2B, Haveli Taluka"),
        ("Total Built-up Area Certified:", "14,850 Sq. Meters (RCC Frame Structure)"),
        ("Inspecting Officer Inspection Remark:", "Fire hydrants, alarms and evacuation staircases functional as per NBC Part IV norms."),
    ]
    y = render_key_value_table(page, y + 10, fields_scan)

    y += 20
    page.draw_rect(fitz.Rect(340, y, 555, y + 65), color=COLOR_BORDER, fill=COLOR_BG_CARD)
    page.insert_text(fitz.Point(350, y + 16), "Signed and Sealed by:", fontsize=8, fontname="helv", color=COLOR_TEXT_MUTED)
    page.insert_text(fitz.Point(350, y + 30), "V. S. Thorat, CFO", fontsize=9.5, fontname="hebo", color=COLOR_PRIMARY)
    page.insert_text(fitz.Point(350, y + 44), "Chief Fire Officer, PMRDA Fire Division", fontsize=8, fontname="helv", color=COLOR_TEXT_MAIN)
    page.insert_text(fitz.Point(350, y + 54), "[GOVERNMENT SEAL AFFIXED]", fontsize=7, fontname="helv", color=COLOR_TEXT_MUTED)

    # Render vector page to high-res pixmap (150 DPI)
    pix = page.get_pixmap(dpi=150)
    img_data = pix.tobytes("png")
    mem_doc.close()

    # Open with PIL to simulate physical scan degradation (subtle rotation, noise, slight blur)
    pil_img = Image.open(io.BytesIO(img_data))
    # Slight deskew angle (0.6 degrees clockwise)
    pil_img = pil_img.rotate(0.6, fillcolor="white", resample=Image.BICUBIC)
    
    # Save as compressed JPEG stream to strip digital text vectors completely
    jpeg_io = io.BytesIO()
    pil_img.save(jpeg_io, format="JPEG", quality=82)
    jpeg_bytes = jpeg_io.getvalue()

    # Create new PDF with ONLY the raster JPEG image
    raster_doc = fitz.open()
    raster_page = raster_doc.new_page(width=595, height=842)
    raster_page.insert_image(fitz.Rect(0, 0, 595, 842), stream=jpeg_bytes)
    raster_doc.save(output_path)
    raster_doc.close()


def generate_all():
    print("Generating Synthetic Document Test Pack for Phase 2...")
    
    # 1. Standard Pack
    p_01 = os.path.join(STANDARD_DIR, "01_institution_profile.pdf")
    p_02 = os.path.join(STANDARD_DIR, "02_previous_eoa_record.pdf")
    p_03 = os.path.join(STANDARD_DIR, "03_affidavit_undertaking.pdf")
    p_04 = os.path.join(STANDARD_DIR, "04_noc_fire_safety.pdf")
    p_05 = os.path.join(STANDARD_DIR, "05_accreditation_certificate.pdf")
    p_06 = os.path.join(STANDARD_DIR, "06_faculty_qualification_records.pdf")
    p_07 = os.path.join(STANDARD_DIR, "07_payment_receipt.pdf")

    make_doc_01_institution_profile(p_01)
    make_doc_02_eoa_record(p_02)
    make_doc_03_affidavit(p_03)
    make_doc_04_noc(p_04, is_expired=False)
    make_doc_05_accreditation(p_05)
    make_doc_06_faculty_records(p_06, missing_director=False)
    make_doc_07_payment_receipt(p_07)

    # 2. Variants
    v_expired = os.path.join(VARIANTS_DIR, "variant_expired_certificate.pdf")
    v_missing = os.path.join(VARIANTS_DIR, "variant_missing_required_field.pdf")
    v_mismatch = os.path.join(VARIANTS_DIR, "variant_cross_doc_mismatch.pdf")
    v_duplicate = os.path.join(VARIANTS_DIR, "variant_exact_duplicate.pdf")
    v_scanned = os.path.join(VARIANTS_DIR, "variant_scanned_ocr_test.pdf")

    # Expired variant: NOC with valid_until = 15-05-2023
    make_doc_04_noc(v_expired, is_expired=True)
    # Missing required field variant: Faculty records missing principal_director_name
    make_doc_06_faculty_records(v_missing, missing_director=True)
    # Mismatch variant: EoA record with institute id 1-9999999999
    make_doc_variant_mismatch(v_mismatch)
    # Exact duplicate variant: exact binary copy of 07_payment_receipt.pdf
    with open(p_07, "rb") as f_src, open(v_duplicate, "wb") as f_dst:
        f_dst.write(f_src.read())
    # Scanned OCR variant
    make_doc_variant_scanned_ocr(v_scanned)

    print("All 12 synthetic PDF test files generated successfully.")


if __name__ == "__main__":
    generate_all()
