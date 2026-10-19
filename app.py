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
                    # Captured profile mapping setup payload cleanly closed with }
                    profile_payload = {
                        "name": st.session_state.temp_registration_data["name"],
                        "email": st.session_state.temp_registration_data["email"],
                        "phone": st.session_state.temp_registration_data["phone"],
                        "country": st.session_state.temp_registration_data["country"],
                        "mpesa_phone": mpesa_number,
                        "transaction_code": mpesa_code.upper(),
                        "location": get_local_time_string(st.session_state.temp_registration_data["country"]),
                        "paid": True
                    }
                    
                    if supabase:
                        try:
                            supabase.table("user_registry").insert(profile_payload).execute()
                        except Exception as db_err:
                            st.sidebar.warning(f"Local state active. Cloud syncing encountered: {db_err}")
                    
                    st.session_state.user_profile = profile_payload
                    st.success("Verification Confirmed! Welcome to the premium tier.")
                    st.rerun()
                else:
                    st.error("Please supply a valid payment mobile phone number and authentic confirmation code identifier.")

else:
    # --- 9. FULL ACCESS PREMIUM DASHBOARD ---
    st.markdown("## 💬 soul Global Premium Lounge")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Main Live Chat Feed")
        for item in st.session_state.chat_history:
            if item["type"] == "text":
                st.info(f"**{item['sender']}:** {item['content']}")
            elif item["type"] == "contact_card":
                card_data = item["content"]
                st.warning(f"📇 **{item['sender']} shared a Profile:** {card_data['name']} ({card_data.get('country', 'Global')}) | 📬 {card_data['email']}")
                
        with st.form("send_chat_msg", clear_on_submit=True):
            chat_text = st.text_input("Compose room broadcast message:")
            submit_msg = st.form_submit_button("Send Broadcast 📡")
            if submit_msg and chat_text:
                st.session_state.chat_history.append({"sender": st.session_state.user_profile["name"], "type": "text", "content": chat_text})
                st.rerun()
                
    with col2:
        st.write("### 🤖 Generative AI Icebreaker Tool")
        selected_style = st.radio("Icebreaker Opener Tone Concept Style:", ["Witty & Techy", "Charming & Direct", "Humorous & Sarcastic"])
        if st.button("Generate Tailored Icebreaker ⚡", use_container_width=True):
            ai_line = generate_dating_line_ai(selected_style, st.session_state.user_profile)
            st.code(ai_line, language="text")
            
        st.markdown("---")
        st.write("### 👥 Cloud Member Nodes Status")
        if live_user_data:
            df = pd.DataFrame(live_user_data)
            if not df.empty and 'name' in df.columns:
                st.dataframe(df[['name', 'country', 'location']], use_container_width=True)
        else:
            st.caption("No external room peers pulled down yet. You are currently the primary member.")
