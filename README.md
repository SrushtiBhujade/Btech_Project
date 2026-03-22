# 💳 SmartBill — AI-Powered Expense Tracker

> Upload a photo of any bill → AI extracts the data → Beautiful dashboard analytics + AI insights

---

## ✨ Features

- **📸 Bill Scanner** — Upload or capture bill photos; AI extracts Amount, Category, Date, Vendor
- **📊 Rich Dashboard** — Monthly/Weekly/Yearly charts, Category pie chart, Top vendors, Spending anomaly detection
- **💰 Expense History** — Filter, edit, and delete recorded expenses
- **🤖 AI Assistant** — Summarize spending, get saving recommendations, or free-form chat
- **🔐 Auth** — Secure JWT-based login/register

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install Python 3.11+
python --version

# Install Tesseract OCR (required for bill scanning)
brew install tesseract          # macOS
# sudo apt install tesseract-ocr  # Ubuntu/Debian
```

### 2. Clone & Setup

```bash
cd "Btech final project"

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your_key_here
```

> 🔑 Get a FREE Gemini API key at [aistudio.google.com](https://aistudio.google.com)
> The app works WITHOUT a key (fallback regex extraction), but AI features require it.

### 4. Start the Backend

```bash
# From the project root:
cd backend
uvicorn main:app --reload --port 8000
```

Backend will be live at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### 5. Start the Frontend

```bash
# Open a new terminal:
cd frontend
streamlit run app.py
```

Frontend will open at: http://localhost:8501

---

## 📁 Project Structure

```
Btech final project/
├── backend/
│   ├── main.py               # FastAPI app
│   ├── database.py           # SQLite setup
│   ├── models.py             # DB models  
│   ├── schemas.py            # Pydantic schemas
│   ├── routers/
│   │   ├── auth.py           # Login / Register
│   │   ├── expenses.py       # Bill upload + CRUD
│   │   ├── analytics.py      # Charts data APIs
│   │   └── ai_assistant.py   # AI endpoints
│   └── services/
│       ├── ocr_service.py    # Tesseract OCR
│       ├── extractor.py      # Gemini field extraction
│       └── ai_service.py     # AI summarize/chat
├── frontend/
│   └── app.py                # Streamlit dashboard
├── uploads/                  # Bill images stored here
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI + SQLite |
| OCR | Tesseract + Pillow |
| AI Extraction | Google Gemini |
| Frontend | Streamlit + Plotly |
| Auth | JWT (python-jose) |

---

## 📊 Dashboard Features

| Chart | Description |
|---|---|
| Monthly Bar Chart | Total spending per month |
| Weekly Line Chart | Last 12 weeks trend |
| Yearly Overview | Year-by-year comparison |
| Category Pie Chart | Spending breakdown by category |
| Top Merchants | Bar chart of top 10 vendors |
| Category Table | Full category-wise totals |
| 🔴 Anomaly Detection | Highlights months >150% of your average |

---

## 🐛 Troubleshooting

**Tesseract not found:**
```bash
brew install tesseract
# Then verify: tesseract --version
```

**Gemini API errors:**
- Check your `GEMINI_API_KEY` in `.env`
- Free tier has rate limits; wait a moment and retry

**Port already in use:**
```bash
uvicorn main:app --reload --port 8001
# Update API_URL in frontend/app.py to match
```
