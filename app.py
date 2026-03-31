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
    st.markdown('<span style="color:#FF6B00; font-size:2rem; font-weight:900;">SAVIWORKS</span>', unsafe_allow_html=True)

def show_landing():
    add_logo()
    st.markdown('<h1 style="text-align:center; color:white;">Saviworks</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; font-size:1.6rem; color:#A0D8FF;">Your portfolio in one place.</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.button("Sign Up", type="primary", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        if st.button("Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

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
            st.success("Login successful!")
            st.rerun()
        except Exception as e:
            st.error("Invalid email or password. Make sure your email is confirmed.")

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
                st.success("Account created! Check your email and click the confirmation link.")
                st.session_state.page = "login"
                st.rerun()
            except Exception as e:
                st.error(str(e))

# Dashboard (simplified for now)
def show_dashboard():
    add_logo()
    st.title("My Portfolio")

    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.info("You have no holdings yet. The full holdings + live charts + add form will be added in the next update once login is stable.")

# Main flow
if st.session_state.user is None:
    if "page" not in st.session_state or st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "signup":
        show_signup()
else:
    show_dashboard()
