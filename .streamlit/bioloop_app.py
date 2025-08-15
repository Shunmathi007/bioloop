import streamlit as st
import json, os, re, hashlib, base64, io
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import distance as geo_distance
import pandas as pd
from fpdf import FPDF

# --- LOCALIZATION ---
labels = {
    "English": {
        # ... full list from your original code ...
        "submit": "Submit Waste", "material": "Material Type", # etc.
    },
    "தமிழ்": {
        "submit": "கழிவை சமர்ப்பி", "material": "பொருள் வகை", "login": "உள்நுழை", "password": "கடவுச்சொல்",
        "signup": "பதிவு செய்", "location": "இடம்", "quantity": "அளவு (கிலோ/வாரம்)", "invalid_login": "🔐 தவறான உள்நுழைவு.",
        "header": "உங்கள் கழிவை சமர்ப்பிக்கவும்", "contact": "தொடர்பு தகவல்", "quality": "தரம்",
        "public_contact": "தொடர்பு பொதுவாக", "account_created": "✅ கணக்கு உருவாக்கப்பட்டது! உள்நுழையவும்.",
        "duplicate_id": "🚫 ஐடி ஏற்கனவே உள்ளது.", "missing_fields": "உங்கள் தகவலை நிரப்பவும்.",
        "logout": "வெளியேறு", "back": "பின்னால்", "success": "சமர்ப்பிப்பு சேமிக்கப்பட்டது.",
        "upload_image": "கழிவின் படத்தை பதிவேற்று", "matched": "பொருந்தியது",
        "go_home": "முதன்மை பக்கம்", "invalid_contact": "தவறான தொடர்பு.",
        "filter_material": "பொருள் மூலம் வடிகட்டு", "filter_location": "இடம் மூலம் வடிகட்டு",
        "browse_waste": "கழிவுகளைக் காண", "all": "அனைத்தும்", "kg_week": "கிலோ/வாரம்",
        "clean": "சுத்தம்", "mixed": "கலந்தது", "contaminated": "கழிவானது",
        "my_submissions": "என் சமர்ப்பிப்புகள்", "analytics": "பகுப்பாய்வு", "microplanner": "மைக்ரோ யூனிட் திட்டம்", "export": "தரவு ஏற்று",
        "admin_panel": "நிர்வாகப் பலகை", "top_materials": "மேம்பட்ட பொருள்கள்",
        "no_data": "தரவு இல்லை.", "no_entries": "நீங்கள் இன்னும் சமர்ப்பிக்கவில்லை.",
        "delete_success": "✅ சமர்ப்பிப்பு நீக்கப்பட்டது.", "download_csv": "CSV பதிவிறக்கு",
        "browse": "பொருள்கள் பார்க்க", "otp": "உங்கள் மின்னஞ்சலில் OTP உள்ளிடவும் (1234)",
        "verify": "சரிபார்க்க", "verified": "சரிபார்க்கப்பட்ட MSME 🟢", "not_verified": "சரிபார்க்கவில்லை 🔴",
        "rate": "இந்த பயனரை மதிப்பிடு", "rating": "மதிப்பீடு", "submit_rating": "மதிப்பீடு சமர்ப்பி", "thanks_rating": "மதிப்பீட்டுக்கு நன்றி!",
        "success_story": "🌟 வெற்றி கதைகள்", "share_story": "உங்கள் கதையை பகிரவும்", "submit_story": "கதை சமர்ப்பி",
        "story_submitted": "கதை சமர்ப்பிக்கப்பட்டது!", "impact_dash": "🌏 தாக்கம்",
        "register_interest": "🔔 விருப்பம் பதிவு செய்", "interest_material": "பொருள்", "interest_location": "விருப்ப இடம்",
        "interest_registered": "விருப்பம் பதிவு செய்யப்பட்டது!", "your_interests": "உங்கள் விருப்பங்கள்", "msg": "💬 செய்திகள்", "send": "அனுப்பு",
        "howto": "🎓 எப்படி & ஏற்குதல்", "ai_help": "🤖 உதவி தேவை? FAQ ஐ கேளுங்கள்:",
        "download_cert": "🎓 பசுமை MSME சான்றிதழ் பதிவிறக்க",
        "profile": "சுயவிவரம்", "leaderboard": "🏆 சிறந்த பங்களிப்பாளர்கள்", "badge_gold": "🥇 தங்கம்",
        "badge_silver": "🥈 வெள்ளி", "badge_bronze": "🥉 வெண்கலம்",
        "add_story_video": "உங்கள் கதை/வீடியோ சேர்க்கவும்", "video_url": "உங்கள் YouTube இணைப்பு",
        "story_title": "கதை தலைப்பு", "story_desc": "உங்கள் கதை/தாக்கம் எழுதவும்", "submit_video": "வீடியோ சமர்ப்பி",
        "video_submitted": "வீடியோ சமர்ப்பிக்கப்பட்டது!", "faq_title": "❓ MSME FAQ Bot", "ask_question": "உங்கள் கேள்வி கேளுங்கள்",
        "ask": "கேள்", "video_section": "🎬 சமூக வீடியோக்கள்", "no_video_stories": "வீடியோக்கள் இல்லை.",
        "report_listing": "🚩 பட்டியலை புகார் செய்", "reported": "புகார் செய்யப்பட்டது!", "already_reported": "ஏற்கனவே புகார் செய்யப்பட்டது.",
        "privacy": "தனியுரிமைக் கொள்கை", "privacy_summary": "உங்கள் தொடர்பு தகவல் பொதுவாக காட்டப்படும். உங்கள் தரவு விற்கப்படாது.",
        "show_contact": "பட்டியலில் தொடர்பு தகவல் காட்டவும்", "hide_contact": "பட்டியலில் காட்ட வேண்டாம்",
        "notifications": "🔔 அறிவிப்புகள்", "no_notifications": "அறிவிப்புகள் இல்லை.",
        "batch_pickup": "பேட்ச் பிக்-அப் சேர", "joined_batch": "நீங்கள் பேட்சில் சேர்ந்துள்ளீர்கள்!", "already_joined": "ஏற்கனவே சேர்ந்துள்ளீர்கள்.",
        "progress": "உங்கள் பசுமை வளர்ச்சி", "next_badge": "அடுத்த பேட்ஜ்", "early_adopter": "🌱 ஆரம்ப பங்காளர்",
        "whatsapp": "WhatsApp சமூகத்தைச் சேர", "howto_desc": "டெமோ பார்க்க, சமூகத்தைச் சேர, BioLoop ஐ முழுமையாக பயன்படுத்துங்கள்.",
        "admin_review": "நிர்வாகப் பரிசீலனை", "gstin": "GSTIN (சரிபார்ப்பு)", "submit_signup": "பதிவு செய்",
        "admin_approve": "அங்கீகரி", "admin_reject": "நிராகரி", "approved": "அங்கீகரிக்கப்பட்டது!", "rejected": "நிராகரிக்கப்பட்டது.",
    },
    "हिन्दी": {
        "submit": "अपशिष्ट जमा करें", "material": "सामग्री प्रकार", "login": "एमएसएमई लॉगिन", "password": "पासवर्ड",
        "signup": "साइन अप", "location": "स्थान", "quantity": "मात्रा (किलो/सप्ताह)", "invalid_login": "🔐 अमान्य लॉगिन.",
        "header": "अपना अपशिष्ट जमा करें", "contact": "संपर्क जानकारी", "quality": "गुणवत्ता",
        "public_contact": "संपर्क सार्वजनिक रूप से दिखाएं", "account_created": "✅ खाता बन गया! कृपया लॉगिन करें.",
        "duplicate_id": "🚫 आईडी पहले से मौजूद है.", "missing_fields": "कृपया सभी फ़ील्ड भरें.",
        "logout": "लॉगआउट", "back": "वापस", "success": "जमा सफल रहा.",
        "upload_image": "अपशिष्ट की तस्वीर अपलोड करें", "matched": "मिलान हुआ",
        "go_home": "होम पर जाएं", "invalid_contact": "अमान्य संपर्क.",
        "filter_material": "सामग्री से फ़िल्टर करें", "filter_location": "स्थान से फ़िल्टर करें",
        "browse_waste": "अपशिष्ट लिस्टिंग देखें", "all": "सभी", "kg_week": "किलो/सप्ताह",
        "clean": "स्वच्छ", "mixed": "मिश्रित", "contaminated": "दूषित",
        "my_submissions": "मेरी जमा", "analytics": "एनालिटिक्स", "microplanner": "माइक्रो-यूनिट योजनाकर्ता", "export": "डाटा एक्सपोर्ट",
        "admin_panel": "एडमिन पैनल", "top_materials": "शीर्ष जमा सामग्री",
        "no_data": "डाटा नहीं मिला.", "no_entries": "आपने अभी तक कोई अपशिष्ट जमा नहीं किया.",
        "delete_success": "✅ जमा सफलतापूर्वक हटाया गया.", "download_csv": "CSV डाउनलोड करें",
        "browse": "सामग्री ब्राउज़ करें", "otp": "अपने ईमेल पर भेजा गया OTP डालें (1234)",
        "verify": "वेरीफाई करें", "verified": "वेरीफाईड MSME 🟢", "not_verified": "वेरीफाई नहीं हुआ 🔴",
        "rate": "इस उपयोगकर्ता को रेट करें", "rating": "रेटिंग", "submit_rating": "रेटिंग सबमिट करें", "thanks_rating": "रेटिंग के लिए धन्यवाद!",
        "success_story": "🌟 सफलता की कहानियाँ", "share_story": "अपनी कहानी साझा करें", "submit_story": "कहानी सबमिट करें",
        "story_submitted": "कहानी सबमिट हो गई!", "impact_dash": "🌏 प्रभाव डैशबोर्ड",
        "register_interest": "🔔 रुचि दर्ज करें", "interest_material": "सामग्री", "interest_location": "वांछित स्थान",
        "interest_registered": "रुचि सफलतापूर्वक दर्ज हो गई!", "your_interests": "आपकी दर्ज रुचियाँ", "msg": "💬 संदेश", "send": "भेजें",
        "howto": "🎓 कैसे करें & अपनाएँ", "ai_help": "🤖 सहायता चाहिए? नीचे हमारे FAQ बॉट से पूछें:",
        "download_cert": "🎓 ग्रीन MSME प्रमाणपत्र डाउनलोड करें",
        "profile": "प्रोफाइल", "leaderboard": "🏆 शीर्ष योगदानकर्ता", "badge_gold": "🥇 गोल्ड",
        "badge_silver": "🥈 सिल्वर", "badge_bronze": "🥉 ब्रॉन्ज",
        "add_story_video": "अपनी कहानी/वीडियो जोड़ें", "video_url": "अपनी कहानी/नवाचार का YouTube लिंक डालें",
        "story_title": "कहानी शीर्षक", "story_desc": "यहाँ अपनी कहानी/प्रभाव लिखें", "submit_video": "वीडियो कहानी सबमिट करें",
        "video_submitted": "वीडियो/कहानी सबमिट हो गई!", "faq_title": "❓ MSME FAQ Bot", "ask_question": "अपना सवाल पूछें",
        "ask": "पूछें", "video_section": "🎬 समुदाय वीडियो/कहानियाँ", "no_video_stories": "अभी कोई वीडियो नहीं.",
        "report_listing": "🚩 लिस्टिंग रिपोर्ट करें", "reported": "रिपोर्ट किया गया! धन्यवाद!", "already_reported": "पहले ही रिपोर्ट किया गया.",
        "privacy": "गोपनीयता नीति", "privacy_summary": "हम केवल तभी संपर्क दिखाते हैं जब आप अनुमति दें. आपका डाटा कभी बेचा नहीं जाता.",
        "show_contact": "लिस्टिंग पर मेरा संपर्क दिखाएँ", "hide_contact": "लिस्टिंग पर मेरा संपर्क छिपाएँ",
        "notifications": "🔔 सूचनाएँ", "no_notifications": "कोई नयी सूचना नहीं.",
        "batch_pickup": "बैच पिकअप से जुड़ें", "joined_batch": "आपने इस बैच में भाग लिया!", "already_joined": "पहले ही जुड़ चुके हैं.",
        "progress": "आपकी ग्रीन प्रगति", "next_badge": "अगला बैज", "early_adopter": "🌱 शुरुआती",
        "whatsapp": "WhatsApp समुदाय से जुड़ें", "howto_desc": "डेमो देखें, समुदाय से जुड़ें, और BioLoop का अधिकतम उपयोग करें.",
        "admin_review": "एडमिन समीक्षा चल रही है", "gstin": "GSTIN (सत्यापन)", "submit_signup": "रजिस्टर करें",
        "admin_approve": "स्वीकृत करें", "admin_reject": "अस्वीकृत करें", "approved": "स्वीकृत!", "rejected": "अस्वीकृत.",
    },
}
def L(key): return labels[st.session_state["lang"]].get(key, key)

