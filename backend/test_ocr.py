import sys
import os
from services.ocr_service import extract_text_from_image, fallback_extract_amount
from services.extractor import extract_fields_with_ai

ocr_text = extract_text_from_image("sample.jpg")
print("OCR Output excerpt:", ocr_text[:200].replace('\n', ' | '))

ai_result = extract_fields_with_ai(ocr_text)
print("\nAI Result:", ai_result)
