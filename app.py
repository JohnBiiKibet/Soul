import streamlit as st
import random
import pandas as pd
from supabase import create_client, Client
from openai import OpenAI

# --- 1. GLOBAL LAYOUT CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="soul - Enforced Premium Registration",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INITIALIZE DATABASE & AI SECRETS ENVIRONMENT ---
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

# --- 3. SESSION STATE MANAGEMENT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"sender": "System", "type": "text", "content": "Welcome to soul! Enforced verification is active. Pay to unlock matching, chat rooms, and AI tools."}
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

# --- 6. SIDEBAR VIEWPORT: MANDATORY PAY-FIRST ROADBLOCK FLOW ---
with st.sidebar:
    st.title("soul 💬❤️")
    st.caption("Live Cloud Registration Node & M-Pesa Gateway")
    
    # STAGE 1: Collect core name/email properties
    if st.session_state.registration_stage == "form_entry" and not st.session_state.user_profile:
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

    # STAGE 2: MANDATORY INTERCEPT—Blocks access entirely unless transaction values exist
    elif st.session_state.registration_stage == "payment_prompt" and not st.session_state.user_profile:
        st.write("### 🔒 Step 2: Pay to Unlock Registration")
        st.error("Access Prohibited: Paid activation required to enter platform features.")
        
        st.markdown(f"""
        <div style="background-color: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 13px; color: #7b341e;">
                Send exactly <b>KES {PREMIUM_FEE_KES}</b> to our official payment node:<br>
                M-Pesa Number: <b style="font-size: 16px; color: #dd6b20;">{MERCHANT_MPESA_NUMBER}</b>
            </p>
        </div>
        """, unsafe_with_html=True)
        
        client_mpesa = st.text_input("Your M-Pesa Phone Number", placeholder="07XXXXXXXX")
        mpesa_code = st.text_input("M-Pesa Transaction Confirmation Code", placeholder="e.g. QRA1234567").strip().upper()
        
        col_cancel, col_confirm = st.columns(2)
        with col_cancel:
            if st.button("⬅️ Cancel"):
                st.session_state.registration_stage = "form_entry"
                st.rerun()
                
        with col_confirm:
            if st.button("Verify & Complete Registration ✅", type="primary"):
                # Strict Gate Enforcer: Checking that phone and transaction text string parameters are present
                if client_mpesa.strip() and mpesa_code:
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
                            st.session_state.registration_stage = "completed"
                            st.success(f"Payment cleared! Welcome to soul, {temp_data['name']}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database sync fail: {e}")
                    else:
                        st.session_state.user_profile = payload
                        st.session_state.registration_stage = "completed"
                        st.info("Offline validation simulation saved.")
                        st.rerun()
                else:
                    st.error("⛔ REGISTRATION DENIED: You must provide your M-Pesa number and Transaction Code to unlock the app.")

    # STAGE 3: Account verified state
    if st.session_state.user_profile:
        st.write("### 📇 Active Account Verified")
        prof = st.session_state.user_profile
        st.success(f"**{prof['name']}** (Verified Premium)")
        st.text(f"📧 Email: {prof['email']}")
        st.text(f"📞 Phone: {prof['phone']}")
        st.text(f"📱 M-Pesa: {prof['mpesa_phone']}")
        
        if st.button("Drop Card Into Chat Feed", use_container_width=True):
            st.session_state.chat_history.append({"sender": "You", "type": "contact_card", "content": prof})
            st.rerun()
            
        if st.button("🚪 Sign Out / New Registration", use_container_width=True, type="secondary"):
            st.session_state.user_profile = None
            st.session_state.registration_stage = "form_entry"
            st.rerun()

# --- 7. MAIN INTERFACE INTERNALS: HIDDEN ENTRIES IF NOT REGISTERED ---
st.markdown("<br>", unsafe_allow_html=True)

if not st.session_state.user_profile:
    # If the user is unverified, lock the main workspace viewports completely to prevent data sniffing
    st.info("🔒 **Welcome to soul.** Please fill out your details and pay KES 20 using the sidebar menu to unlock the live chatroom feed and the Generative AI Dating assistant tool.")
else:
    tab_chat, tab_admin = st.tabs(["💬 Core Chatroom Feed", "📊 Executive Admin Records & Reporting"])

    # ==================== TAB 1: LIVE CHAT SPACE ====================
    with tab_chat:
        col_chat_feed, col_bot_panel = st.columns([1.8, 1.2], gap="medium")
        with col_chat_feed:
            chat_container = st.container(height=420)
