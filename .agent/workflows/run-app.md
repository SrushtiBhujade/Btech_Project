---
description: Run the SmartBill application (Backend + Frontend)
---

This workflow will start both the FastAPI backend and the Streamlit frontend.

### Prerequisites
- Ensure you have installed the dependencies: `pip install -r requirements.txt`
- Ensure you have a `.env` file with your `GEMINI_API_KEY` (optional but recommended).

### Steps

1. Start the Backend (FastAPI)
// turbo
```bash
./venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

2. Start the Frontend (Streamlit)
// turbo
```bash
cd frontend && streamlit run app.py
```
