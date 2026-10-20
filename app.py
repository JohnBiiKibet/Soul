import streamlit as st
import random
import pandas as pd
from datetime import datetime
import pytz
import base64
import requests
from supabase import create_client, Client
from openai import OpenAI

# --- 1. GLOBAL LAYOUT CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="soul - Chat, AI & Live Global Members",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INITIALIZE DATABASE, AI, & MPESA SECRETS ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

# M-Pesa Integration Credentials
MPESA_CONSUMER_KEY = st.secrets.get("MPESA_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = st.secrets.get("MPESA_CONSUMER_SECRET", "")
MPESA_SHORTCODE = st.secrets.get("MPESA_SHORTCODE", "174379")  # Defaults to sandbox
MPESA_PASSKEY = st.secrets.get("MPESA_PASSKEY", "")

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

# --- 7. M-PESA DARAJA STK PUSH API ENGINE ---
def initiate_mpesa_stk_push(phone_number: str, amount: int) -> bool:
    """Triggers an instantaneous STK Push pop-up prompt menu directly onto the target device."""
    # Sanitize Phone Numbers (M-Pesa API standard normalization)
    phone_number = phone_number.strip().replace(" ", "").replace("+", "")
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("7") or phone_number.startswith("1"):
        phone_number = "254" + phone_number

    is_sandbox = "174379" in MPESA_SHORTCODE
    base_url = "https://safaricom.co.ke" if is_sandbox else "https://safaricom.co.ke"

    try:
        # Authenticate and Request Authorization Token Access
        auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_response = requests.get(auth_url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET), timeout=10)
        access_token = auth_response.json().get("access_token")
        
        if not access_token:
            st.error("M-Pesa Gateway Authentication Failed. Please verify credentials setup.")
            return False

        # Create Security Validation Timestamps and Hashes
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
        password_encoded = base64.b64encode(password_str.encode()).decode()

        # Construct Request Headers and Content Structure Payload
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        stk_payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password_encoded,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": "https://example.com",  # Replace with valid URL endpoint if using webhooks
            "AccountReference": "soul Premium",
            "TransactionDesc": "Registration fee entry verification"
        }

        # Push Payload Transmission
        stk_url = f"{base_url}/mpesa/stkpush/v1/processrequest"
        response = requests.post(stk_url, json=stk_payload, headers=headers, timeout=10)
        res_json = response.json()
        
        if res_json.get("ResponseCode") == "0":
            return True
        else:
            st.error(f"Safaricom Network Rejection: {res_json.get('ResponseDescription', 'Unknown API Error')}")
            return False

    except Exception as network_exception:
        st.error(f"M-Pesa API Outbound Connectivity Interrupted: {network_exception}")
        return False

# --- 8. SIDEBAR VIEWPORT: ACCOUNT METRICS & ACTIONS ---
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
