import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import json
from supabase import create_client, Client

# Page config - Apple-like clean look
st.set_page_config(page_title="Saviworks", page_icon="💼", layout="wide")

# ------------------- Supabase Connection -------------------
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# ------------------- Session State -------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "portfolio_name" not in st.session_state:
    st.session_state.portfolio_name = "My Portfolio"

# ------------------- Landing Page -------------------
def show_landing():
    st.markdown("""
    <style>
    .big-title {font-size: 4.5rem; font-weight: 700; text-align: center; margin-top: 100px; color: #FFFFFF;}
    .subtitle {font-size: 1.8rem; text-align: center; color: #A0D8FF; margin-bottom: 60px;}
    .btn {padding: 15px 40px; font-size: 1.3rem; border-radius: 50px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="big-title">Saviworks</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your portfolio in one place.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Sign Up", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        if st.button("Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

# ------------------- Auth Pages -------------------
def show_login():
    st.title("Login to Saviworks")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error("Invalid email or password")

def show_signup():
    st.title("Create your Saviworks account")
    email = st.text_input("Email")
    password = st.text_input("Password (min 6 characters)", type="password")
    if st.button("Sign Up"):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.success("Account created! Please check your email to confirm (if required). You can now login.")
            st.session_state.page = "login"
            st.rerun()
        except Exception as e:
            st.error(str(e))

# ------------------- Main Dashboard (Snowball-style) -------------------
def show_dashboard():
    st.title(st.session_state.portfolio_name)

    # Top metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Value", "£124,567.89", "£2,345.67 (+1.92%)")  # Placeholder - will be dynamic

    # Tabs like Snowball
    tab1, tab2, tab3 = st.tabs(["Overview", "Holdings", "Performance"])

    with tab1:  # Overview - Mountain + Pie
        st.subheader("Portfolio Performance")
        # Dummy mountain chart (we'll make it dynamic later)
        dates = pd.date_range(end=datetime.today(), periods=30).tolist()
        values = [100000 + i*500 + (i**2)*10 for i in range(30)]
        fig = go.Figure(go.Scatter(x=dates, y=values, mode='lines', fill='tozeroy', line=dict(color='#00BFFF')))
        fig.update_layout(template="plotly_dark", height=400, title="Portfolio Value Over Time")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Allocation")
        # Dummy pie
        pie_fig = px.pie(values=[40, 30, 20, 10], names=["Stocks", "Crypto", "ETFs", "Cash"], template="plotly_dark")
        st.plotly_chart(pie_fig, use_container_width=True)

    with tab2:  # Holdings
        st.subheader("Your Holdings")
        # Add holding button (placeholder for now)
        if st.button("+ Add Holding"):
            st.info("Add holding form coming in next update")

        # Example table
        data = pd.DataFrame({
            "Ticker": ["BMNR", "VUSA.L"],
            "Quantity": [500, 120],
            "Price (native)": ["$1.23", "£85.45"],
            "Value (GBP)": ["£487", "£10,254"]
        })
        st.dataframe(data, use_container_width=True, hide_index=True)

    with tab3:
        st.write("Detailed performance charts coming soon.")

    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# ------------------- Main App Logic -------------------
if st.session_state.user is None:
    if "page" not in st.session_state:
        show_landing()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "signup":
        show_signup()
else:
    show_dashboard()