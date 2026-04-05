import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load .env file from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

from .database import engine, Base
from .routers import auth, expenses, analytics, ai_assistant, group

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Bill Expense Tracker",
    description="Upload bills, auto-extract data with AI, and visualize your spending.",
    version="1.0.0",
)

# CORS — allow Streamlit frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(analytics.router)
app.include_router(ai_assistant.router)
app.include_router(group.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "AI Bill Expense Tracker API is running 🚀"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