# --- DATA FILES ---
DATA_FILE = "data/waste_profiles.json"
USER_FILE = "data/users.json"
INTERESTS_FILE = "data/interests.json"
MESSAGES_DIR = "data/messages/"
STORIES_FILE = "data/success_stories.json"
RATINGS_FILE = "data/ratings.json"
REPORTS_FILE = "data/reports.json"
BATCHES_FILE = "data/batch_pickups.json"
NOTIFICATIONS_FILE = "data/notifications.json"
os.makedirs("data", exist_ok=True)
os.makedirs(MESSAGES_DIR, exist_ok=True)
for f in [DATA_FILE, USER_FILE, INTERESTS_FILE, STORIES_FILE, RATINGS_FILE, REPORTS_FILE, BATCHES_FILE, NOTIFICATIONS_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump([] if f.endswith(".json") else {}, file)

# --- UTILITY FUNCTIONS ---
def load_datafile(path, default=None):
    if not os.path.exists(path): return default
    with open(path) as f:
        try: return json.load(f)
        except: return default
def save_datafile(path, data):
    with open(path, "w") as f: json.dump(data, f, indent=2)
def load_data(): return load_datafile(DATA_FILE, [])
def save_data(data): save_datafile(DATA_FILE, data)
def load_users():
    users = load_datafile(USER_FILE, {})
    return users if isinstance(users, dict) else {}
def save_users(users): save_datafile(USER_FILE, users)
def add_notification(user, msg):
    notifs = load_datafile(NOTIFICATIONS_FILE, [])
    notifs.append({"user": user, "msg": msg, "time": datetime.now().isoformat()})
    save_datafile(NOTIFICATIONS_FILE, notifs)
def get_user_rating(user_id):
    ratings = load_datafile(RATINGS_FILE, [])
    user_ratings = [r["rating"] for r in ratings if r["user"] == user_id]
    if user_ratings:
        return round(sum(user_ratings) / len(user_ratings), 1)
    else:
        return "N/A"
def generate_trace_hash(entry):
    raw = f"{entry['material']}{entry['quantity']}{entry['location']}_{entry['timestamp']}"
    return hashlib.sha256(raw.encode()).hexdigest()
def validate_gstin(gstin):
    # Placeholder for GSTIN API validation, return True if format is valid
    return bool(re.match(r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}", gstin))
geolocator = Nominatim(user_agent="bioloop")

# --- REUSE DB, MICRO UNITS, CARBON FACTORS ---
reuse_db = {
    "cotton scraps": ["🧸 Toy Stuffing", "🧵 Yarn Recyclers"],
    "metal scraps": ["⚙ Metal Artist", "🪑 Furniture Maker"],
    "food waste": ["🌱 Composting", "🔥 Biogas"],
    "sawdust": ["🪵 Board Makers", "🔥 Briquette Units"],
    "paper waste": ["📚 Stationery", "📦 Packaging"]
}
micro_units = {
    "cotton scraps": {"unit": "Stuffing Unit", "tool": "Shredder (₹8,000)", "roi": "2 months"},
    "metal scraps": {"unit": "Art Studio", "tool": "Welder (₹12,000)", "roi": "₹6,000/month"},
    "food waste": {"unit": "Compost Bin", "tool": "Bin (₹2,000)", "roi": "₹1,500/month"},
    "sawdust": {"unit": "Briquette Unit", "tool": "Press (₹15,000)", "roi": "₹3,000/month"},
    "paper waste": {"unit": "Paper Unit", "tool": "Pulper (₹10,000)", "roi": "₹2,500/month"}
}
carbon_factors = {
    "cotton scraps": 2.5, "metal scraps": 6.0, "food waste": 1.8,
    "sawdust": 2.2, "paper waste": 2.9
}
import streamlit as st
from bioloop_core import *
from datetime import datetime
# --- SETUP PAGE CONFIG ---
st.set_page_config(page_title="BioLoop", page_icon="♻", layout="centered")
for k, v in [
    ("authenticated", False), ("user_id", ""), ("page", "landing"),
    ("lang", "English"), ("verified", False), ("prev_page", "landing"),
    ("notifications", []),
]: st.session_state.setdefault(k, v)

# --- LANG SELECTOR ---
def lang_selector():
    lang = st.selectbox("🌍", list(labels.keys()),
                        index=list(labels.keys()).index(st.session_state["lang"]))
    st.session_state["lang"] = lang

# --- PAGE NAV ---
def go(page):
    st.session_state["prev_page"] = st.session_state.get("page", "landing")
    st.session_state["page"] = page
def back_button(default="landing"):
    prev = st.session_state.get("prev_page", default)
    if st.button("⬅ " + L("back")):
        st.session_state["page"] = prev

# --- LOGIN/SIGNUP/LOGOUT ---
def login_page():
    st.markdown(f"<div class='biol-title'>{L('login')}</div>", unsafe_allow_html=True)
    lang_selector()
    users = load_users()
    user = st.text_input("MSME ID")
    pw = st.text_input(L("password"), type="password")
    if st.button(L("login")):
        if user in users and users[user]["pw"] == pw and users[user].get("approved", False):
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user
            st.session_state["verified"] = users[user].get("verified", False)
            st.session_state["early"] = users[user].get("early", False)
            st.session_state["privacy"] = users[user].get("privacy", True)
            st.session_state["page"] = "home"
        elif user in users and not users[user].get("approved", False):
            st.warning(L("admin_review"))
        else:
            st.error(L("invalid_login"))
    back_button("landing")

def signup_page():
    st.markdown(f"<div class='biol-title'>{L('signup')}</div>", unsafe_allow_html=True)
    lang_selector()
    users = load_users()
    new_id = st.text_input("Choose MSME ID")
    new_pw = st.text_input("Choose Password", type="password")
    gstin = st.text_input(L("gstin"))
    if st.button(L("submit_signup")):
        if new_id in users:
            st.error(L("duplicate_id"))
        elif not new_id or not new_pw or not gstin:
            st.warning(L("missing_fields"))
        elif not validate_gstin(gstin):
            st.warning(L("invalid_contact"))
        else:
            users[new_id] = {
                "pw": new_pw,
                "gstin": gstin,
                "verified": False,
                "approved": False,
                "early": datetime.now().isoformat() < "2025-12-31T00:00:00",
                "privacy": True
            }
            save_users(users)
            st.success(L("account_created") + " " + L("admin_review"))
            st.button(L("login"), on_click=go, args=("login",))
    back_button("landing")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = ""
    st.session_state["page"] = "landing"

def verify_user():
    if not st.session_state.get("verified"):
        otp = st.text_input(L("otp"))
        if st.button(L("verify")):
            if otp == "1234":
                st.session_state["verified"] = True
                users = load_users()
                users[st.session_state["user_id"]]["verified"] = True
                save_users(users)
                st.success(L("verified"))
            else:
                st.error("Incorrect OTP.")

# --- PRIVACY SETTINGS ---
def privacy_settings():
    st.header(L("privacy"))
    users = load_users()
    user_id = st.session_state["user_id"]
    privacy = users[user_id].get("privacy", True)
    show_contact = st.checkbox(L("show_contact"), value=privacy)
    if st.button("Save Privacy Settings"):
        users[user_id]["privacy"] = show_contact
        save_users(users)
        st.session_state["privacy"] = show_contact
        st.success("Privacy Updated!")
    back_button("dashboard")

# --- LANDING PAGE ---
def landing_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown(f"<div class='biol-title' style='text-align:center;'>♻ BioLoop</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='biol-sub' style='text-align:center;'>Empowering Circular Economy for MSMEs</div>", unsafe_allow_html=True)
        lang_selector()
        st.button(L("login"), use_container_width=True, on_click=go, args=("login",))
        st.button(L("signup"), use_container_width=True, on_click=go, args=("signup",))
        st.button(L("faq_title"), use_container_width=True, on_click=go, args=("faq",))
        st.button(L("add_story_video"), use_container_width=True, on_click=go, args=("addvideo",))
        st.button(L("video_section"), use_container_width=True, on_click=go, args=("videos",))
        st.button(L("howto"), use_container_width=True, on_click=go, args=("howto",))
        st.button(L("privacy"), use_container_width=True, on_click=go, args=("privacy",))
        st.button(L("whatsapp"), use_container_width=True, on_click=go, args=("chat",))

# --- HOME PAGE ---
def user_badge(user_id):
    if user_id == "admin@bioloop.in":
        return "🛡 Admin"
    if st.session_state.get("verified"):
        return L("verified")
    return L("not_verified")

def home_page():
    st.markdown(f"<div class='biol-title'>Hi, {st.session_state['user_id']}! {user_badge(st.session_state['user_id'])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='biol-sub'>{L('browse')}</div>", unsafe_allow_html=True)
    if st.session_state.get("early"): st.info(L("early_adopter"))
    if not st.session_state.get("verified"):
        verify_user()
    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 " + L("submit"), on_click=go, args=("submit",), use_container_width=True)
        st.button("👤 " + L("my_submissions"), on_click=go, args=("dashboard",), use_container_width=True)
        st.button(L("register_interest"), on_click=go, args=("interest",), use_container_width=True)
        st.button("📈 " + L("analytics"), on_click=go, args=("analytics",), use_container_width=True)
        st.button(L("notifications"), on_click=go, args=("notifications",), use_container_width=True)
    with col2:
        st.button("🔍 " + L("browse"), on_click=go, args=("browse",), use_container_width=True)
        st.button("🏭 " + L("microplanner"), on_click=go, args=("microplanner",), use_container_width=True)
        st.button("📤 " + L("export"), on_click=go, args=("export",), use_container_width=True)
        st.button(L("faq_title"), on_click=go, args=("faq",), use_container_width=True)
        st.button(L("add_story_video"), on_click=go, args=("addvideo",), use_container_width=True)
        st.button(L("video_section"), on_click=go, args=("videos",), use_container_width=True)
        st.button(L("privacy"), on_click=go, args=("privacy_settings",), use_container_width=True)
        st.button(L("whatsapp"), on_click=go, args=("chat",), use_container_width=True)
    if st.session_state["user_id"] == "admin@bioloop.in":
        st.button("Admin Panel", on_click=go, args=("admin",), use_container_width=True)
    st.button(L("logout"), on_click=logout, use_container_width=True)
    back_button("landing")

# -- ADMIN PANEL --
def admin_panel():
    st.header(L("admin_panel"))
    users = load_users()
    unapproved = [u for u, d in users.items() if not d.get("approved")]
    for uid in unapproved:
        st.write(f"{uid} (GSTIN: {users[uid]['gstin']})")
        c1, c2 = st.columns(2)
        if c1.button(L("admin_approve"), key=f"ap-{uid}"):
            users[uid]["approved"] = True
            save_users(users)
            st.success(L("approved"))
        if c2.button(L("admin_reject"), key=f"rej-{uid}"):
            users[uid]["approved"] = False
            save_users(users)
            st.error(L("rejected"))
    st.markdown("---")
    reports = load_datafile(REPORTS_FILE, [])
    st.subheader("Reported Listings")
    for r in reports[::-1]:
        st.write(f"Reported by: {r['reporter']} | Listing ID: {r['trace_id']}")
        st.write(r["reason"])
    back_button("home")

# -- COMMUNITY CHAT/HELPDESK --
def community_chat_page():
    st.header("🌐 " + L("whatsapp"))
    st.markdown("[Join WhatsApp Community](https://chat.whatsapp.com/XXXXX)")
    st.markdown("Ask, share, and get help from fellow MSMEs and experts!")
    st.markdown("---")
    st.header("💬 Message Board")
    messages = load_datafile("data/community_messages.json", [])
    msg = st.text_input("Your message")
    if st.button("Post Message"):
        if msg and st.session_state["user_id"]:
            messages.append({"user": st.session_state["user_id"], "msg": msg, "time": datetime.now().isoformat()})
            save_datafile("data/community_messages.json", messages)
    for m in messages[::-1][:10]:
        st.markdown(f"{m['user']}: {m['msg']}  \n<sub>{m['time'][:16].replace('T',' ')}</sub>", unsafe_allow_html=True)
    back_button("home")

# --- FAQ BOT ---
def faq_bot():
    st.header(L("faq_title"))
    faqs = {
        "English": {
            "how to submit waste": "Click 'Submit Waste', fill the form and submit.",
            "how to get certificate": "Contribute over 50kg and download from dashboard.",
            "how to register interest": "Go to 'Register Interest' and fill the form.",
            "how to contact buyer": "Use the message board on the listing.",
            "how to add video": "Go to 'Add Your Story/Video' and submit your video link.",
            "how to join batch pickup": "On a listing, click 'Join Batch Pickup' to pool with others nearby.",
            "how to get early adopter badge": "Sign up and submit waste before 2025-12-31.",
            "how to report spam": "Click 'Report Listing' and our admins will review it."
        },
        "தமிழ்": {
            "waste submit எப்படி": "‘Submit Waste’ கிளிக் செய்து, படிவத்தை நிரப்பி சமர்ப்பிக்கவும்.",
            "certificate எப்படிப்பெறுவது": "50kg-க்கும் மேலாக பங்களித்து dashboard-ல் பதிவிறக்கவும்.",
            "interest பதிவு எப்படி": "‘Register Interest’ சென்று படிவத்தை நிரப்பவும்.",
            "buyer தொடர்பு எப்படி": "Listing-ல் Message Board பயன்படுத்தவும்.",
            "video எப்படி சேர்க்க": "‘Add Your Story/Video’ சென்று video link ஐ சமர்ப்பிக்கவும்.",
        },
        "हिन्दी": {
            "अपशिष्ट कैसे जमा करें": "‘Submit Waste’ पर क्लिक करें, फॉर्म भरें और सबमिट करें.",
            "प्रमाणपत्र कैसे प्राप्त करें": "50kg से अधिक योगदान करें और डैशबोर्ड से डाउनलोड करें.",
            "रुचि कैसे दर्ज करें": "‘Register Interest’ पर जाएँ और फ़ॉर्म भरें.",
        }
    }
    q = st.text_input(L("ask_question"))
    if st.button(L("ask")):
        faqd = faqs.get(st.session_state["lang"], faqs["English"])
        best_match, score = process.extractOne(q.lower().strip(), faqd.keys())
        if score > 70:
            st.info(faqd[best_match])
        else:
            st.info({
                "English": "Sorry, I can't answer that yet!",
                "தமிழ்": "மன்னிக்கவும், பதில் இல்லை!",
                "हिन्दी": "माफ़ कीजिए, इसका उत्तर नहीं है!"
            }[st.session_state["lang"]])
    back_button("home")

# --- HOWTO PAGE ---
def howto_page():
    st.header(L("howto"))
    st.info(L("howto_desc"))
    st.video("https://www.youtube.com/embed/tsuB5Gv3yEk")
    st.markdown("[Join WhatsApp Community](https://chat.whatsapp.com/XXXXX)")
    st.markdown("Early Adopter? You may get a special badge on your profile!")
    back_button("landing")

def privacy_policy_page():
    st.header(L("privacy"))
    st.write(L("privacy_summary"))
    st.write("For more info, contact admin@bioloop.in")
    back_button("landing")

# --- MAIN PAGE DICT ---
pages = {
    "landing": landing_page,
    "login": login_page,
    "signup": signup_page,
    "home": home_page,
    "admin": admin_panel,
    "faq": faq_bot,
    "howto": howto_page,
    "privacy": privacy_policy_page,
    "privacy_settings": privacy_settings,
    "chat": community_chat_page,
    # Part 3 pages (submit, browse, dashboard, export, etc.) come next
}
import streamlit as st
from bioloop_core import *
from datetime import datetime
import base64
import io
import pandas as pd
from fpdf import FPDF
# --- WASTE SUBMISSION ---
def submit_page():
    st.markdown(f"<div class='biol-title'>{L('header')}</div>", unsafe_allow_html=True)
    material_input = st.text_input(L("material"))
    material = None
    if material_input:
        match = process.extractOne(material_input.lower(), reuse_db.keys())
        if match:
            material = match[0]
            st.info(f"{L('matched')}: {material.title()} ({match[1]}%)")
    uploaded_img = st.file_uploader(L("upload_image"), type=["png", "jpg", "jpeg"])
    img_b64 = ""
    if uploaded_img:
        img_bytes = uploaded_img.read()
        img_b64 = base64.b64encode(img_bytes).decode()
    if material:
        quantity = st.number_input(L("quantity"), min_value=1)
        location = st.text_input(L("location"))
        contact = st.text_input(L("contact"))
        quality = st.selectbox(L("quality"), [L("clean"), L("mixed"), L("contaminated")])
        users = load_users()
        show_contact = st.checkbox(L("show_contact"), value=users[st.session_state["user_id"]].get("privacy", True))
        if st.button(L("submit")):
            valid = re.match(r"[^@]+@[^@]+\.[^@]+", contact) or re.match(r"\d{10}", contact)
            if not valid:
                st.warning(L("invalid_contact"))
            else:
                lat, lon = None, None
                try:
                    loc = geolocator.geocode(location)
                    if loc: lat, lon = loc.latitude, loc.longitude
                except: pass
                entry = {
                    "material": material,
                    "quantity": quantity,
                    "location": location,
                    "contact": contact if show_contact else "Hidden",
                    "lat": lat, "lon": lon,
                    "quality": quality,
                    "image": img_b64,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": st.session_state["user_id"],
                    "show_contact": show_contact
                }
                entry["trace_id"] = generate_trace_hash(entry)
                data = load_data()
                data.append(entry)
                save_data(data)
                st.success(L("success"))
                st.session_state["page"] = "home"
    back_button("home")

# --- BROWSE WASTE LISTINGS (MARKETPLACE) with Batch Pickup & Reporting & Ratings ---
def browse_page():
    st.header(L("browse_waste"))
    data = load_data()
    df = pd.DataFrame(data)
    mat = st.selectbox(L("filter_material"), [L("all")] + list(reuse_db.keys()))
    loc = st.text_input(L("filter_location"))
    filtered = df
    if mat and mat != L("all"):
        filtered = filtered[filtered["material"] == mat]
    if loc:
        filtered = filtered[filtered["location"].str.contains(loc, case=False, na=False)]
    if filtered.empty:
        st.info(L("no_data"))
    else:
        for i, row in filtered.iterrows():
            st.markdown(f"### {row['material'].title()} — {row['quantity']} {L('kg_week')}")
            if row.get("image"):
                st.image(base64.b64decode(row["image"]), width=200)
            st.write(f"{L('location')}:** {row['location']}")
            st.write(f"{L('quality')}:** {row['quality']}")
            st.write(f"{L('contact')}:** {row['contact'] if row.get('show_contact', True) else 'Hidden'}")
            st.write(f"{L('rating')}:** {get_user_rating(row['user_id'])} ⭐")
            st.write(f"ID: {row['trace_id'][:8]}")
            st.write(f"{L('rate')}:")
            user_rating = st.slider(L("rating"), 1, 5, 3, key=f"rate-{i}")
            if st.button(L("submit_rating"), key=f"submitrate-{i}"):
                ratings = load_datafile(RATINGS_FILE, [])
                ratings.append({"user": row["user_id"], "rating": user_rating, "by": st.session_state["user_id"], "time": datetime.now().isoformat()})
                save_datafile(RATINGS_FILE, ratings)
                st.success(L("thanks_rating"))
            st.write(f"{L('batch_pickup')}:")
            if st.button(L("batch_pickup"), key=f"batch-{i}"):
                join_batch_pickup(row['material'], row['location'], st.session_state['user_id'])
            if st.button(L("report_listing"), key=f"rep-{i}"):
                report_listing(row['trace_id'])
            st.markdown("---")
    back_button("home")

def join_batch_pickup(material, location, user_id):
    batches = load_datafile(BATCHES_FILE, [])
    for b in batches:
        if b["material"] == material and b["location"] == location:
            if user_id in b["users"]:
                st.info(L("already_joined"))
                return
            else:
                b["users"].append(user_id)
                save_datafile(BATCHES_FILE, batches)
                st.success(L("joined_batch"))
                add_notification(user_id, f"Batch pickup joined for {material} at {location}")
                return
    batches.append({"material": material, "location": location, "users": [user_id], "created": datetime.now().isoformat()})
    save_datafile(BATCHES_FILE, batches)
    st.success(L("joined_batch"))
    add_notification(user_id, f"Batch pickup created for {material} at {location}")

def report_listing(trace_id):
    reports = load_datafile(REPORTS_FILE, [])
    if any(r["trace_id"] == trace_id and r["reporter"] == st.session_state["user_id"] for r in reports):
        st.info(L("already_reported"))
        return
    reason = st.text_area("Describe the issue (spam, fake info, etc.)", key=f"repmsg-{trace_id}")
    if st.button("Submit Report", key=f"repsub-{trace_id}"):
        reports.append({
            "trace_id": trace_id,
            "reporter": st.session_state["user_id"],
            "reason": reason,
            "time": datetime.now().isoformat()
        })
        save_datafile(REPORTS_FILE, reports)
        st.success(L("reported"))
        add_notification("admin@bioloop.in", f"Listing {trace_id} reported by {st.session_state['user_id']}")

# --- DASHBOARD (MY SUBMISSIONS) with Progress Bar/BADGES ---
def dashboard_page():
    st.header(L("my_submissions"))
    data = load_data()
    mydata = [d for d in data if d["user_id"] == st.session_state["user_id"]]
    total = sum(d["quantity"] for d in mydata)
    st.progress(min(total/100,1.0), text=f"{L('progress')}: {total} kg — {L('next_badge')}: 20/50/100 kg")
    if total >= 100:
        st.success(L("badge_gold"))
    elif total >= 50:
        st.info(L("badge_silver"))
    elif total >= 20:
        st.info(L("badge_bronze"))
    if st.session_state.get("early"):
        st.info(L("early_adopter"))
    if not mydata:
        st.info(L("no_entries"))
    else:
        for i, row in enumerate(mydata[::-1]):
            st.markdown(f"### {row['material'].title()} — {row['quantity']} {L('kg_week')}")
            st.write(f"{L('location')}:** {row['location']}")
            if row.get("image"):
                st.image(base64.b64decode(row["image"]), width=200)
            st.write(f"{L('quality')}:** {row['quality']}")
            st.write(f"ID: {row['trace_id'][:8]}")
            if st.button("❌ " + L("delete_success"), key=f"del-{i}"):
                data.remove(row)
                save_data(data)
                st.success(L("delete_success"))
    st.button("Privacy Settings", on_click=go, args=("privacy_settings",), use_container_width=True)
    back_button("home")

# --- INTEREST REGISTRATION ---
def interest_registration():
    st.subheader(L("register_interest"))
    mat = st.selectbox(L("interest_material"), list(reuse_db.keys()))
    loc = st.text_input(L("interest_location"))
    if st.button(L("register_interest")):
        interests = load_datafile(INTERESTS_FILE, [])
        interests.append({
            "user": st.session_state["user_id"],
            "material": mat,
            "location": loc,
            "time": datetime.now().isoformat()
        })
        save_datafile(INTERESTS_FILE, interests)
        st.success(L("interest_registered"))
        add_notification(st.session_state["user_id"], f"Interest registered for {mat} at {loc}")
    back_button("home")

# --- NOTIFICATIONS PAGE ---
def notifications_page():
    st.header(L("notifications"))
    notifs = load_datafile(NOTIFICATIONS_FILE, [])
    user_notifs = [n for n in notifs if n["user"] == st.session_state["user_id"]]
    if not user_notifs:
        st.info(L("no_notifications"))
    else:
        for n in user_notifs[::-1]:
            st.success(n["msg"])
    back_button("home")

# --- ANALYTICS / IMPACT DASHBOARD ---
def analytics_page():
    st.subheader(L("impact_dash"))
    data = load_data()
    df = pd.DataFrame(data)
    if not df.empty and "lat" in df and "lon" in df:
        st.map(df[["lat", "lon"]].dropna())
        leader = df.groupby("user_id")["quantity"].sum().sort_values(ascending=False).head(5)
        st.write(L("leaderboard"))
        for idx, (user, amt) in enumerate(leader.items(), 1):
            badge = ""
            if idx == 1: badge = L("badge_gold")
            elif idx == 2: badge = L("badge_silver")
            elif idx == 3: badge = L("badge_bronze")
            st.write(f"{idx}. {user} — {amt} kg/week {badge}")
        user_amt = leader.get(st.session_state["user_id"], 0)
        if user_amt >= 100:
            st.success(L("badge_gold"))
        elif user_amt >= 50:
            st.info(L("badge_silver"))
        elif user_amt >= 20:
            st.info(L("badge_bronze"))
    else:
        st.info(L("no_data"))
    back_button("home")

# --- MICRO UNIT PLANNER ---
def microplanner_page():
    st.header(L("microplanner"))
    mat = st.selectbox(L("material"), list(micro_units.keys()))
    unit = micro_units[mat]
    st.write(f"Unit: {unit['unit']}")
    st.write(f"Tool/Cost: {unit['tool']}")
    st.write(f"ROI: {unit['roi']}")
    st.write(f"Sample Reusers: {', '.join(reuse_db[mat])}")
    st.info("This is a sample micro-unit business plan. Adapt as per your needs.")
    back_button("home")

# --- EXPORT DATA ---
def export_page():
    st.header(L("export"))
    data = load_data()
    df = pd.DataFrame(data)
    if not df.empty:
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button(L("download_csv"), buf.getvalue(), "waste_data.csv", "text/csv")
    else:
        st.info(L("no_data"))
    back_button("home")

# --- CERTIFICATE GENERATION ---
def generate_certificate(user_id, total_waste):
    if total_waste >= 50:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="BioLoop Green MSME Certificate", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Awarded to {user_id}", ln=True, align='C')
        pdf.cell(200, 10, txt=f"For recycling {total_waste} kg waste", ln=True, align='C')
        buf = io.BytesIO()
        pdf.output(buf)
        st.download_button(L("download_cert"), buf.getvalue(), "certificate.pdf", "application/pdf")

def certificate_page():
    st.header(L("download_cert"))
    data = load_data()
    df = pd.DataFrame(data)
    total = df[df["user_id"] == st.session_state["user_id"]]["quantity"].sum() if not df.empty else 0
    generate_certificate(st.session_state["user_id"], total)
    back_button("home")

# --- VIDEO/STORY SUBMISSION ---
def video_stories():
    st.header(L("add_story_video"))
    stories = load_datafile(STORIES_FILE, [])
    title = st.text_input(L("story_title"))
    desc = st.text_area(L("story_desc"))
    youtube = st.text_input(L("video_url"), placeholder="https://www.youtube.com/embed/...")
    if st.button(L("submit_video")):
        if youtube:
            stories.append({
                "user": st.session_state["user_id"],
                "title": title,
                "desc": desc,
                "youtube": youtube,
                "time": datetime.now().isoformat()
            })
            save_datafile(STORIES_FILE, stories)
            st.success(L("video_submitted"))
    back_button("home")

def show_video_stories():
    st.header(L("video_section"))
    stories = load_datafile(STORIES_FILE, [])
    if not stories:
        st.info(L("no_video_stories"))
    for s in stories[::-1]:
        st.markdown(f"### {s['title'] if s['title'] else '(No Title)'}")
        st.write(f"by {s['user']} at {s['time'][:16].replace('T',' ')}")
        if s.get("youtube"):
            st.video(s["youtube"])
        if s.get("desc"):
            st.write(s["desc"])
        st.markdown("---")
    back_button("home")

# --- MAIN LOOP ---
def main():
    pages = {
        "landing": landing_page,
        "login": login_page,
        "signup": signup_page,
        "home": home_page,
        "admin": admin_panel,
        "faq": faq_bot,
        "howto": howto_page,
        "privacy": privacy_policy_page,
        "privacy_settings": privacy_settings,
        "chat": community_chat_page,
        "submit": submit_page,
        "browse": browse_page,
        "dashboard": dashboard_page,
        "export": export_page,
        "analytics": analytics_page,
        "microplanner": microplanner_page,
        "certificate": certificate_page,
        "interest": interest_registration,
        "notifications": notifications_page,
        "addvideo": video_stories,
        "videos": show_video_stories,
    }
    page = st.session_state.get("page", "landing")
    if page in pages:
        pages[page]()
    else:
        landing_page()

if _name_ == "_main_":
    main()
