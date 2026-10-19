import streamlit as st
import random
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client
from openai import OpenAI

# --- 1. GLOBAL LAYOUT CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="soul - Chat, AI & Live Global Members",
    page_icon="🔒",
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
        {"sender": "System", "type": "text", "content": "Welcome to soul! Global premium activation verified successfully."}
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
        
    user_context = f"Name: {profile['name']}. Location context: {profile['location']}. Country: {profile.get('country', 'Kenya')}." if profile else "An anonymous user"
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

# --- 5. GLOBAL GEOGRAPHY & TIME ZONE UTILITIES ---
TIMEZONE_MAPPING = {
    "Kenya 🇰🇪": "Africa/Nairobi",
    "Tanzania 🇹🇿": "Africa/Dar_es_Salaam",
    "Uganda 🇺🇬": "Africa/Kampala",
    "Rwanda 🇷🇼": "Africa/Kigali",
    "United Kingdom 🇬🇧": "Europe/London",
    "United States 🇺🇸": "America/New_York",
    "Germany 🇩🇪": "Europe/Berlin"
}

def get_local_time_string(country_name):
    """Computes the active current time inside a specific country's boundaries."""
    tz_zone = TIMEZONE_MAPPING.get(country_name, "Africa/Nairobi")
    try:
        target_tz = pytz.timezone(tz_zone)
        local_dt = datetime.now(target_tz)
        return local_dt.strftime("%I:%M %p")
    except Exception:
        return datetime.now().strftime("%I:%M %p")

# --- 6. REPORT GENERATION & REVENUE UTILITIES ---
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
        "---|---|---|---|---|---|---",
        "Full Name | Email Address | Contact Digits | Premium Status | Client M-Pesa Number | Country Code | Region Coordinates",
        "---|---|---|---|---|---|---"
    ]
    for u in user_list:
        client_mpesa = u.get('mpesa_phone', 'None')
        country_val = u.get('country', 'Kenya 🇰🇪')
        report_lines.append(f"{u.get('name')} | {u.get('email')} | {u.get('phone')} | {'✅ Paid' if u.get('paid') else '❌ Free'} | {client_mpesa} | {country_val} | {u.get('location')}")
    return "\n".join(report_lines)

live_user_data = fetch_users_from_db()

# --- 7. SIDEBAR VIEWPORT: ACCOUNT METRICS & ACTIONS ---
with st.sidebar:
    st.title("soul 💬❤️")
    st.caption("Onboarding Authentication Center")
    
    if st.session_state.registration_stage == "form_entry" and not st.session_state.user_profile:
        st.write("### Step 1: Profile Setup")
        with st.form("primary_profile_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email Address", placeholder="john@example.com")
            phone = st.text_input("Contact Phone Number", placeholder="+254 7XX XXX XXX")
            selected_country = st.selectbox("Select Your Country:", list(TIMEZONE_MAPPING.keys()))
            
            proceed_button = st.form_submit_button("Proceed to Verification ➡️")
            
            if proceed_button:
                if name and email:
                    st.session_state.temp_registration_data = {
                        "name": name,
                        "email": email,
                        "phone": phone if phone else "Not provided",
                        "country": selected_country
                    }
                    st.session_state.registration_stage = "payment_prompt"
                    st.rerun()
                else:
                    st.error("Name and Email are mandatory fields.")

    elif st.session_state.registration_stage == "payment_prompt" and not st.session_state.user_profile:
        st.write("### 💳 Verification Pending")
        st.info("Please fill out the billing checkout form on the main screen page area to unlock access.")
        if st.button("⬅️ Edit Profile Info"):
            st.session_state.registration_stage = "form_entry"
            st.rerun()

    if st.session_state.user_profile:
        st.write("### 📇 Authenticated Session")
        prof = st.session_state.user_profile
        st.success(f"**{prof['name']}** (Online)")
        st.caption(f"Origin Node: {prof.get('country', 'Kenya 🇰🇪')}")
        st.text(f"📧 Email: {prof['email']}")
        st.text(f"📱 M-Pesa: {prof['mpesa_phone']}")
        
        if st.button("Drop Card Into Chat Feed", use_container_width=True):
            st.session_state.chat_history.append({"sender": "You", "type": "contact_card", "content": prof})
            st.rerun()
            
        if st.button("🚪 Sign Out / New Session", use_container_width=True, type="secondary"):
            st.session_state.user_profile = None
            st.session_state.registration_stage = "form_entry"
            st.rerun()

# --- 8. MAIN INTERFACE VIEWPORT MAPS ---
st.markdown("<br>", unsafe_allow_html=True)

# GATED ROUTING CONDITION: If user has not successfully paid, display the invoice billing screen
if not st.session_state.user_profile:
    
    if st.session_state.registration_stage == "form_entry":
        st.markdown(f"""
        <div style="background-color: #f1f5f9; padding: 40px; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; max-width: 800px; margin: 40px auto;">
            <h1 style="color: #0f172a; margin-bottom: 8px; font-size: 28px;">Welcome to soul</h1>
            <p style="color: #64748b; font-size: 16px; margin-bottom: 24px;">An exclusive global matching stream, real-time chatroom, and generative AI conversation assistant.</p>
            <hr style="border-color: #e2e8f0; margin-bottom: 24px;">
            <h3 style="color: #4f46e5; margin-bottom: 4px;">Account Setup Required</h3>
            <p style="color: #475569; font-size: 14px; margin-bottom: 0;">Please fill out your **Full Name** and **Email Address** inside the left sidebar form block to get started.</p>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.registration_stage == "payment_prompt":
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 40px; border-radius: 16px; border: 2px solid #ef4444; max-width: 750px; margin: 20px auto; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 24px;">
                <span style="font-size: 48px;">🔒</span>
                <h1 style="color: #1e293b; margin: 12px 0 4px 0; font-size: 26px;">Account Verification Required</h1>
                <p style="color: #ef4444; font-weight: 600; font-size: 15px; margin: 0;">PREMIUM STATUS: UNPAID</p>
            </div>
            
            <div style="background-color: #fef2f2; border: 1px solid #fee2e2; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
                <p style="margin: 0; color: #991b1b; font-size: 14px;">Verification Activation Fee Amount Due:</p>
                <h2 style="margin: 6px 0; color: #dc2626; font-size: 36px; font-weight: 800;">KES {PREMIUM_FEE_KES}.00</h2>
                <p style="margin: 0; color: #7f1d1d; font-size: 12px; font-weight: 500;">One-time charge to unlock account privileges and see live members online.</p>
            </div>
            
