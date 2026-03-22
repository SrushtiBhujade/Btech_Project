import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")

from services.extractor import EXTRACTION_PROMPT_TEMPLATE, CATEGORIES

ocr_text = """
ESTIMATE
Party: GAURAV
8:00:04PM
Bill No. 5128 DATE: 04-02-2026
Sr. Item Name QTY Price Amt
1 OXYTOP 1L 1 80.00 80.00
2 OXYTOP 500ML 1 120.00 120.00
3 DIET COKE 1 700.00 700.00
Total Qty : 3
Bill Amount : - ₹ 900.00
Old Balace 1,070.00
Net Balance 1,970.00
"""

prompt = EXTRACTION_PROMPT_TEMPLATE.replace("{categories}", ", ".join(CATEGORIES)).replace("{ocr_text}", ocr_text)
print("Prompt:\n", prompt)
print("---")
response = model.generate_content(prompt)
print("Raw Response:", repr(response.text))
