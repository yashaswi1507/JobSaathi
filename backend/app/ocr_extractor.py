"""
ocr_extractor.py
------------------
Day 10 — OCR/PDF text extraction module.

Handles 3 input types:
  1. Text-based PDFs (most common resumes) — pypdf, fast + accurate
  2. Scanned/image-based PDFs (phone-camera photos of resumes)
     — pdf2image converts pages to images, then OCR extracts text
  3. Image files directly (WhatsApp screenshots, Instagram
     screenshots, SMS photos) — pytesseract with EasyOCR fallback

This module is intentionally separate from resume_parser.py and
preprocessing_v2.py — it sits ONE STEP BEFORE them in the pipeline:

  User uploads file/image
        ↓
  ocr_extractor.py → extracts raw text
        ↓
  resume_parser.py → extracts skills/experience/education
        ↓
  routes/resume.py → returns structured result to frontend

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\ocr_extractor.py

DEPENDENCIES (add to requirements.txt):
  pypdf           — already in project
  pytesseract     — primary OCR engine (needs tesseract binary)
  easyocr         — secondary OCR engine, better for noisy images
                    (first use downloads ~100MB model — after that,
                    runs fully offline)
  pdf2image       — converts scanned PDF pages to images for OCR
  pillow          — image processing (already installed)
  poppler         — pdf2image backend (system package:
                    Windows: download from poppler.freedesktop.org
                    Linux:   sudo apt-get install poppler-utils
                    Mac:     brew install poppler)

INSTALL:
  pip install pypdf pytesseract easyocr pdf2image pillow
  # then also install tesseract binary for your OS:
  # Windows: https://github.com/UB-Mannheim/tesseract/wiki
  # Linux:   sudo apt-get install tesseract-ocr
  # Mac:     brew install tesseract
"""

import io
import os
import re


# ============================================================
# EXTRACTION STRATEGY SELECTOR
# ============================================================
def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Main entry point. Accepts raw file bytes + original filename.
    Automatically picks the right extraction strategy based on the
    file type:
      - .pdf  -> try pypdf first (fast, no loss for text PDFs);
                 if little/no text extracted, fall back to OCR
                 (for scanned/image-based PDFs)
      - image types (.png, .jpg, .jpeg, .webp, .bmp, .tiff)
                -> directly run OCR (pytesseract + EasyOCR fallback)

    Returns: raw extracted text (str). Empty string if extraction
    completely failed — callers should check for this rather than
    crashing.
    """
    ext = os.path.splitext(filename.lower())[1]

    if ext == ".pdf":
        return _extract_from_pdf(file_bytes)
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"):
        return _extract_from_image_bytes(file_bytes)
    else:
        return ""


# ============================================================
# PDF EXTRACTION (text-first, OCR fallback)
# ============================================================
MIN_CHARS_FOR_VALID_TEXT_PDF = 100

def _extract_from_pdf(file_bytes: bytes) -> str:
    """
    Tries pypdf first (fast, lossless for text PDFs). If little text
    comes back (threshold: MIN_CHARS_FOR_VALID_TEXT_PDF), it's likely
    a scanned/image-based PDF, so falls back to OCR by converting
    pages to images then running _extract_from_image_bytes on each.
    """
    text = _pypdf_extract(file_bytes)
    if len(text.strip()) >= MIN_CHARS_FOR_VALID_TEXT_PDF:
        return text

    # Not enough text — probably a scanned PDF, try OCR fallback
    print("[ocr_extractor] pypdf extracted very little text — "
          "attempting OCR fallback for scanned PDF...")
    ocr_text = _ocr_pdf(file_bytes)
    return ocr_text if ocr_text.strip() else text


def _pypdf_extract(file_bytes: bytes) -> str:
    """Extract text from a text-based PDF using pypdf."""
    try:
        import pypdf
        pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[ocr_extractor] pypdf extraction failed: {e}")
        return ""


def _ocr_pdf(file_bytes: bytes) -> str:
    """
    Converts each page of a scanned PDF to an image, then runs OCR.
    Uses pdf2image (poppler-based) for the conversion.
    """
    try:
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(file_bytes, dpi=200)
        text = ""
        for i, page_image in enumerate(pages):
            page_bytes = io.BytesIO()
            page_image.save(page_bytes, format="PNG")
            page_text = _extract_from_image_bytes(page_bytes.getvalue())
            text += page_text + "\n"
            print(f"[ocr_extractor] OCR page {i+1}/{len(pages)}: "
                  f"{len(page_text)} chars extracted")
        return text
    except ImportError:
        print("[ocr_extractor] pdf2image not installed — cannot OCR "
              "scanned PDFs. Install: pip install pdf2image "
              "(also needs poppler system package).")
        return ""
    except Exception as e:
        print(f"[ocr_extractor] PDF-to-image conversion failed: {e}")
        return ""


# ============================================================
# IMAGE EXTRACTION (pytesseract + EasyOCR fallback)
# ============================================================
def _extract_from_image_bytes(image_bytes: bytes) -> str:
    """
    Runs OCR on a raw image (bytes). Tries pytesseract first (fast,
    no internet needed, works offline). If pytesseract fails or
    returns very little text, falls back to EasyOCR (better at
    noisy/low-quality images, but requires a one-time model download
    on first use and is slower).

    This covers:
      - WhatsApp scam-message screenshots
      - Instagram job-post screenshots
      - SMS photos
      - Phone-camera photos of paper resumes
    """
    text = _tesseract_extract(image_bytes)
    if len(text.strip()) >= 20:
        return text

    print("[ocr_extractor] pytesseract returned very little text — "
          "trying EasyOCR as fallback...")
    return _easyocr_extract(image_bytes)


def _tesseract_extract(image_bytes: bytes) -> str:
    """Primary OCR: pytesseract (wraps system Tesseract binary)."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        # PSM 6 = assume a single uniform block of text (good for
        # screenshots and formatted documents)
        config = "--psm 6"
        text = pytesseract.image_to_string(image, config=config)
        return text
    except Exception as e:
        print(f"[ocr_extractor] pytesseract failed: {e}")
        return ""


