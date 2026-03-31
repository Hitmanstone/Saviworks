import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Saviworks", page_icon="💼", layout="centered")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if "user" not in st.session_state:
    st.session_state.user = None

def add_logo():
    st.markdown('<h1 style="text-align:center; color:#FF6B00; font-size:3.2rem; margin:40px 0 20px 0;">SAVIWORKS</h1>', unsafe_allow_html=True)

def show_landing():
    add_logo()
    st.markdown("<p style='text-align:center; font-size:1.5rem; color:#A0D8FF;'>Your portfolio in one place.</p>", unsafe_allow_html=True)

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
            else:
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("Account created! Login now.")
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

    st.subheader("Add New Holding - Test")
    with st.form("test_form"):
        ticker = st.text_input("Ticker", placeholder="BMNR")
        quantity = st.number_input("Quantity", min_value=0.1, value=10.0)
        if st.form_submit_button("Add Holding"):
            if ticker:
                try:
                    result = supabase.table("holdings").insert({
                        "user_id": st.session_state.user.id,
                        "ticker": ticker.upper().strip(),
                        "quantity": float(quantity)
                    }).execute()
                    st.success("Holding added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Insert failed: {str(e)}")

    st.info("If you can add a holding here, RLS is the issue. If not, table setup is wrong.")

if st.session_state.user is None:
    if "page" not in st.session_state or st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "signup":
        show_signup()
    elif st.session_state.page == "login":
        show_login()
else:
    show_dashboard()
