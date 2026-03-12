import streamlit as st
import dashboard
import about
import data_processing
import visualization


# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Crypto Volatility & Risk Analyzer")

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "Data Acquisition"


# ---------------- LOGIN PAGE ----------------
def login_page():
    st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #141E30, #243B55);
    }
    </style>
    """,
    unsafe_allow_html=True
)

    st.title("🔐 Login - Crypto Volatility & Risk Analyzer")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid Credentials")


# ---------------- NAVIGATION MENU ----------------
def navigation_menu():
    st.sidebar.title("📌 Navigation")

    page = st.sidebar.radio(
        "Go to",
        [
            "Data Acquisition",
            "Data Processing",
            "Visualization",
            "Advanced Analytics",
            "About"
        ]
    )

    st.session_state.page = page

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


# ---------------- MAIN LOGIC ----------------
if not st.session_state.logged_in:
    login_page()
else:
    navigation_menu()

    if st.session_state.page == "Data Acquisition":
        dashboard.show_dashboard()

    elif st.session_state.page == "Data Processing":
        data_processing.show_milestone2()  # rename function later if you want

    elif st.session_state.page == "Visualization":
        visualization.show_milestone3()

    elif st.session_state.page == "Advanced Analytics":
        st.title("🚀 Advanced Analytics")
        st.info("This section is under development.")

    elif st.session_state.page == "About":
        about.show_about()