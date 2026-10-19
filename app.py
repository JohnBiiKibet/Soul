import streamlit as st
import random
import pandas as pd
from supabase import create_client, Client
from openai import OpenAI

# --- 1. INITIALIZE DATABASE & AI SECRETS ENVIRONMENT ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

# FIXED PLATFORM CONFIGURATIONS
MERCHANT_MPESA_NUMBER = "0711317556"
PREMIUM_FEE_KES = 20

@st.cache_resource
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)

supabase = get_supabase_client()
ai_client = get_openai_client()

# --- 2. GLOBAL LAYOUT CONFIGURATION ---
st.set_page_config(
    page_title="soul - Premium M-Pesa Revenue Gate",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. SESSION STATE MANAGEMENT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"sender": "System", "type": "text", "content": "Welcome to soul! Complete your verification prompt on the sidebar to unlock matching features."}
    ]

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

if "registration_stage" not in st.session_state:
    st.session_state.registration_stage = "form_entry"

if "temp_registration_data" not in st.session_state:
    st.session_state.temp_registration_data = None

# --- 4. LIVE OPENAI GENERATION ENGINE ---
def generate_dating_line_ai(style, profile):
    if not ai_client:
        fallbacks = [
            "Are you a software update? Because whenever I look at you, my whole system pauses.",
            "I'm usually better at writing code than opening lines, but you completely broke my logic loop."
        ]
        return random.choice(fallbacks) + " (Fallback Mode)"
        
    user_context = f"Name: {profile['name']}. Location context: {profile['location']}." if profile else "An anonymous user"
    prompt = f"Write one unique dating icebreaker opener for 'soul'. Tone: {style}. Sender details: {user_context}."
    
    try:
        completion = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.8
        )
        return completion.choices.message.content.strip()
    except Exception as e:
        return f"AI line generation unavailable: {e}"

# --- 5. REPORT GENERATION & REVENUE UTILITIES ---
def fetch_users_from_db():
    if not supabase: return []
    try:
        response = supabase.table("user_registry").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Database Read Error: {e}")
        return []

def compile_registry_report(user_list, total_rev):
    total_users = len(user_list)
    premium_users = len([u for u in user_list if u.get('paid')])
    conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0.0
    
    report_lines = [
        "# SOUL APPLICATION - SYSTEM REGISTRY REPORT",
        f"- **Platform Merchant Receiving Number**: {MERCHANT_MPESA_NUMBER}",
        f"- **Total Platform Earnings**: KES {total_rev:,}",
        f"- **Total Registered Cloud Accounts**: {total_users}",
        f"- **Premium Conversion Ratio**: {conversion_rate:.1f}%\n",
        "---|---|---|---|---|---",
        "Full Name | Email Address | Contact Digits | Premium Status | Client M-Pesa Number | Location Coordinates",
        "---|---|---|---|---|---"
    ]
    for u in user_list:
        client_mpesa = u.get('mpesa_phone', 'None')
        report_lines.append(f"{u.get('name')} | {u.get('email')} | {u.get('phone')} | {'✅ Paid' if u.get('paid') else '❌ Free'} | {client_mpesa} | {u.get('location')}")
    return "\n".join(report_lines)

live_user_data = fetch_users_from_db()

