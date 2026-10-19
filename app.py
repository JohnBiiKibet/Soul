import streamlit as st
import random
import pandas as pd
from supabase import create_client, Client

# --- 1. INITIALIZE DATABASE SECRETS ENVIRONMENT ---
# Pulling credentials securely from deployment settings
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# Single-point initialization function
@st.cache_resource
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# --- 2. GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    page_title="soul - Cloud Connected Chat & Ledger",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. SESSION STATE MANAGEMENT (Localized Chat Cache Only) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"sender": "System", "type": "text", "content": "Welcome to soul! Your session is connected to a secure cloud-backed database ledger."}
    ]

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

# --- 4. HARDCODED BOT DATING LINE ENGINE ---
DATING_LINES_DATABASE = {
    "Witty & Playful": [
        "Are you a software update? Because whenever I look at you, my whole system pauses.",
        "Are we a high-speed network connection? Because I'm feeling an instant link here.",
        "I'm usually better at writing code than opening lines, but you completely broke my logic loop."
    ],
    "Confident & Direct": [
        "Let's skip the small talk—what's your favorite spot in the city for coffee?",
        "I was having a completely productive day until I crossed paths with your profile.",
        "My calendar has a critical slot opening up this Friday night. I highly recommend you fill it."
    ],
    "Sweet & Charming": [
        "Excuse me, but I think you dropped something... my jaw, specifically.",
        "Is it bright in here, or is it just the smile radiating from your profile photos?",
        "I didn't believe in perfect matches until I saw your contact card pull up."
    ]
}

def generate_dating_line(style, profile):
    base_lines = DATING_LINES_DATABASE.get(style, DATING_LINES_DATABASE["Witty & Playful"])
    selected_line = random.choice(base_lines)
    if profile and profile.get("name"):
        first_name = profile["name"].split()[0]
        if random.choice([True, False]):
            selected_line = f"Hey {first_name}! {selected_line}"
    return selected_line

# --- 5. DATA INGESTION & REPORT GENERATION UTILITIES ---
def fetch_users_from_db():
    """Queries live rows from the permanent Supabase database schema."""
    if not supabase:
        return []
    try:
        response = supabase.table("user_registry").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Database Read Error: {e}")
        return []

def compile_registry_report(user_list):
    """Compiles a clean markdown analytical table from live database records."""
    total_users = len(user_list)
    premium_users = len([u for u in user_list if u.get('paid')])
    conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0.0
    
    report_lines = [
        "# SOUL APPLICATION - LIVE SYSTEM REGISTRY REPORT",
        "## Core User Footprint & Revenue Telemetry Metrics\n",
        f"- **Total Registered Cloud Accounts**: {total_users}",
        f"- **Premium Conversion Ratio**: {conversion_rate:.1f}%\n",
        "---|---|---|---|---",
        "Full Name | Email Address | Phone Number | Premium Paid | Location Coordinates",
        "---|---|---|---|---"
    ]
    for u in user_list:
        report_lines.append(f"{u.get('name')} | {u.get('email')} | {u.get('phone')} | {'✅ Yes' if u.get('paid') else '❌ No'} | {u.get('location')}")
    
    return "\n".join(report_lines)

# Fetch current records from database upfront
live_user_data = fetch_users_from_db()

