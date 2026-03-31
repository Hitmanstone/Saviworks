import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saviworks", page_icon="💼", layout="wide")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if "user" not in st.session_state:
    st.session_state.user = None

def add_logo():
    st.markdown('<span style="color:#FF6B00; font-size:2.3rem; font-weight:900;">SAVIWORKS</span>', unsafe_allow_html=True)

# ==================== LOGIN & SIGNUP ====================
def show_login():
    add_logo()
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error("Login failed. Please check your email and password.")

def show_signup():
    add_logo()
    st.title("Create Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    if st.button("Create Account", type="primary"):
        if password != confirm:
            st.error("Passwords do not match")
        else:
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Account created! You can now login.")
                st.session_state.page = "login"
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ==================== DASHBOARD ====================
def show_dashboard():
    add_logo()
    st.title("My Portfolio")

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

    # Live data + calculations
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
                "Ticker": h["ticker"],
                "Quantity": round(h["quantity"], 4),
                "Price Native": round(price, 4),
                "Value GBP": round(value_gbp, 2)
            })

    # Top total
    st.metric("Total Portfolio Value", f"£{total_gbp:,.2f}")

    # Charts (empty when no holdings)
    col1, col2 = st.columns(2)
    with col1:
        if pie_values:
            fig = px.pie(names=pie_labels, values=pie_values, title="Allocation")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add holdings to see allocation pie chart")

    with col2:
        dates = pd.date_range(end=datetime.today(), periods=30)
        values = [total_gbp * 0.9 + i*300 for i in range(30)]
        fig = go.Figure(go.Scatter(x=dates, y=values, fill='tozeroy', line=dict(color='#00BFFF')))
        fig.update_layout(title="Portfolio Trend (simulated)", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    # Holdings Table
    st.subheader("Holdings")
    if table_data:
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.info("No holdings yet. Add some below.")

    # Inline Add Holding Form
    st.subheader("Add New Holding")
    with st.form("add_form"):
        ticker = st.text_input("Ticker Symbol (e.g. BMNR, VUSA.L, AAPL)")
        quantity = st.number_input("Quantity", min_value=0.0001, value=1.0, step=0.0001)
        cost_price = st.number_input("Cost Price per share (optional)", min_value=0.0, value=0.0)
        submitted = st.form_submit_button("Add to Portfolio")
        if submitted and ticker:
            try:
                supabase.table("holdings").insert({
                    "user_id": st.session_state.user.id,
                    "ticker": ticker.upper().strip(),
                    "quantity": float(quantity),
                    "cost_price": float(cost_price)
                }).execute()
                st.success(f"✅ Added {ticker.upper()}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding holding: {str(e)}")

# ==================== MAIN FLOW ====================
if st.session_state.user is None:
    if "page" not in st.session_state or st.session_state.page in ["landing", "login"]:
        show_login()   # Go straight to login for simplicity
    elif st.session_state.page == "signup":
        show_signup()
else:
    show_dashboard()
