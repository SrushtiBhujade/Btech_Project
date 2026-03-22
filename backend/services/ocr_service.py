import os
import re
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract


def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhance image for better OCR accuracy."""
    # Convert to grayscale
    image = image.convert("L")
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)
    return image


def extract_text_from_image(image_path: str) -> str:
    """
    Extract raw text from a bill image using Tesseract OCR.
    Returns cleaned text string.
    """
    try:
        img = Image.open(image_path)
        img = preprocess_image(img)

        # OCR config: treat as a single block of text
        custom_config = r"--oem 3 --psm 6"
        raw_text = pytesseract.image_to_string(img, config=custom_config)

        # Clean up whitespace
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        return f"OCR_ERROR: {str(e)}"


def fallback_extract_amount(text: str) -> float:
    """Regex fallback to extract monetary amount from text."""
    # Match patterns like: Rs. 250, ₹ 1,234.50, 250.00, Total: 500
    patterns = [
        r"(?:total|amount|total amount|grand total|net amount|payable)[^\d]*(\d[\d,]*\.?\d*)",
        r"(?:rs\.?|₹|inr)\s*(\d[\d,]*\.?\d*)",
        r"(\d[\d,]*\.\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return float(amount_str)
            except ValueError:
                continue
    return 0.0


def fallback_extract_date(text: str) -> str:
    """Regex fallback to extract date from text."""
    from datetime import datetime, date

    patterns = [
        r"(\d{2})[\/\-](\d{2})[\/\-](\d{4})",  # DD/MM/YYYY
        r"(\d{4})[\/\-](\d{2})[\/\-](\d{2})",  # YYYY-MM-DD
        r"(\d{1,2})\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3 and len(groups[2]) == 4:
                    # DD/MM/YYYY
                    return f"{groups[2]}-{groups[1].zfill(2)}-{groups[0].zfill(2)}"
                elif len(groups) == 3 and len(groups[0]) == 4:
                    # YYYY-MM-DD
                    return f"{groups[0]}-{groups[1]}-{groups[2]}"
            except Exception:
                continue

    return date.today().isoformat()