# --- 6. SIDEBAR VIEWPORT: PROFILE & AUTHENTICATION REGISTRY ---
with st.sidebar:
    st.title("soul 💬❤️")
    st.caption("Live Cloud Registration Node & Payment Portal")
    
    if not supabase:
        st.warning("⚠️ Database connection parameters missing. Provide credentials in Secrets settings.")

    with st.form("sidebar_profile_form"):
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email Address", placeholder="john@example.com")
        phone = st.text_input("Phone Number", placeholder="+254 700 000000")
        is_paid = st.checkbox("Pay for Service Premium Tier (Unlocks Location Logs)", value=False)
        
        submit_profile = st.form_submit_button("Register & Sync to Cloud")
        
        if submit_profile:
            if name and email:
                resolved_loc = "Berlin, Germany" if is_paid else "[Redacted - Upgrade to Premium]"
                
                payload = {
                    "name": name,
                    "email": email,
                    "phone": phone if phone else "Not provided",
                    "paid": is_paid,
                    "location": resolved_loc
                }
                
                if supabase:
                    try:
                        # Direct database mutation injection loop
                        supabase.table("user_registry").insert(payload).execute()
                        st.session_state.user_profile = payload
                        st.success("Successfully synchronized to cloud database!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to push data: {e}")
                else:
                    st.session_state.user_profile = payload
                    st.info("Cached locally (Offline Mode).")
            else:
                st.error("Name and Email are mandatory fields.")

    if st.session_state.user_profile:
        st.write("---")
        st.markdown("### 📇 Configured Profile Card")
        prof = st.session_state.user_profile
        st.markdown(f"""
            <div style="background-color: #f8fafc; border: 2px solid #6366f1; border-radius: 12px; padding: 14px; margin-bottom: 8px;">
                <b style="color: #1e293b; font-size: 15px;">{prof['name']}</b> ({'Premium Tier' if prof['paid'] else 'Free Tier'})<br>
                <hr style="margin: 6px 0; border-color: #e2e8f0;">
                <span style="font-size: 12px; color: #64748b;">📧 {prof['email']}</span><br>
                <span style="font-size: 12px; color: #64748b;">📞 {prof['phone']}</span><br>
                <span style="font-size: 12px; color: #4f46e5;">📍 {prof['location']}</span>
            </div>
        """, unsafe_with_html=True)
        
        if st.button("Drop Card Into Chat Feed", use_container_width=True):
            st.session_state.chat_history.append({"sender": "You", "type": "contact_card", "content": prof})
            st.rerun()

# --- 7. MAIN INTERFACE VIEWPORTS (Workspace Layout) ---
tab_chat, tab_admin = st.tabs(["💬 Core Chatroom Feed", "📊 Executive Admin Records & Reporting"])

# ==================== TAB 1: LIVE CHAT SPACE ====================
with tab_chat:
    col_chat_feed, col_bot_panel = st.columns([1.8, 1.2], gap="medium")
    
    with col_chat_feed:
        chat_container = st.container(height=420)
        with chat_container:
            for message in st.session_state.chat_history:
                if message["sender"] == "You":
                    if message["type"] == "contact_card":
                        card = message["content"]
                        st.markdown(f"""
                            <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                                <div style="background-color: #ffffff; border: 2px solid #4f46e5; border-radius: 12px; padding: 12px; max-width: 280px; width: 100%; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                                    <h4 style="margin: 0; font-size: 13px; color: #111827;">📇 {card['name']}</h4>
                                    <div style="margin-top: 6px; font-size: 11px; color: #4b5563; line-height: 1.4;">
                                        <b>Email:</b> {card['email']}<br>
                                        <b>Phone:</b> {card['phone']}<br>
                                        <b>Location:</b> {card['location']}
                                    </div>
                                </div>
                            </div>
                        """, unsafe_with_html=True)
                    else:
                        st.chat_message("user").write(message["content"])
                elif message["sender"] == "System":
                    st.caption(f"🤖 {message['content']}")
                else:
                    st.chat_message("assistant").write(message["content"])

        if user_text := st.chat_input("Type a message or insert your customized dating line icebreaker..."):
            st.session_state.chat_history.append({"sender": "You", "type": "text", "content": user_text})
            st.rerun()

    with col_bot_panel:
        st.subheader("🤖 AI Line Recommendation")
        style_choice = st.selectbox("Line Persona Mood:", ["Witty & Playful", "Confident & Direct", "Sweet & Charming"])
        
        if "current_suggestion" not in st.session_state:
            st.session_state.current_suggestion = ""
            
        if st.button("Generate Icebreaker Line ✨", use_container_width=True, type="primary"):
            st.session_state.current_suggestion = generate_dating_line(style_choice, st.session_state.user_profile)
            
        if st.session_state.current_suggestion:
            st.info(f"\"{st.session_state.current_suggestion}\"")
            if st.button("Send Directly to Chat 🚀", use_container_width=True):
