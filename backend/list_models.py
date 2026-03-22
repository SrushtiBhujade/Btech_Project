import os
import google.generativeai as genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
