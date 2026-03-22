import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
from io import BytesIO

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_URL = "http://localhost:8000"
CATEGORIES = [
    "Food & Dining", "Groceries", "Transport", "Healthcare",
    "Utilities", "Shopping", "Entertainment", "Education", "Travel", "Other"
]

st.set_page_config(
    page_title="💳 SmartBill - AI Expense Tracker",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        min-height: 100vh;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.07);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #a78bfa;
        margin: 8px 0 4px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-icon {
        font-size: 1.8rem;
    }

    /* Section headers */
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 24px 0 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(167,139,250,0.4);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15,12,41,0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(124,58,237,0.4);
    }

    /* Input fields */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
        color: white !important;
    }

    /* Success/error alerts */
    .success-box {
        background: rgba(34,197,94,0.15);
        border: 1px solid rgba(34,197,94,0.4);
        border-radius: 12px;
        padding: 16px;
        color: #86efac;
    }

    .info-box {
        background: rgba(96,165,250,0.15);
        border: 1px solid rgba(96,165,250,0.4);
        border-radius: 12px;
        padding: 16px;
        color: #93c5fd;
    }

    /* Chat bubbles */
    .chat-user {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        border-radius: 16px 16px 4px 16px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        color: white;
    }
    .chat-ai {
        background: rgba(255,255,255,0.08);
        border-radius: 16px 16px 16px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 85%;
        border: 1px solid rgba(255,255,255,0.1);
        color: #e2e8f0;
    }

    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(124,58,237,0.3), rgba(79,70,229,0.3));
        border: 1px solid rgba(167,139,250,0.3);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        margin-bottom: 24px;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #a78bfa, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.7);
        font-size: 1.1rem;
    }

    /* Anomaly badge */
    .anomaly-badge {
        background: rgba(239,68,68,0.2);
        border: 1px solid rgba(239,68,68,0.5);
        border-radius: 8px;
        padding: 8px 12px;
        color: #fca5a5;
        font-size: 0.85rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        color: rgba(255,255,255,0.6);
    }
    .stTabs [aria-selected="true"] {
        color: #a78bfa !important;
        border-bottom-color: #a78bfa !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"


# ─────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────
def api_get(path, params=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.get(f"{API_URL}{path}", headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to backend. Make sure the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        return None


def api_post(path, json_data=None, files=None, data=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.post(
            f"{API_URL}{path}", headers=headers,
            json=json_data, files=files, data=data, timeout=60
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to backend. Make sure the FastAPI server is running on port 8000.")
        return None
    except Exception as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"Error: {detail}")
        return None


def api_put(path, json_data):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        r = requests.put(f"{API_URL}{path}", headers=headers, json=json_data, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


def api_delete(path):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        r = requests.delete(f"{API_URL}{path}", headers=headers, timeout=15)
        r.raise_for_status()
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────
CHART_COLORS = ["#a78bfa", "#818cf8", "#60a5fa", "#34d399", "#f472b6", "#fb923c", "#facc15", "#4ade80", "#f87171", "#94a3b8"]
LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#e2e8f0"),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0")),
)


def style_fig(fig):
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color="#94a3b8"))
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color="#94a3b8"))
    return fig


