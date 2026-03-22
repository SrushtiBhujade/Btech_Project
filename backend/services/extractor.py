import os
import json
import re
from datetime import date

import google.generativeai as genai
from dotenv import load_dotenv
from .ocr_service import fallback_extract_amount, fallback_extract_date

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Transport",
    "Healthcare",
    "Utilities",
    "Shopping",
    "Entertainment",
    "Education",
    "Travel",
    "Other",
]

EXTRACTION_PROMPT_TEMPLATE = """
You are a bill/receipt data extraction assistant. Given raw OCR text from a bill or receipt,
extract the following fields and return ONLY a valid JSON object with these exact keys:

{{
  "amount": <float, the total amount paid>,
  "category": <one of: {categories}>,
  "vendor": <string, merchant/shop name>,
  "date": <string, in YYYY-MM-DD format>,
  "description": <string, one-line summary of what was purchased>
}}

Rules:
- amount: Extract the TOTAL/GRAND TOTAL paid. Must be a number, never null.
- category: Pick the most appropriate category from the list.
- vendor: The business/merchant name from the bill header.
- date: Convert any date format to YYYY-MM-DD. If not found, use today's date.
- description: Brief summary like "Grocery shopping at D-Mart" or "Electricity bill for March".

OCR Text from Bill:
---
{ocr_text}
---

Return ONLY the JSON object, no markdown, no explanation.
"""

EXTRACTION_PROMPT = EXTRACTION_PROMPT_TEMPLATE.format(
    categories=", ".join(CATEGORIES), ocr_text="{ocr_text}"
)


def extract_fields_with_ai(ocr_text: str) -> dict:
    """Use Gemini to extract structured fields from OCR text."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return _fallback_extraction(ocr_text)

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")

        prompt = EXTRACTION_PROMPT.replace("{ocr_text}", ocr_text)
        response = model.generate_content(prompt)

        # Parse JSON from response
        raw = response.text.strip()
        # Remove markdown code fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

        data = json.loads(raw)

        # Validate and sanitize
        return {
            "amount": float(data.get("amount") or 0),
            "category": data.get("category", "Other"),
            "vendor": str(data.get("vendor", "Unknown")),
            "date": str(data.get("date", date.today().isoformat())),
            "description": str(data.get("description", "")),
        }

    except Exception as e:
        print(f"[Extractor] Gemini extraction failed: {e}. Using fallback.")
        return _fallback_extraction(ocr_text)


def _fallback_extraction(ocr_text: str) -> dict:
    """Rule-based fallback extraction when AI is unavailable."""
    amount = fallback_extract_amount(ocr_text)
    extracted_date = fallback_extract_date(ocr_text)

    # Guess vendor from first non-empty line
    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
    vendor = lines[0] if lines else "Unknown"
    # If vendor looks like a number, skip it
    if vendor and vendor[0].isdigit():
        vendor = lines[1] if len(lines) > 1 else "Unknown"

    # Guess category by keywords
    lower_text = ocr_text.lower()
    category = "Other"
    keyword_map = {
        "Food & Dining": ["restaurant", "cafe", "hotel", "food", "zomato", "swiggy", "biryani", "pizza"],
        "Groceries": ["grocery", "supermarket", "mart", "d-mart", "dmart", "reliance fresh", "bigbasket"],
        "Transport": ["uber", "ola", "petrol", "diesel", "fuel", "railway", "bus", "metro", "toll"],
        "Healthcare": ["pharmacy", "medical", "hospital", "clinic", "doctor", "medicine", "apollo"],
        "Utilities": ["electricity", "water", "gas", "recharge", "broadband", "internet", "bill"],
        "Shopping": ["amazon", "flipkart", "myntra", "clothes", "fashion", "electronics"],
        "Entertainment": ["netflix", "cinema", "movie", "ticket", "hotstar", "prime"],
        "Education": ["school", "college", "tuition", "fee", "course", "book"],
        "Travel": ["hotel", "flight", "makemytrip", "goibibo", "booking"],
    }
    for cat, keywords in keyword_map.items():
        if any(kw in lower_text for kw in keywords):
            category = cat
            break

    return {
        "amount": amount,
        "category": category,
        "vendor": vendor[:100],
        "date": extracted_date,
        "description": f"Bill from {vendor}",
    }
