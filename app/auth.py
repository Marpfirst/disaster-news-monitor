"""
Simple authentication system untuk Streamlit
"""

import streamlit as st
import json
import os
from pathlib import Path
import hashlib


class SimpleAuth:
    """Simple password-based authentication"""
    
    def __init__(self, users_file="data/users.json"):
        self.users_file = users_file
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users file if not exists"""
        if not os.path.exists(self.users_file):
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            
            # Default user: admin / admin123
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123"),
                    "role": "admin"
                }
            }
            
            with open(self.users_file, "w") as f:
                json.dump(default_users, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self) -> dict:
        """Load users from file"""
        try:
            with open(self.users_file, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading users: {e}")
            return {}
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verify username and password
        
        Returns:
            True if credentials valid
        """
        users = self._load_users()
        
        if username not in users:
            return False
        
        password_hash = self._hash_password(password)
        return users[username]["password_hash"] == password_hash
    
    def get_user_role(self, username: str) -> str:
        """Get user role"""
        users = self._load_users()
        return users.get(username, {}).get("role", "viewer")
    
    def login_form(self):
        """
        Display login form and handle authentication
        
        Returns:
            True if logged in
        """
        # Check if already logged in
        if st.session_state.get("authenticated", False):
            return True
        
        # Show login form
        st.title("🔐 Login")
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", width='stretch')
            
            if submit:
                if self.verify_credentials(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = self.get_user_role(username)
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        
        # Info box
        st.info("**Default credentials:**\n\nUsername: `admin`\n\nPassword: `admin123`")
        
        return False
    
    def logout(self):
        """Logout current user"""
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.rerun()
    
    @staticmethod
    def require_auth(func):
        """Decorator to require authentication"""
        def wrapper(*args, **kwargs):
            if not st.session_state.get("authenticated", False):
                st.warning("Please login to access this page")
                st.stop()
            return func(*args, **kwargs)
        return wrapper


def show_user_info():
    """Show current user info in sidebar"""
    if st.session_state.get("authenticated", False):
        username = st.session_state.get("username", "Unknown")
        role = st.session_state.get("role", "viewer")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 User:** {username}")
        st.sidebar.markdown(f"**🎭 Role:** {role.title()}")