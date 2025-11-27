"""
Main Streamlit Application
Disaster News Monitoring System
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.auth import SimpleAuth, show_user_info
from database.db_manager import CSVDatabase
from app.ui.dashboard import show_dashboard
from app.ui.verification import show_verification_page
from app.ui.settings import show_settings_page


# Page config
st.set_page_config(
    page_title="Disaster News Monitor",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"


def main():
    """Main application function"""
    
    # Initialize
    init_session_state()
    auth = SimpleAuth()
    db = CSVDatabase()
    
    # Check authentication
    if not auth.login_form():
        return
    
    # Sidebar navigation
    st.sidebar.title("🚨 Disaster Monitor")
    st.sidebar.markdown("---")
    
    # Navigation menu
    pages = {
        "📊 Dashboard": "dashboard",
        "✅ Verifikasi Artikel": "verification",
        "⚙️ Settings": "settings"
    }
    
    page = st.sidebar.radio(
        "Navigation",
        list(pages.keys()),
        key="navigation"
    )
    
    st.session_state["current_page"] = pages[page]
    
    # User info
    show_user_info()
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", width='stretch'):
        auth.logout()
    
    # Main content area
    if st.session_state["current_page"] == "dashboard":
        show_dashboard(db)
    elif st.session_state["current_page"] == "verification":
        show_verification_page(db)
    elif st.session_state["current_page"] == "settings":
        show_settings_page(db)


if __name__ == "__main__":
    main()