# ─────────────────────────────────────────────
# AUTH PAGES
# ─────────────────────────────────────────────
def show_auth():
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">💳 SmartBill</div>
        <div class="hero-subtitle">AI-Powered Expense Tracker — Click a Bill, Track Everything</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login →", use_container_width=True)
            if submitted:
                result = api_post("/auth/login", data={"username": email, "password": password})
                if result:
                    st.session_state.token = result["access_token"]
                    me = api_get("/auth/me")
                    if me:
                        st.session_state.user_name = me["name"]
                    st.success(f"Welcome back! 🎉")
                    st.rerun()

    with tab2:
        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="Your Name")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create Account →", use_container_width=True)
            if submitted:
                result = api_post("/auth/register", json_data={"email": email, "name": name, "password": password})
                if result:
                    st.session_state.token = result["access_token"]
                    st.session_state.user_name = name
                    st.success("Account created! Welcome aboard 🚀")
                    st.rerun()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 16px 0 24px;">
            <div style="font-size:2.5rem;">💳</div>
            <div style="font-size:1.3rem; font-weight:700; color:#a78bfa;">SmartBill</div>
            <div style="font-size:0.8rem; color:rgba(255,255,255,0.5);">AI Expense Tracker</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.user_name:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,0.15); border-radius:10px; padding:10px 14px; margin-bottom:16px;">
                <div style="font-size:0.75rem; color:rgba(255,255,255,0.5);">Logged in as</div>
                <div style="font-weight:600; color:#a78bfa;">👤 {st.session_state.user_name}</div>
            </div>
            """, unsafe_allow_html=True)

        pages = [
            ("🏠 Dashboard", "📊 Analytics"),
            ("📤 Upload Bill", "📸 Scan Bills"),
            ("📋 Expenses", "💰 History"),
            ("🤖 AI Assistant", "✨ Insights"),
        ]

        st.markdown('<div style="color:rgba(255,255,255,0.4); font-size:0.75rem; letter-spacing:2px; margin-bottom:8px;">NAVIGATION</div>', unsafe_allow_html=True)

        for page_name, page_desc in pages:
            is_active = st.session_state.page == page_name
            btn_style = "background: linear-gradient(135deg, #7c3aed, #4f46e5);" if is_active else ""
            if st.button(f"{page_name}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.page = page_name
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user_name = ""
            st.session_state.chat_history = []
            st.rerun()


# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard():
    st.markdown('<div class="section-title">📊 Dashboard Overview</div>', unsafe_allow_html=True)

    summary = api_get("/analytics/summary")
    if not summary:
        st.info("No expenses yet. Upload your first bill to see analytics! 📤")
        return

    # ── Metric Cards ──
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "💰", "Total Spent", f"₹{summary['total_spent']:,.0f}"),
        (c2, "📅", "This Month", f"₹{summary['this_month']:,.0f}"),
        (c3, "🏆", "Peak Month", f"{summary['max_month']} · ₹{summary['max_month_amount']:,.0f}"),
        (c4, "🛒", "Top Category", f"{summary['top_category']}"),
    ]
    for col, icon, label, val in metrics:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ── Row 2: Monthly Bar + Category Pie ──
    monthly_data = api_get("/analytics/monthly") or []
    category_data = api_get("/analytics/category") or []

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-title">📈 Monthly Spending</div>', unsafe_allow_html=True)
        if monthly_data:
            df_m = pd.DataFrame(monthly_data)
            fig = px.bar(
                df_m, x="month", y="total",
                color="total",
                color_continuous_scale=["#4f46e5", "#a78bfa", "#c4b5fd"],
                labels={"month": "Month", "total": "Amount (₹)"},
                title=""
            )
            fig.update_traces(marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("No monthly data yet.")

    with col_right:
        st.markdown('<div class="section-title">🥧 Category Breakdown</div>', unsafe_allow_html=True)
        if category_data:
            df_c = pd.DataFrame(category_data)
            fig = px.pie(
                df_c, values="total", names="category",
                color_discrete_sequence=CHART_COLORS,
                hole=0.45,
            )
            fig.update_traces(textinfo="label+percent", pull=[0.03]*len(df_c))
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("No category data yet.")

    # ── Row 3: Weekly Line + Yearly Bar ──
    weekly_data = api_get("/analytics/weekly") or []
    yearly_data = api_get("/analytics/yearly") or []

    col_wk, col_yr = st.columns(2)

    with col_wk:
        st.markdown('<div class="section-title">📉 Weekly Trend (Last 12 Weeks)</div>', unsafe_allow_html=True)
        if weekly_data:
            df_w = pd.DataFrame(weekly_data)
            fig = px.line(
                df_w, x="week", y="total",
                markers=True,
                line_shape="spline",
                color_discrete_sequence=["#a78bfa"],
                labels={"week": "Week", "total": "Amount (₹)"},
            )
            fig.update_traces(fill="tozeroy", fillcolor="rgba(167,139,250,0.15)", line_width=2.5)
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("Not enough data for weekly chart.")

    with col_yr:
        st.markdown('<div class="section-title">📆 Yearly Overview</div>', unsafe_allow_html=True)
        if yearly_data:
            df_y = pd.DataFrame(yearly_data)
            fig = px.bar(
                df_y, x="year", y="total",
                color_discrete_sequence=["#818cf8"],
                labels={"year": "Year", "total": "Amount (₹)"},
            )
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("No yearly data yet.")

    # ── Row 4: Top Vendors + Category Table ──
    vendor_data = api_get("/analytics/vendors") or []
    col_v, col_t = st.columns(2)

    with col_v:
        st.markdown('<div class="section-title">🏪 Top Merchants</div>', unsafe_allow_html=True)
        if vendor_data:
            df_v = pd.DataFrame(vendor_data)
            fig = px.bar(
                df_v.sort_values("total"), x="total", y="vendor",
                orientation="h",
                color="total",
                color_continuous_scale=["#4f46e5", "#a78bfa"],
                labels={"total": "Amount (₹)", "vendor": "Merchant"},
            )
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("No vendor data yet.")

    with col_t:
        st.markdown('<div class="section-title">📊 Category-wise Totals</div>', unsafe_allow_html=True)
        if category_data:
            df_cat = pd.DataFrame(category_data)
            df_cat["total"] = df_cat["total"].apply(lambda x: f"₹{x:,.2f}")
            df_cat.columns = ["Category", "Total Spent", "Transactions"]
            st.dataframe(df_cat, hide_index=True, use_container_width=True)
        else:
            st.info("No data yet.")

    # ── Spending Anomaly Detection ──
    if monthly_data and len(monthly_data) >= 3:
        df_m = pd.DataFrame(monthly_data)
        avg = df_m["total"].mean()
        anomalies = df_m[df_m["total"] > avg * 1.5]
        if not anomalies.empty:
            st.markdown('<div class="section-title">🔴 Spending Anomalies Detected</div>', unsafe_allow_html=True)
            for _, row in anomalies.iterrows():
                pct = ((row["total"] - avg) / avg) * 100
                st.markdown(f"""
                <div class="anomaly-badge">
                    ⚠️ <strong>{row['month']}</strong> — ₹{row['total']:,.0f} spent 
                    (<strong>+{pct:.0f}%</strong> above your average of ₹{avg:,.0f})
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE: UPLOAD BILL
# ─────────────────────────────────────────────
def page_upload():
    st.markdown('<div class="section-title">📸 Upload or Capture a Bill</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        🤖 Our AI will automatically extract <strong>Amount, Category, Date, Vendor</strong> from your bill.
        You can review and edit before saving.
    </div>
    """, unsafe_allow_html=True)

    tab_upload, tab_manual = st.tabs(["📁 Upload File / Camera", "✏️ Manual Entry"])

    with tab_upload:
        input_method = st.radio("Input Method", ["📁 Upload File", "📷 Camera"], horizontal=True)
        uploaded_file = None

        if input_method == "📁 Upload File":
            uploaded_file = st.file_uploader(
                "Drop your bill here",
                type=["jpg", "jpeg", "png", "pdf", "webp"],
                help="Supports JPG, PNG, PDF"
            )
        else:
            uploaded_file = st.camera_input("Take a photo of your bill")

        if uploaded_file:
            col_img, col_result = st.columns([1, 1])
            with col_img:
                st.image(uploaded_file, caption="Bill Preview", use_column_width=True)

            with col_result:
                with st.spinner("🔍 Extracting data with AI..."):
                    files = {"file": (uploaded_file.name or "bill.jpg", uploaded_file.getvalue(), uploaded_file.type or "image/jpeg")}
                    result = api_post("/expenses/upload", files=files)

                if result:
                    st.markdown('<div class="success-box">✅ Bill processed successfully!</div>', unsafe_allow_html=True)
                    st.markdown("**Review & Edit Extracted Fields:**")

                    with st.form("edit_extracted"):
                        amount = st.number_input("Amount (₹)", value=float(result.get("amount", 0)), min_value=0.0, step=0.5)
                        category = st.selectbox("Category", CATEGORIES,
                                                index=CATEGORIES.index(result.get("category", "Other")) if result.get("category") in CATEGORIES else 0)
                        vendor = st.text_input("Vendor / Merchant", value=result.get("vendor", ""))
                        exp_date = st.text_input("Date (YYYY-MM-DD)", value=result.get("date", date.today().isoformat()))
                        description = st.text_input("Description", value=result.get("description", ""))

                        save = st.form_submit_button("💾 Save Expense", use_container_width=True)
                        if save:
                            update = api_post("/expenses/manual", json_data={
                                "amount": amount, "category": category,
                                "vendor": vendor, "date": exp_date, "description": description,
                                "image_path": result.get("image_path")
                            })
                            if update:
                                st.success("✅ Expense saved!")

    with tab_manual:
        with st.form("manual_entry"):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount (₹)*", min_value=0.0, step=0.5)
                vendor = st.text_input("Vendor / Merchant*")
                exp_date = st.date_input("Date*", value=date.today())
            with col2:
                category = st.selectbox("Category*", CATEGORIES)
                description = st.text_input("Description", placeholder="Brief note about this expense")

            submitted = st.form_submit_button("➕ Add Expense", use_container_width=True)
            if submitted:
                if amount <= 0 or not vendor:
                    st.error("Please fill in Amount and Vendor.")
                else:
                    result = api_post("/expenses/manual", json_data={
                        "amount": amount, "category": category,
                        "vendor": vendor, "date": str(exp_date), "description": description
                    })
                    if result:
                        st.success(f"✅ Added ₹{amount:,.2f} from {vendor}!")


# ─────────────────────────────────────────────
# PAGE: EXPENSE HISTORY
# ─────────────────────────────────────────────
def page_expenses():
    st.markdown('<div class="section-title">💰 Expense History</div>', unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        start = st.date_input("From", value=date.today() - timedelta(days=30))
    with col2:
        end = st.date_input("To", value=date.today())
    with col3:
        cat_filter = st.selectbox("Category", ["All"] + CATEGORIES)

    params = {"start_date": str(start), "end_date": str(end)}
    if cat_filter != "All":
        params["category"] = cat_filter

    expenses = api_get("/expenses/", params=params) or []

    if not expenses:
        st.info("No expenses found for the selected filters.")
        return

    # Summary bar
    total = sum(e["amount"] for e in expenses)
    st.markdown(f"""
    <div style="background:rgba(167,139,250,0.15); border-radius:12px; padding:16px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
        <span>📋 <strong>{len(expenses)}</strong> transactions found</span>
        <span>💰 Total: <strong style="color:#a78bfa;">₹{total:,.2f}</strong></span>
    </div>
    """, unsafe_allow_html=True)

    # Table
    df = pd.DataFrame(expenses)
    df_display = df[["date", "vendor", "category", "amount", "description"]].copy()
    df_display["amount"] = df_display["amount"].apply(lambda x: f"₹{x:,.2f}")
    df_display.columns = ["Date", "Vendor", "Category", "Amount", "Description"]
    st.dataframe(df_display, hide_index=True, use_container_width=True)

    # Edit/Delete section
    st.markdown('<div class="section-title">✏️ Edit or Delete an Expense</div>', unsafe_allow_html=True)
    exp_ids = {f"#{e['id']} — {e['vendor']} ({e['date']}) ₹{e['amount']}": e for e in expenses}
    selected_label = st.selectbox("Select expense", list(exp_ids.keys()))

    if selected_label:
        selected = exp_ids[selected_label]

        col_edit, col_del = st.columns(2)
        with col_edit:
            with st.form("edit_expense"):
                new_amount = st.number_input("Amount (₹)", value=float(selected["amount"]))
                new_cat = st.selectbox("Category", CATEGORIES,
                                       index=CATEGORIES.index(selected["category"]) if selected["category"] in CATEGORIES else 0)
                new_vendor = st.text_input("Vendor", value=selected["vendor"])
                new_date = st.text_input("Date (YYYY-MM-DD)", value=selected["date"])
                new_desc = st.text_input("Description", value=selected.get("description", ""))
                if st.form_submit_button("💾 Update", use_container_width=True):
                    res = api_put(f"/expenses/{selected['id']}", {
                        "amount": new_amount, "category": new_cat,
                        "vendor": new_vendor, "date": new_date, "description": new_desc
                    })
                    if res:
                        st.success("Updated!")
                        st.rerun()

        with col_del:
            st.markdown("")
            st.markdown("")
            if st.button("🗑️ Delete this expense", use_container_width=True):
                if api_delete(f"/expenses/{selected['id']}"):
                    st.success("Deleted!")
                    st.rerun()


# ─────────────────────────────────────────────
# PAGE: AI ASSISTANT
# ─────────────────────────────────────────────
def page_ai():
    st.markdown('<div class="section-title">🤖 AI Financial Assistant</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        Ask me anything about your spending! I can summarize, recommend savings, and answer questions.
    </div>
    """, unsafe_allow_html=True)

    tab_sum, tab_rec, tab_chat = st.tabs(["📋 Summarize", "💡 Recommendations", "💬 Chat"])

    with tab_sum:
        days = st.slider("Summarize last N days", 7, 365, 30, step=7)
        if st.button("🔍 Generate Summary", use_container_width=True):
            with st.spinner("Analyzing your spending..."):
                result = api_get(f"/ai/summarize", params={"days": days})
            if result:
                st.markdown(f"""
                <div style="background:rgba(167,139,250,0.1); border:1px solid rgba(167,139,250,0.3); 
                     border-radius:12px; padding:20px; color:#e2e8f0; line-height:1.7;">
                    {result['summary']}
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"Based on {result['expense_count']} transactions over {result['days']} days")

    with tab_rec:
        if st.button("💡 Get Personalized Recommendations", use_container_width=True):
            with st.spinner("Generating recommendations..."):
                result = api_get("/ai/recommend")
            if result:
                st.markdown(f"""
                <div style="background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.3); 
                     border-radius:12px; padding:20px; color:#e2e8f0; line-height:1.8; white-space:pre-line;">
                    {result['recommendations']}
                </div>
                """, unsafe_allow_html=True)

    with tab_chat:
        # Display history
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; color:rgba(255,255,255,0.4); padding:32px;">
                👋 Ask me about your expenses!<br>
                <em>"How much did I spend on food this month?"</em><br>
                <em>"What was my biggest expense?"</em><br>
                <em>"Where am I overspending?"</em>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

        # Input
        user_input = st.chat_input("Ask about your expenses...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("Thinking..."):
                result = api_post("/ai/chat", json_data={
                    "message": user_input,
                    "history": st.session_state.chat_history[-10:]
                })
            if result:
                reply = result.get("reply", "Sorry, I couldn't process that.")
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()


# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
def main():
    if not st.session_state.token:
        show_auth()
        return

    show_sidebar()

    page = st.session_state.page
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📤 Upload Bill":
        page_upload()
    elif page == "📋 Expenses":
        page_expenses()
    elif page == "🤖 AI Assistant":
        page_ai()


if __name__ == "__main__":
    main()
