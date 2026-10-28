import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import pymupdf  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)

# Resource safety limits
MAX_DOCUMENT_PAGE_COUNT = 50
MAX_DOCUMENT_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

_ocr_reader = None
_ocr_initialized = False


def get_ocr_model_dir() -> str:
    """Returns absolute path to the local model storage directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "storage", "models", "easyocr")


def check_ocr_readiness() -> Tuple[bool, str]:
    """
    Checks if EasyOCR package and required model weights are provisioned and accessible.
    Strictly read-only; never triggers network requests or model downloads.
    """
    try:
        import easyocr  # noqa: F401
    except ImportError:
        return False, "EasyOCR package not installed in environment"

    model_dir = get_ocr_model_dir()
    craft_path = os.path.join(model_dir, "craft_mlt_25k.pth")
    recog_path = os.path.join(model_dir, "english_g2.pth")

    if not os.path.isfile(craft_path):
        return False, f"Detection model weights missing: {craft_path}"
    if not os.path.isfile(recog_path):
        return False, f"Recognition model weights missing: {recog_path}"
    if os.path.getsize(craft_path) < 1000000:
        return False, f"Detection model weights corrupted or incomplete ({os.path.getsize(craft_path)} bytes)"
    if os.path.getsize(recog_path) < 1000000:
        return False, f"Recognition model weights corrupted or incomplete ({os.path.getsize(recog_path)} bytes)"

    return True, "EasyOCR and pre-provisioned model weights verified ready"


def get_ocr_reader() -> Optional[Any]:
    """
    Lazy singleton initialization of EasyOCR engine configured for CPU execution
    with local model storage.
    Strictly forbids request-time model downloads: models must be pre-provisioned.
    """
    global _ocr_reader, _ocr_initialized
    if _ocr_initialized:
        return _ocr_reader
    try:
        ready, reason = check_ocr_readiness()
        if not ready:
            logger.warning(f"EasyOCR reader unavailable: {reason}. Request-time model download is disabled.")
            _ocr_reader = None
            _ocr_initialized = True
            return None

        import easyocr
        model_dir = get_ocr_model_dir()
        user_net_dir = os.path.join(model_dir, "user_network")
        os.makedirs(user_net_dir, exist_ok=True)

        _ocr_reader = easyocr.Reader(
            ["en"],
            gpu=False,
            model_storage_directory=model_dir,
            user_network_directory=user_net_dir,
            download_enabled=False,
            verbose=False,
        )
        logger.info("EasyOCR engine successfully initialized from pre-provisioned local models.")
    except Exception as e:
        logger.warning(f"EasyOCR reader initialization unavailable or failed: {e}")
        _ocr_reader = None
    finally:
        _ocr_initialized = True
    return _ocr_reader


class OCRExtractorService:
    @staticmethod
    def extract_text_and_pages(file_path: str, mime_type: str) -> Tuple[str, int, List[Dict[str, Any]], float]:
        """
        Executes hybrid document processing:
        1. Fast-path digital vector text extraction via PyMuPDF.
        2. Per-page rasterization and genuine OCR (EasyOCR) for scanned or image-only pages.
        3. Direct genuine OCR for uploaded image files.
        Returns: (full_text, page_count, pages_metadata, average_confidence)
        """
        if not os.path.isfile(file_path):
            raise ValueError(f"Document file not found at path: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > MAX_DOCUMENT_FILE_SIZE:
            raise ValueError(f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum permitted limit of 50 MB.")

        pages_metadata: List[Dict[str, Any]] = []
        all_text_parts: List[str] = []
        confidences: List[float] = []

        if "pdf" in mime_type.lower() or file_path.lower().endswith(".pdf"):
            try:
                doc = pymupdf.open(file_path)
            except Exception as e:
                raise ValueError(f"Corrupt, damaged, or unreadable PDF document: {str(e)}")

            try:
                if doc.is_encrypted:
                    raise ValueError("Password-protected or encrypted PDF documents cannot be processed.")

                page_count = len(doc)
                if page_count == 0:
                    raise ValueError("PDF document contains 0 pages.")
                if page_count > MAX_DOCUMENT_PAGE_COUNT:
                    raise ValueError(f"Document contains {page_count} pages, exceeding the maximum allowed limit of {MAX_DOCUMENT_PAGE_COUNT} pages.")

                for page_idx in range(page_count):
                    page = doc[page_idx]
                    page_num = page_idx + 1

                    # 1. Attempt digital vector text extraction first
                    digital_text = page.get_text("text").strip()
                    alnum_chars = re.sub(r"[^A-Za-z0-9]", "", digital_text)

                    if len(alnum_chars) >= 25:
                        # Page has usable digital vector text (fast path)
                        method = "DIGITAL_TEXT"
                        page_text = digital_text
                        page_conf = 0.98
                        is_scanned = False
                    else:
                        # Page lacks usable text; render raster pixmap and run genuine OCR
                        method = "OCR_RASTER"
                        is_scanned = True
                        try:
                            pix = page.get_pixmap(dpi=150)
                            img_bytes = pix.tobytes("png")
                            pix = None  # Free pixmap memory immediately

                            reader = get_ocr_reader()
                            if reader:
                                results = reader.readtext(img_bytes)
                                lines = [r[1].strip() for r in results if r[1] and r[1].strip()]
                                confs = [float(r[2]) for r in results if r[1] and r[1].strip()]
                                if lines:
                                    ocr_text = "\n".join(lines)
                                    page_conf = round(sum(confs) / len(confs), 2)
                                    page_text = ocr_text
                                else:
                                    page_text = "[No legible text recognized by OCR on scanned page]"
                                    page_conf = 0.0
                            else:
                                method = "OCR_UNAVAILABLE"
                                page_text = "[Scanned page detected; OCR engine unavailable in environment]"
                                page_conf = 0.0
                        except Exception as ocr_err:
                            logger.error(f"OCR raster processing failed on page {page_num}: {ocr_err}", exc_info=True)
                            method = "OCR_FAILED"
                            page_text = f"[OCR processing failed on page {page_num}: {str(ocr_err)}]"
                            page_conf = 0.0

                    confidences.append(page_conf)
                    all_text_parts.append(f"--- [Page {page_num} ({method})] ---\n{page_text}")
                    pages_metadata.append({
                        "page": page_num,
                        "text": page_text,
                        "char_count": len(page_text),
                        "extraction_method": method,
                        "is_scanned": is_scanned,
                        "confidence": page_conf,
                    })

                full_text = "\n\n".join(all_text_parts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                return full_text, page_count, pages_metadata, round(avg_conf, 2)

            finally:
                doc.close()

        else:
            # Direct Image inspection and genuine OCR
            try:
                with Image.open(file_path) as img:
                    img.verify()
            except Exception as e:
                raise ValueError(f"Corrupt, damaged, or unsupported image file: {str(e)}")

            reader = get_ocr_reader()
            if reader:
                try:
                    results = reader.readtext(file_path)
                    lines = [r[1].strip() for r in results if r[1] and r[1].strip()]
                    confs = [float(r[2]) for r in results if r[1] and r[1].strip()]
                    if lines:
                        text = "\n".join(lines)
                        avg_conf = round(sum(confs) / len(confs), 2)
                        method = "OCR_RASTER"
                    else:
                        text = "[No legible text recognized by OCR on image document]"
                        avg_conf = 0.0
                        method = "OCR_RASTER"
                except Exception as img_err:
                    logger.error(f"OCR failed for image {file_path}: {img_err}", exc_info=True)
                    text = f"[OCR processing failed for image: {str(img_err)}]"
                    avg_conf = 0.0
                    method = "OCR_FAILED"
            else:
                text = "[Image document detected; OCR engine unavailable in environment]"
                avg_conf = 0.0
                method = "OCR_UNAVAILABLE"

            full_text = f"--- [Page 1 ({method})] ---\n{text}"
            pages_metadata = [{
                "page": 1,
                "text": text,
                "char_count": len(text),
                "extraction_method": method,
                "is_scanned": True,
                "confidence": avg_conf,
            }]
            return full_text, 1, pages_metadata, avg_conf

    @staticmethod
    def _create_field_entry(val: str, snippet: str, p: Dict[str, Any], default_conf: float = 0.90) -> Dict[str, Any]:
        """Creates a standardized structured field dictionary with traceable provenance."""
        conf = round(p.get("confidence", default_conf), 2)
        return {
            "value": val,
            "page": p["page"],
            "confidence": conf,
            "source_snippet": snippet,
            "corrected": False,
            "is_ocr_derived": bool(p.get("is_scanned", False)),
            "extraction_method": p.get("extraction_method", "DIGITAL_TEXT"),
        }

    @classmethod
    def extract_structured_fields(
        cls, text: str, document_type: str, pages_metadata: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extracts regulatory fields with page references, evidence spans, and OCR provenance based on document category.
        Returns: {field_name: {value, page, confidence, source_snippet, is_ocr_derived, extraction_method}}
        """
        extracted: Dict[str, Dict[str, Any]] = {}

        def search_span(pattern: str, page_num: int, page_text: str) -> Optional[Tuple[str, str]]:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                start = max(0, match.start() - 20)
                end = min(len(page_text), match.end() + 20)
                snippet = page_text[start:end].replace("\n", " ").strip()
                return val, snippet
            return None

        # 1. Institution Name (common)
        inst_patterns = [
            r"(?:name\s+of\s+(?:the\s+)?(?:institution|college|applicant)|institute|college)\s*[:\-]\s*([^\r\n]{3,60})",
            r"(?:in\s+favour\s+of|favouring|granted\s+to)\s+([^\r\n]{5,50}\s+(?:Institute|College|Trust|Society))",
        ]
        for p in pages_metadata:
            for pat in inst_patterns:
                res = search_span(pat, p["page"], p["text"])
                if res and "institution_name" not in extracted:
                    extracted["institution_name"] = cls._create_field_entry(res[0], res[1], p, 0.92)
                    break

        # 2. Document/Certificate Number
        num_patterns = [
            r"(?:cert(?:ificate)?|noc|order|deed|letter|approval|file|reg(?:istration)?)\s*(?:no\.?|na\.?|number|reference|ref\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_']{4,35})",
            r"(?:no|na)\.\s*[:\-]?\s*([A-Za-z0-9\/\-_']{4,35})",
        ]
        for p in pages_metadata:
            for pat in num_patterns:
                res = search_span(pat, p["page"], p["text"])
                if res and "certificate_number" not in extracted:
                    extracted["certificate_number"] = cls._create_field_entry(res[0].replace("'", "/"), res[1], p, 0.89)
                    break

        # 3. Dates (Issue Date & Expiry / Valid Until)
        date_pattern = r"(?:dated?|date\s+of\s+issue|issued\s+on)\s*[:\-]?\s*(\d{1,2}[\/\-\.,]\d{1,2}[\/\-\.,]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})"
        expiry_pattern = r"(?:valid\s+(?:up\s*to|until|till)|expiry\s+date)\s*[:\-]?\s*(\d{1,2}[\/\-\.,]\d{1,2}[\/\-\.,]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})"

        for p in pages_metadata:
            res_date = search_span(date_pattern, p["page"], p["text"])
            if res_date and "issue_date" not in extracted:
                norm_date = res_date[0].replace(",", "/")
                extracted["issue_date"] = cls._create_field_entry(norm_date, res_date[1], p, 0.91)

            res_exp = search_span(expiry_pattern, p["page"], p["text"])
            if res_exp and "valid_until" not in extracted:
                norm_exp = res_exp[0].replace(",", "/")
                extracted["valid_until"] = cls._create_field_entry(norm_exp, res_exp[1], p, 0.94)

        # 4. Issuing Authority
        auth_patterns = [
            r"(?:issued\s+by|sanctioning\s+authority|office\s+of\s+the|competent\s+authority)\s*[:\-]?\s*([A-Za-z\s.,]{4,60})",
            r"(Director\s+General\s+of\s+Fire\s+Services|Chief\s+Fire\s+Officer|Town\s+and\s+Country\s+Planning|Municipal\s+Corporation|State\s+Revenue\s+Department|Sub-Registrar)",
        ]
        for p in pages_metadata:
            for pat in auth_patterns:
                res = search_span(pat, p["page"], p["text"])
                if res and "issuing_authority" not in extracted:
                    extracted["issuing_authority"] = cls._create_field_entry(res[0], res[1], p, 0.88)
                    break

        # 5. Land Specific: Survey No, Land Area, Unit (Exclude Satellite Imagery)
        if ("land" in document_type.lower() or "title" in document_type.lower()) and "satellite" not in document_type.lower():
            survey_patterns = [
                r"(?:survey\s*(?:no\.?|number)|khasra\s*(?:no\.?|number)|gat\s*no\.?)\s*[:\-]?\s*([0-9\/\-_A-Za-z,\s]{2,30})",
            ]
            area_patterns = [
                r"(?:land\s+area|total\s+area|measuring|extent\s+of\s+land)\s*[:\-]?\s*([0-9.,]+)\s*(acres?|hectares?|sq\.?\s*(?:mtrs?|meters?|ft|yards?))",
            ]
            for p in pages_metadata:
                for pat in survey_patterns:
                    res = search_span(pat, p["page"], p["text"])
                    if res and "survey_number" not in extracted:
                        extracted["survey_number"] = cls._create_field_entry(res[0], res[1], p, 0.93)
                        break

                match_area = re.search(area_patterns[0], p["text"], re.IGNORECASE)
                if match_area and "land_area" not in extracted:
                    extracted["land_area"] = cls._create_field_entry(match_area.group(1).strip(), match_area.group(0), p, 0.95)
                    extracted["land_area_unit"] = cls._create_field_entry(match_area.group(2).strip(), match_area.group(0), p, 0.95)

        # 6. Satellite Map of Land (Geo Coordinates & Entrance)
        if "satellite" in document_type.lower() or "map" in document_type.lower():
            lat_patterns = [
                r"(?:latitude|lat\.?)\s*[:\-]?\s*([0-9]{1,2}\.[0-9]{3,8}[°\s]*[NS]?)",
                r"([0-9]{1,2}\.[0-9]{4,8}\s*°?\s*[NS])",
            ]
            lon_patterns = [
                r"(?:longitude|long\.?|lon\.?)\s*[:\-]?\s*([0-9]{1,3}\.[0-9]{3,8}[°\s]*[EW]?)",
                r"([0-9]{1,3}\.[0-9]{4,8}\s*°?\s*[EW])",
            ]
            for p in pages_metadata:
                for pat in lat_patterns:
                    res = search_span(pat, p["page"], p["text"])
                    if res and "latitude" not in extracted:
                        extracted["latitude"] = cls._create_field_entry(res[0], res[1], p, 0.92)
                        break
                for pat in lon_patterns:
                    res = search_span(pat, p["page"], p["text"])
                    if res and "longitude" not in extracted:
                        extracted["longitude"] = cls._create_field_entry(res[0], res[1], p, 0.92)
                        break

        # 7. Affidavit 2 Specific: Stamp Duty, Sworn Authority, Signatory
        if "affidavit" in document_type.lower():
            stamp_pat = r"(?:stamp\s*(?:duty|amount|value)|e-?stamp)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9.,]+)"
            sworn_pat = r"(?:sworn\s+before|notary\s+public|judicial\s+magistrate|oath\s+commissioner|deposed\s+before)\s*[:\-]?\s*([A-Za-z\s.,]{3,50})"
            desig_pat = r"(Chairman|Secretary|President|Authorized Signatory)"
            for p in pages_metadata:
                res_stamp = search_span(stamp_pat, p["page"], p["text"])
                if res_stamp and "stamp_duty_amount" not in extracted:
                    extracted["stamp_duty_amount"] = cls._create_field_entry(res_stamp[0], res_stamp[1], p, 0.91)
                res_sworn = search_span(sworn_pat, p["page"], p["text"])
                if res_sworn and "sworn_before" not in extracted:
                    extracted["sworn_before"] = cls._create_field_entry(res_sworn[0], res_sworn[1], p, 0.89)
                res_desig = search_span(desig_pat, p["page"], p["text"])
                if res_desig and "signatory_designation" not in extracted:
                    extracted["signatory_designation"] = cls._create_field_entry(res_desig[0], res_desig[1], p, 0.90)

        # 8. Structural Stability: Engineer details & building age
        if "structural" in document_type.lower() or "stability" in document_type.lower():
            eng_pat = r"(?:structural\s*engineer|consulting\s*engineer|certified\s*by)\s*[:\-]?\s*([A-Za-z\s.,]{3,50})"
            age_pat = r"(?:building\s*age|age\s*of\s*building|years?\s*old|constructed\s*in)\s*[:\-]?\s*([0-9]{1,3}(?:\s*years)?|\d{4})"
            for p in pages_metadata:
                res_eng = search_span(eng_pat, p["page"], p["text"])
                if res_eng and "structural_engineer_name" not in extracted:
                    extracted["structural_engineer_name"] = cls._create_field_entry(res_eng[0], res_eng[1], p, 0.90)
                res_age = search_span(age_pat, p["page"], p["text"])
                if res_age and "building_age_years" not in extracted:
                    extracted["building_age_years"] = cls._create_field_entry(res_age[0], res_age[1], p, 0.92)

        # 9. Audited Accounts: Financial Year & CA Membership
        if "audit" in document_type.lower() or "account" in document_type.lower():
            fy_pat = r"(?:financial\s*year|f\.?y\.?|year\s*ended)\s*[:\-]?\s*(\d{4}[\s\-–\/]\d{2,4}|\d{4})"
            ca_pat = r"(?:membership\s*(?:no\.?|number)|ca\s*reg\.?|m\.?\s*no\.?)\s*[:\-]?\s*([0-9]{4,8})"
            for p in pages_metadata:
                res_fy = search_span(fy_pat, p["page"], p["text"])
                if res_fy and "financial_year" not in extracted:
                    extracted["financial_year"] = cls._create_field_entry(res_fy[0], res_fy[1], p, 0.93)
                res_ca = search_span(ca_pat, p["page"], p["text"])
                if res_ca and "ca_membership_number" not in extracted:
                    extracted["ca_membership_number"] = cls._create_field_entry(res_ca[0], res_ca[1], p, 0.92)

        # 10. Building / Instructional Area
        if "building" in document_type.lower() or "architect" in document_type.lower():
            built_up_pattern = r"(?:built[\s\-]up\s+area|carpet\s+area|total\s+instructional\s+area)\s*[:\-]?\s*([0-9.,]+)\s*(?:sq\.?\s*m(?:trs?|meters?)?|sq\.?\s*ft)?"
            for p in pages_metadata:
                res_bld = search_span(built_up_pattern, p["page"], p["text"])
                if res_bld and "built_up_area_sqm" not in extracted:
                    extracted["built_up_area_sqm"] = cls._create_field_entry(res_bld[0], res_bld[1], p, 0.90)

        # 11. Format 3 Resolution & Governance
        if "resolution" in document_type.lower() or "format 3" in document_type.lower():
            res_num_pat = r"(?:resolution\s*(?:no\.?|number)|item\s*no\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]{2,30})"
            for p in pages_metadata:
                res_r = search_span(res_num_pat, p["page"], p["text"])
                if res_r and "resolution_number" not in extracted:
                    extracted["resolution_number"] = cls._create_field_entry(res_r[0], res_r[1], p, 0.91)

        # 12. Bank Certificate 3
        if "bank" in document_type.lower() or "certificate 3" in document_type.lower():
            fdr_pat = r"(?:fdr\s*(?:no\.?|account|number)|deposit\s*receipt\s*no\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]{4,30})"
            amt_pat = r"(?:deposit\s*amount|fdr\s*amount|sum\s*of\s*(?:rs\.?|inr|₹)?)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9.,]+)"
            for p in pages_metadata:
                res_fdr = search_span(fdr_pat, p["page"], p["text"])
                if res_fdr and "fdr_account_number" not in extracted:
                    extracted["fdr_account_number"] = cls._create_field_entry(res_fdr[0], res_fdr[1], p, 0.92)
                res_amt = search_span(amt_pat, p["page"], p["text"])
                if res_amt and "deposit_amount" not in extracted:
                    extracted["deposit_amount"] = cls._create_field_entry(res_amt[0], res_amt[1], p, 0.90)

        # 13. Proposed Site Details (Change of Site)
        if "proposed" in document_type.lower() or "format 2" in document_type.lower():
            prop_addr_pat = r"(?:proposed\s*(?:site|location|campus)\s*address|at\s*village|situated\s*at)\s*[:\-]?\s*([A-Za-z0-9\s,.'\-]{3,60})"
            for p in pages_metadata:
                res_addr = search_span(prop_addr_pat, p["page"], p["text"])
                if res_addr and "proposed_site_address" not in extracted:
                    extracted["proposed_site_address"] = cls._create_field_entry(res_addr[0], res_addr[1], p, 0.88)

        return extracted
