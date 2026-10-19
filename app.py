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
            <p style="color: #64748b; font-size: 16px; margin-bottom: 24px;">An exclusive chatroom feed and Generative AI Dating gateway.</p>
            <p style="font-weight: 600; color: #3b82f6;">Please complete your Step 1 profile setup in the sidebar to proceed.</p>
        </div>
        """, unsafe_allow_html=True)
        
    elif st.session_state.registration_stage == "payment_prompt":
        # Form Entry Completed -> Prompting payment step details on main stage
        st.markdown(f"""
        <div style="background-color: #fffdf5; padding: 30px; border-radius: 12px; border: 1px solid #fef08a; max-width: 700px; margin: 20px auto;">
            <h2 style="color: #854d0e; margin-top: 0;">Complete Premium Verification</h2>
            <p>To view global online members and activate your chat routing module, an activation fee is required:</p>
            <ul>
                <li><strong>Amount:</strong> KES {PREMIUM_FEE_KES}</li>
                <li><strong>Merchant Destination Number:</strong> {MERCHANT_MPESA_NUMBER}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.write("### Confirm M-Pesa Billing Information")
            mpesa_number = st.text_input("Enter Your M-Pesa Number (Used for verification)", placeholder="07XXXXXXXX")
            mpesa_code = st.text_input("Enter M-Pesa Transaction Code", placeholder="SJKXXXXXXX")
            
            if st.button("Complete Premium Onboarding Verification 🚀", type="primary"):
                if len(mpesa_number) >= 9 and len(mpesa_code) >= 6:
                    # Capture registration data construct
                    profile_payload = {
                        "name": st.session_state.temp_registration_data["name"],
                        "email": st.session_state.temp_registration_data["email"],
