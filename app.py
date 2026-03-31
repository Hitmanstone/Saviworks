import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Saviworks", page_icon="💼", layout="centered")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if "user" not in st.session_state:
    st.session_state.user = None

def add_logo():
    st.markdown('<h1 style="text-align:center; color:#FF6B00; font-size:3.5rem; margin:40px 0 20px 0;">SAVIWORKS</h1>', unsafe_allow_html=True)

def show_landing():
    add_logo()
    st.markdown("<p style='text-align:center; font-size:1.6rem; color:#A0D8FF;'>Your portfolio in one place.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Sign Up", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        if st.button("Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

def show_signup():
    add_logo()
    st.subheader("Create Account")
    col = st.columns([1,2,1])[1]
    with col:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Create Account", type="primary"):
            if password != confirm:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Account created! You can now login.")
                    st.session_state.page = "login"
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        if st.button("← Back"):
            st.session_state.page = "landing"
            st.rerun()

def show_login():
    add_logo()
    st.subheader("Login")
    col = st.columns([1,2,1])[1]
    with col:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except:
                st.error("Invalid email or password")

        if st.button("← Back"):
            st.session_state.page = "landing"
            st.rerun()

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

    total_value = 0.0
    table_data = []

    if holdings:
        tickers = " ".join(h["ticker"] for h in holdings)
        batch = yf.Tickers(tickers)

        for h in holdings:
            t = batch.tickers[h["ticker"]]
            price = t.info.get("currentPrice") or t.info.get("regularMarketPrice", 0)

            value = price * h["quantity"]
            total_value += value

            table_data.append({
                "Ticker": h["ticker"],
                "Quantity": round(h["quantity"], 4),
                "Price": round(price, 4),
                "Value": round(value, 2)
            })

    st.metric("Total Portfolio Value", f"£{total_value:,.2f}")

    col1, col2 = st.columns(2)
    with col1:
        if table_data:
            fig = px.pie(names=[row["Ticker"] for row in table_data], values=[row["Value"] for row in table_data], title="Allocation")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add holdings to see allocation chart")

    with col2:
        dates = pd.date_range(end=datetime.today(), periods=30)
        values = [total_value * 0.9 + i*400 for i in range(30)]
        fig = go.Figure(go.Scatter(x=dates, y=values, fill='tozeroy', line=dict(color='#00BFFF')))
        fig.update_layout(title="Portfolio Trend", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Your Holdings")
    if table_data:
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.info("No holdings yet. Add your first one below.")

    st.subheader("Add New Holding")
    with st.form("add_form", clear_on_submit=True):
        ticker = st.text_input("Ticker Symbol", placeholder="BMNR, VUSA.L, AAPL")
        quantity = st.number_input("Quantity", min_value=0.0001, value=1.0, step=0.0001)
        cost_price = st.number_input("Cost Price per share (optional)", min_value=0.0, value=0.0)
        if st.form_submit_button("Add to Portfolio"):
            if ticker:
                try:
                    supabase.table("holdings").insert({
                        "user_id": st.session_state.user.id,
                        "ticker": ticker.upper().strip(),
                        "quantity": float(quantity),
                        "cost_price": float(cost_price) if cost_price > 0 else None
                    }).execute()
                    st.success(f"Added {ticker.upper()} successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if st.session_state.user is None:
    if "page" not in st.session_state or st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "signup":
        show_signup()
    elif st.session_state.page == "login":
        show_login()
else:
    show_dashboard()