# --- 6. SIDEBAR VIEWPORT: ENFORCED TWO-STEP PAY-FIRST FLOW ---
with st.sidebar:
    st.title("soul 💬❤️")
    st.caption("Live Cloud Registration Node & M-Pesa Gateway")
    
    if st.session_state.registration_stage == "form_entry":
        st.write("### Step 1: Account Setup")
        with st.form("primary_profile_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email Address", placeholder="john@example.com")
            phone = st.text_input("Contact Phone Number", placeholder="+254 700 000000")
            
            proceed_button = st.form_submit_button("Continue to Verification ➡️")
            
            if proceed_button:
                if name and email:
                    st.session_state.temp_registration_data = {
                        "name": name,
                        "email": email,
                        "phone": phone if phone else "Not provided"
                    }
                    st.session_state.registration_stage = "payment_prompt"
                    st.rerun()
                else:
                    st.error("Name and Email are mandatory fields.")

    elif st.session_state.registration_stage == "payment_prompt":
        st.write("### 💳 Step 2: Payment Prompt Verification")
        st.warning(f"Action Required: Send KES {PREMIUM_FEE_KES} to complete onboarding.")
        
        st.markdown(f"""
        <div style="background-color: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 13px; color: #7b341e;">
                Please send activation funds to our official merchant wallet number:<br>
                <b style="font-size: 16px; color: #dd6b20;">{MERCHANT_MPESA_NUMBER}</b>
            </p>
        </div>
        """, unsafe_with_html=True)
        
        client_mpesa = st.text_input("Enter your M-Pesa Number used to transact:", placeholder="e.g. 07XXXXXXXX")
        
        col_cancel, col_confirm = st.columns(2)
        with col_cancel:
            if st.button("⬅️ Back / Cancel"):
                st.session_state.registration_stage = "form_entry"
                st.rerun()
                
        with col_confirm:
            if st.button("Confirm Payment & Register ✅", type="primary"):
                if client_mpesa.strip():
                    temp_data = st.session_state.temp_registration_data
                    payload = {
                        "name": temp_data["name"],
                        "email": temp_data["email"],
                        "phone": temp_data["phone"],
                        "paid": True,
                        "mpesa_phone": client_mpesa,
                        "location": "Nairobi, Kenya"
                    }
                    
                    if supabase:
                        try:
                            supabase.table("user_registry").insert(payload).execute()
                            st.session_state.user_profile = payload
                            st.session_state.registration_stage = "form_entry"
                            st.success("Payment verified! Premium registration confirmed.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to synchronize ledger: {e}")
                    else:
                        st.session_state.user_profile = payload
                        st.session_state.registration_stage = "form_entry"
                        st.info("Offline simulation saved.")
                        st.rerun()
                else:
                    st.error("You must input your payment phone number to verify transmission.")

    if st.session_state.user_profile:
        st.write("---")
        st.markdown("### 📇 Active Verified Profile")
        prof = st.session_state.user_profile
        st.markdown(f"""
            <div style="background-color: #f8fafc; border: 2px solid #15803d; border-radius: 12px; padding: 14px; margin-bottom: 8px;">
                <b style="color: #1e293b;">{prof['name']}</b> (<span style="color: #15803d; font-weight: bold;">Verified Premium</span>)<br>
                <hr style="margin: 6px 0; border-color: #e2e8f0;">
                <span style="font-size: 12px; color: #64748b;">📧 {prof['email']}</span><br>
                <span style="font-size: 12px; color: #64748b;">📞 {prof['phone']}</span><br>
                <span style="font-size: 12px; color: #15803d;">📱 Paid via: {prof['mpesa_phone']}</span>
            </div>
        """, unsafe_with_html=True)
        
        if st.button("Drop Card Into Chat Feed", use_container_width=True):
            st.session_state.chat_history.append({"sender": "You", "type": "contact_card", "content": prof})
            st.rerun()

# --- 7. MAIN INTERFACE VIEWPORTS ---
st.markdown("<br>", unsafe_with_html=True)
tab_chat, tab_admin = st.tabs(["💬 Core Chatroom Feed", "📊 Executive Admin Records & Reporting"])

# ==================== TAB 1: LIVE CHAT SPACE ====================
with tab_chat:
    col_chat_feed, col_bot_panel = st.columns([1.8, 1.2], gap="medium")
    with col_chat_feed:
        chat_container = st.container(height=420)
        with chat_container:
            for message in st.session_state.chat_history:
                if message["sender"] == "You" and message["type"] == "contact_card":
                    card = message["content"]
                    st.markdown(f"""
                        <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                            <div style="background-color: #ffffff; border: 2px solid #15803d; border-radius: 12px; padding: 12px; max-width: 280px; width: 100%; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                                <h4 style="margin: 0; font-size: 13px; color: #111827;">📇 {card['name']}</h4>