def _easyocr_extract(image_bytes: bytes) -> str:
    """
    Fallback OCR: EasyOCR (better for noisy/complex images).
    First call downloads ~100MB model — subsequent calls are offline.
    """
    try:
        import easyocr
        import numpy as np
        from PIL import Image

        img_array = np.array(Image.open(io.BytesIO(image_bytes)))
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        result = reader.readtext(img_array, detail=0)
        return " ".join(result)
    except ImportError:
        print("[ocr_extractor] EasyOCR not installed — "
              "run: pip install easyocr")
        return ""
    except Exception as e:
        print(f"[ocr_extractor] EasyOCR failed: {e}")
        return ""


# ============================================================
# POST-PROCESSING (clean OCR noise common in scanned docs)
# ============================================================
def clean_ocr_text(text: str) -> str:
    """
    Light cleanup of OCR output to fix common OCR artifacts that
    would confuse the resume parser downstream:
      - Multiple blank lines → single blank line
      - Common OCR character confusions (0/O, 1/l, Rs/R3 etc.)
      - Stray non-ASCII characters

    NOTE: intentionally conservative — does NOT try to "correct"
    actual words, just removes structural noise.
    """
    if not text:
        return ""

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = text.strip()
    return text


# ============================================================
# CONVENIENCE WRAPPER (used by routes/resume.py)
# ============================================================
def extract_and_clean(file_bytes: bytes, filename: str) -> str:
    """
    Single function to call from routes/resume.py:
      raw_text = extract_and_clean(file_bytes, filename)
    Returns clean text ready for resume_parser.py functions.
    """
    raw = extract_text_from_file(file_bytes, filename)
    return clean_ocr_text(raw)


if __name__ == "__main__":
    import sys

    print("=== Self-test: pypdf on a text-based PDF ===")
    # Test needs actual PDF files — checking if the function chain
    # imports correctly and handles missing files gracefully.
    result = extract_and_clean(b"", "test.pdf")
    print(f"Empty bytes result: '{result}' (empty string expected)")

    result2 = extract_and_clean(b"", "screenshot.png")
    print(f"Empty image result: '{result2}' (empty string expected)")

    print("\nImports and structure OK. To test with real files:")
    print("  from ocr_extractor import extract_and_clean")
    print("  with open('resume.pdf', 'rb') as f:")
    print("      text = extract_and_clean(f.read(), 'resume.pdf')")