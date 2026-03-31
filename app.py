import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saviworks", page_icon="💼", layout="wide")

# Supabase
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if "user" not in st.session_state:
    st.session_state.user = None

def add_logo():
    st.markdown('<span style="color:#FF6B00; font-size:2.2rem; font-weight:900;">SAVIWORKS</span>', unsafe_allow_html=True)

# ==================== LANDING PAGE ====================
def show_landing():
    add_logo()
    st.markdown("<h1 style='text-align:center; color:white; margin-top:80px;'>Saviworks</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:1.8rem; color:#A0D8FF;'>Your portfolio in one place.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Sign Up", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        if st.button("Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

# ==================== LOGIN & SIGNUP ====================
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
            st.error("Invalid email or password")

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
                st.success("Account created! Please check your email for confirmation link.")
                st.session_state.page = "login"
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ==================== FULL DASHBOARD ====================
def show_dashboard():
    add_logo()
    st.title("My Portfolio")

    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    # Fetch user's holdings
    try:
        response = supabase.table("holdings").select("*").eq("user_id", st.session_state.user.id).execute()
        holdings = response.data
    except:
        holdings = []

    if not holdings:
        st.info("You have no holdings yet. Click '+ Add Holding' below to get started.")
    else:
        # Live data from Yahoo Finance
        tickers_str = " ".join([h["ticker"] for h in holdings])
        batch = yf.Tickers(tickers_str)
        fx_rate = yf.Ticker("GBPUSD=X").info.get("regularMarketPrice", 1.0)

        total_gbp = 0
        table_data = []
        pie_values = []
        pie_labels = []

        for h in holdings:
            ticker_info = batch.tickers[h["ticker"]]
            price = ticker_info.info.get("currentPrice") or ticker_info.info.get("regularMarketPrice", 0)
            currency = ticker_info.info.get("currency", "USD")

            value_native = price * h["quantity"]
            value_gbp = value_native if currency.upper() == "GBP" else (value_native / fx_rate)

            total_gbp += value_gbp
            pie_values.append(value_gbp)
            pie_labels.append(h["ticker"])

            table_data.append({
                "Ticker": h["ticker"],
                "Quantity": round(h["quantity"], 4),
                "Price (native)": round(price, 4),
                "Value (GBP)": round(value_gbp, 2)
            })

        df = pd.DataFrame(table_data)

        # Top metrics
        st.metric(label="Total Portfolio Value", value=f"£{total_gbp:,.2f}")

        # Pie Chart
        fig_pie = px.pie(names=pie_labels, values=pie_values, title="Portfolio Allocation")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Holdings Table
        st.subheader("Your Holdings")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Add Holding Button & Form
    if st.button("+ Add Holding"):
        st.session_state.show_form = True

    if st.session_state.get("show_form", False):
        with st.form("add_holding_form"):
            st.subheader("Add New Holding")
            ticker = st.text_input("Ticker Symbol (e.g. BMNR, VUSA.L, AAPL)")
            quantity = st.number_input("Quantity", min_value=0.0001, value=1.0, step=0.0001)
            cost = st.number_input("Cost Price per share (optional)", min_value=0.0, value=0.0, step=0.01)
            submitted = st.form_submit_button("Add to Portfolio")
            if submitted and ticker:
                supabase.table("holdings").insert({
                    "user_id": st.session_state.user.id,
                    "ticker": ticker.upper().strip(),
                    "quantity": quantity,
                    "cost_price": cost
                }).execute()
                st.success(f"Added {ticker.upper()} successfully!")
                st.session_state.show_form = False
                st.rerun()

# ==================== MAIN APP LOGIC ====================
if st.session_state.user is None:
    if "page" not in st.session_state or st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "signup":
        show_signup()
else:
    show_dashboard()
