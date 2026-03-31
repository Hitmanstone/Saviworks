import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Page configuration
st.set_page_config(page_title="SAVIWORKS", page_icon="💼", layout="centered")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if "user" not in st.session_state:
    st.session_state.user = None

# Custom CSS - All capital letters, reasonable input width, gothic-style font
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Impact:wght@400;700&display=swap');

    * {
        font-family: 'Impact', 'Arial Black', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 1px;
    }

    .logo {
        font-size: 3.8rem;
        font-weight: 900;
        color: #FF6B00;
        text-align: center;
        margin-bottom: 20px;
        letter-spacing: 4px;
    }

    .input-box {
        max-width: 420px;
        margin: 0 auto;
    }

    .stTextInput > div > div > input {
        max-width: 420px !important;
        margin: 0 auto;
    }

    .stNumberInput > div {
        max-width: 420px !important;
        margin: 0 auto;
    }

    h1, h2, h3 {
        text-align: center;
    }

    .stButton > button {
        width: 100%;
        max-width: 420px;
        margin: 10px auto;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

def add_centered_logo():
    st.markdown('<div class="logo">SAVIWORKS</div>', unsafe_allow_html=True)

# ==================== LANDING PAGE ====================
def show_landing():
    add_centered_logo()
    st.markdown("<h1 style='text-align:center; color:white;'>SAVIWORKS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:1.6rem; color:#A0D8FF;'>YOUR PORTFOLIO IN ONE PLACE.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("SIGN UP", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        if st.button("LOGIN", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

# ==================== SIGN UP PAGE ====================
def show_signup():
    add_centered_logo()
    st.markdown("<h2>SIGN UP</h2>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="input-box">', unsafe_allow_html=True)
        email = st.text_input("EMAIL")
        password = st.text_input("PASSWORD", type="password")
        confirm = st.text_input("CONFIRM PASSWORD", type="password")
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← BACK"):
            st.session_state.page = "landing"
            st.rerun()
    with col2:
        if st.button("CREATE ACCOUNT", type="primary"):
            if password != confirm:
                st.error("PASSWORDS DO NOT MATCH")
            elif len(password) < 6:
                st.error("PASSWORD MUST BE AT LEAST 6 CHARACTERS")
            else:
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("ACCOUNT CREATED! YOU CAN NOW LOGIN.")
                    st.session_state.page = "login"
                    st.rerun()
                except Exception as e:
                    st.error(str(e).upper())

# ==================== LOGIN PAGE ====================
def show_login():
    add_centered_logo()
    st.markdown("<h2>LOGIN</h2>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="input-box">', unsafe_allow_html=True)
        email = st.text_input("EMAIL")
        password = st.text_input("PASSWORD", type="password")
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← BACK"):
            st.session_state.page = "landing"
            st.rerun()
    with col2:
        if st.button("LOGIN", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("LOGGED IN SUCCESSFULLY!")
                st.rerun()
            except Exception:
                st.error("INVALID EMAIL OR PASSWORD. PLEASE TRY AGAIN.")

# ==================== DASHBOARD ====================
def show_dashboard():
    add_centered_logo()
    st.title("MY PORTFOLIO")

    if st.button("LOGOUT"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    # Fetch holdings
    try:
        res = supabase.table("holdings").select("*").eq("user_id", st.session_state.user.id).execute()
        holdings = res.data
    except:
        holdings = []

    total_gbp = 0.0
    table_data = []
    pie_labels = []
    pie_values = []

    if holdings:
        tickers = " ".join(h["ticker"] for h in holdings)
        batch = yf.Tickers(tickers)
        fx_rate = yf.Ticker("GBPUSD=X").info.get("regularMarketPrice", 1.0)

        for h in holdings:
            t = batch.tickers[h["ticker"]]
            price = t.info.get("currentPrice") or t.info.get("regularMarketPrice", 0)
            currency = t.info.get("currency", "USD")

            value_native = price * h["quantity"]
            value_gbp = value_native if currency.upper() == "GBP" else value_native / fx_rate

            total_gbp += value_gbp
            pie_labels.append(h["ticker"])
            pie_values.append(value_gbp)

            table_data.append({
                "TICKER": h["ticker"],
                "QUANTITY": round(h["quantity"], 4),
                "PRICE NATIVE": round(price, 4),
                "VALUE GBP": round(value_gbp, 2)
            })

    st.metric("TOTAL PORTFOLIO VALUE", f"£{total_gbp:,.2f}")

    # Charts (empty state)
    col1, col2 = st.columns(2)
    with col1:
        if pie_values:
            fig = px.pie(names=pie_labels, values=pie_values, title="ALLOCATION")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ADD HOLDINGS TO SEE ALLOCATION CHART")

    with col2:
        dates = pd.date_range(end=datetime.today(), periods=30)
        values = [total_gbp * 0.9 + i * 400 for i in range(30)]
        fig = go.Figure(go.Scatter(x=dates, y=values, fill='tozeroy', line=dict(color='#00BFFF')))
        fig.update_layout(title="PORTFOLIO TREND", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Holdings Table
    st.subheader("YOUR HOLDINGS")
    if table_data:
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.info("NO HOLDINGS YET. ADD YOUR FIRST ONE BELOW.")

    # Inline Add Form
    st.subheader("ADD NEW HOLDING")
    with st.form("add_form", clear_on_submit=True):
        ticker = st.text_input("TICKER SYMBOL", placeholder="BMNR, VUSA.L, AAPL")
        quantity = st.number_input("QUANTITY", min_value=0.0001, value=1.0, step=0.0001)
        cost_price = st.number_input("COST PRICE PER SHARE (OPTIONAL)", min_value=0.0, value=0.0)
        if st.form_submit_button("ADD TO PORTFOLIO"):
            if ticker:
                try:
                    supabase.table("holdings").insert({
                        "user_id": st.session_state.user.id,
                        "ticker": ticker.upper().strip(),
                        "quantity": float(quantity),
                        "cost_price": float(cost_price) if cost_price > 0 else None
                    }).execute()
                    st.success(f"ADDED {ticker.upper()} SUCCESSFULLY!")
                    st.rerun()
                except Exception as e:
                    st.error(f"ERROR ADDING HOLDING: {str(e).upper()}")

# ==================== MAIN FLOW ====================
if st.session_state.user is None:
    if "page" not in st.session_state or st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "signup":
        show_signup()
    elif st.session_state.page == "login":
        show_login()
else:
    show_dashboard()
