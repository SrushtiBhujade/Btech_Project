import os
import json
from typing import List, Dict

import google.generativeai as genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _get_model():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-flash-latest")


def summarize_expenses(expenses: List[Dict]) -> str:
    """Generate a human-readable summary of recent expenses."""
    model = _get_model()
    if not model or not expenses:
        return _fallback_summary(expenses)

    expense_text = "\n".join(
        [f"- {e['date']}: {e['vendor']} ({e['category']}) — ₹{e['amount']:.2f}"
         for e in expenses[:50]]
    )

    prompt = f"""Analyze the following expense records and write a friendly, insightful summary 
for the user in 3-4 sentences. Mention: total spent, top spending categories, biggest single expense,
and any notable patterns. Use Indian Rupees (₹).

Expense Records:
{expense_text}

Write a helpful, conversational summary:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _fallback_summary(expenses)


def get_recommendations(expenses: List[Dict], summary_stats: Dict) -> str:
    """Generate personalized saving recommendations."""
    model = _get_model()
    if not model:
        return _fallback_recommendations()

    expense_text = "\n".join(
        [f"- {e['category']}: ₹{e['amount']:.2f} at {e['vendor']}"
         for e in expenses[:30]]
    )

    stats_text = json.dumps(summary_stats, indent=2)

    prompt = f"""You are a personal finance advisor. Based on the user's expenses below,
give 5 specific, actionable saving tips. Be friendly, practical, and mention specific categories.
Use Indian Rupees (₹).

Summary Stats:
{stats_text}

Recent Expenses:
{expense_text}

Provide 5 numbered saving recommendations:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _fallback_recommendations()


def chat_with_expenses(user_message: str, expenses: List[Dict], history: List[Dict]) -> str:
    """Chat with AI about expenses."""
    model = _get_model()
    if not model:
        return "AI assistant is not available. Please add your Gemini API key in the .env file."

    expense_context = "\n".join(
        [f"- {e['date']}: {e['vendor']} ({e['category']}) — ₹{e['amount']:.2f} | {e['description']}"
         for e in expenses[:100]]
    )

    system_context = f"""You are a helpful personal finance assistant for an Indian user.
You have access to their expense history below. Answer questions about their spending honestly and helpfully.
Use Indian Rupees (₹). Be concise and friendly.

Expense History (most recent 100 entries):
{expense_context}

Today's date: {__import__('datetime').date.today().isoformat()}"""

    # Build conversation
    chat = model.start_chat(history=[])
    full_prompt = f"{system_context}\n\nUser: {user_message}"

    try:
        response = chat.send_message(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I couldn't process your query. Error: {str(e)}"


def _fallback_summary(expenses: List[Dict]) -> str:
    if not expenses:
        return "No expenses recorded yet. Upload your first bill to get started!"
    total = sum(e.get("amount", 0) for e in expenses)
    cats = {}
    for e in expenses:
        cats[e.get("category", "Other")] = cats.get(e.get("category", "Other"), 0) + e.get("amount", 0)
    top_cat = max(cats, key=cats.get) if cats else "N/A"
    return (f"You have {len(expenses)} recorded expenses totalling ₹{total:,.2f}. "
            f"Your biggest spending category is {top_cat}. "
            f"Add your Gemini API key for deeper AI insights!")


def _fallback_recommendations() -> str:
    return """Here are some general saving tips:
1. **Track every expense** — You're already doing this! Keep it up.
2. **Follow the 50/30/20 rule** — 50% needs, 30% wants, 20% savings.
3. **Plan your groceries** — Make a list before shopping to avoid impulse buys.
4. **Reduce dining out** — Cook at home more often; it's healthier and cheaper.
5. **Add Gemini API key** — Get personalized AI-powered recommendations!"""
