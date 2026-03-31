import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saviworks", page_icon="💼", layout="wide")

# ------------------- Supabase -------------------
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None
if "portfolio_name" not in st.session_state:
    st.session_state.portfolio_name = "My Portfolio"

# ------------------- Custom Styling -------------------
st.markdown("""
<style>
    .logo { color: #FF6B00; font-size: 2rem; font-weight: 900; }
    .big-title { font-size: 4rem; font-weight: 700; text-align: center; color: #FFFFFF; }
    .subtitle { font-size: 1.6rem; text-align: center; color: #A0D8FF; }
</style>
""", unsafe_allow_html=True)

def add_logo():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown('<span class="logo">SAVIWORKS</span>', unsafe_allow_html=True)

# ------------------- Landing Page -------------------
def show_landing():
    add_logo()
    st.markdown('<div class="big-title">Saviworks</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your portfolio in one place.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.button("Sign Up", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        if st.button("Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

# ------------------- Login & Signup (with back buttons) -------------------
def show_login():
    add_logo()
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()
    if st.button("Login", type="primary"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.success("Logged in successfully!")
            st.rerun()
        except:
            st.error("Invalid credentials")

def show_signup():
    add_logo()
    st.title("Create Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    if st.button("← Back"):
        st.session_state.page = "landing"
        st.rerun()
    if st.button("Create Account", type="primary"):
        if password != confirm:
            st.error("Passwords do not match")
        else:
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Account created! Check your email for the confirmation link.")
                st.session_state.page = "login"
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ------------------- Main Dashboard -------------------
def show_dashboard():
    add_logo()
    st.title(st.session_state.portfolio_name)

    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    # Fetch holdings
    try:
        res = supabase.table("holdings").select("*").eq("user_id", st.session_state.user.id).execute()
        holdings = res.data
    except:
        holdings = []

    # Live data fetch
    if holdings:
        tickers = " ".join([h["ticker"] for h in holdings])
        batch = yf.Tickers(tickers)
        fx = yf.Ticker("GBPUSD=X").info.get("regularMarketPrice", 1.0)

        total_gbp = 0
        rows = []
        values_for_pie = []

        for h in holdings:
            t = batch.tickers[h["ticker"]]
            price = t.info.get("currentPrice") or t.info.get("regularMarketPrice", 0)
            currency = t.info.get("currency", "USD")

            value_native = price * h["quantity"]
            value_gbp = value_native if currency.upper() == "GBP" else value_native / fx

            total_gbp += value_gbp
            values_for_pie.append(value_gbp)

            rows.append({
                "Ticker": h["ticker"],
                "Quantity": h["quantity"],
                "Price Native": round(price, 4),
                "Value Native": round(value_native, 2),
                "Value GBP": round(value_gbp, 2)
            })

        df = pd.DataFrame(rows)

        # Top metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Value", f"£{total_gbp:,.2f}", "↑ £1,234.56 (+0.97%)")  # placeholder change

        with col2:
            if st.button("+ Add Holding"):
                st.session_state.show_add_form = True

        # Tabs
        tab1, tab2 = st.tabs(["Overview", "Holdings"])

        with tab1:
            # Mountain Chart (simulated)
            dates = pd.date_range(end=datetime.today(), periods=30)
            values = [total_gbp * 0.85 + i*800 for i in range(30)]
            fig = go.Figure(go.Scatter(x=dates, y=values, fill='tozeroy', line=dict(color='#00BFFF')))
            fig.update_layout(template="plotly_dark", title="Portfolio Value Trend")
            st.plotly_chart(fig, use_container_width=True)

            # Pie Chart
            if values_for_pie:
                pie_fig = px.pie(names=[h["Ticker"] for h in holdings], values=values_for_pie, template="plotly_dark")
                st.plotly_chart(pie_fig, use_container_width=True)

        with tab2:
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No holdings yet. Add some above!")

    else:
        st.info("You have no holdings yet. Click '+ Add Holding' to get started.")

    # Add Holding Form
    if st.session_state.get("show_add_form", False):
        with st.form("add_holding"):
            st.subheader("Add New Holding")
            ticker = st.text_input("Ticker (e.g. BMNR, VUSA.L, BTC-USD)")
            quantity = st.number_input("Quantity", min_value=0.0001, step=0.0001)
            cost_price = st.number_input("Cost Price (optional)", min_value=0.0, step=0.01)
            submitted = st.form_submit_button("Add Holding")
            if submitted and ticker:
                supabase.table("holdings").insert({
                    "user_id": st.session_state.user.id,
                    "ticker": ticker.upper(),
                    "quantity": quantity,
                    "cost_price": cost_price
                }).execute()
                st.success("Holding added!")
                st.session_state.show_add_form = False
                st.rerun()

# ------------------- Main App Flow -------------------
if st.session_state.user is None:
    if "page" not in st.session_state:
        show_landing()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "signup":
        show_signup()
else:
    show_dashboard()
