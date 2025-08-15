import streamlit as st
import json, os, re, hashlib, base64, io
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from fpdf import FPDF
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF

# --- SESSION STATE & SETUP ---
st.set_page_config(page_title="BioLoop", page_icon="♻", layout="centered")
for k, v in [
    ("authenticated", False), ("user_id", ""), ("page", "landing"),
    ("lang", "English"), ("verified", False), ("prev_page", "landing")
]: st.session_state.setdefault(k, v)

# --- FILES & DIRS ---
DATA_FILE = "data/waste_profiles.json"
USER_FILE = "data/users.json"
INTERESTS_FILE = "data/interests.json"
MESSAGES_DIR = "data/messages/"
STORIES_FILE = "data/success_stories.json"
RATINGS_FILE = "data/ratings.json"
os.makedirs("data", exist_ok=True)
os.makedirs(MESSAGES_DIR, exist_ok=True)
for f in [DATA_FILE, USER_FILE, INTERESTS_FILE, STORIES_FILE, RATINGS_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump([] if f.endswith(".json") else {}, file)

# --- LABELS (English, Tamil, Hindi) ---
labels = {
    "English": {
        "submit": "Submit Waste", "material": "Material Type", "login": "MSME Login", "password": "Password",
        "signup": "Sign Up", "location": "Location", "quantity": "Quantity (kg/week)", "invalid_login": "🔐 Invalid login.",
        "header": "Submit Your Waste", "contact": "Contact Info", "quality": "Quality", "public_contact": "Show contact publicly",
        "account_created": "✅ Account created! Please log in.", "duplicate_id": "🚫 ID already exists.",
        "missing_fields": "Please fill both fields.", "logout": "Logout", "back": "Back", "success": "Submission saved.",
        "upload_image": "Upload a picture of the waste", "matched": "Matched",
        "go_home": "Go Home", "invalid_contact": "Invalid contact.",
        "filter_material": "Filter by Material", "filter_location": "Filter by Location",
        "browse_waste": "Browse Waste Listings", "all": "All", "kg_week": "kg/week",
        "clean": "Clean", "mixed": "Mixed", "contaminated": "Contaminated",
        "my_submissions": "My Submissions", "analytics": "Analytics", "microplanner": "Micro-unit Planner", "export": "Export Data",
        "admin_panel": "Admin Panel", "top_materials": "Top Submitted Materials",
        "no_data": "No data found yet.", "no_entries": "You haven't submitted any waste yet.",
        "delete_success": "✅ Submission deleted successfully.", "download_csv": "Download CSV",
        "browse": "Browse Materials", "otp": "Enter OTP sent to your email (1234)",
        "verify": "Verify", "verified": "Verified MSME 🟢", "not_verified": "Not Verified 🔴",
        "rate": "Rate this user", "rating": "Rating", "submit_rating": "Submit Rating", "thanks_rating": "Thanks for rating!",
        "success_story": "🌟 Success Stories", "share_story": "Share Your Story", "submit_story": "Submit Story",
        "story_submitted": "Story submitted!", "impact_dash": "🌏 Impact Dashboard",
        "register_interest": "🔔 Register Interest", "interest_material": "Material", "interest_location": "Preferred Location",
        "interest_registered": "Interest registered! You'll see matches on your dashboard.",
        "your_interests": "Your Registered Interests", "msg": "💬 Messages", "send": "Send",
        "howto": "🎓 How-to Videos & Support", "ai_help": "🤖 Need help? Ask our FAQ bot below:",
        "download_cert": "🎓 Download Green MSME Certificate",
        "profile": "Profile", "leaderboard": "🏆 Top Contributors", "badge_gold": "🥇 Gold Contributor",
        "badge_silver": "🥈 Silver Contributor", "badge_bronze": "🥉 Bronze Contributor",
        "add_story_video": "Add Your Story/Video", "video_url": "Paste YouTube Link of Your Story/Innovation",
        "story_title": "Story Title", "story_desc": "Write your story/impact here", "submit_video": "Submit Video Story",
        "video_submitted": "Video/Story submitted!", "faq_title": "❓ MSME FAQ Bot", "ask_question": "Ask your question",
        "ask": "Ask", "video_section": "🎬 Community Videos & Stories", "no_video_stories": "No video stories yet."
    },
    "தமிழ்": {
        "submit": "சமர்ப்பி", "material": "வஸ்து வகை", "login": "எம்.எஸ்.எம்.இ நுழைவு", "password": "கடவுச்சொல்",
        "signup": "பதிவு செய்", "location": "இடம்", "quantity": "அளவு (கி.கி/வாரம்)", "invalid_login": "🔐 தவறான நுழைவு.",
        "header": "உங்கள் கழிவுகளை சமர்ப்பிக்கவும்", "contact": "தொடர்பு தகவல்", "quality": "தரம்", "public_contact": "தொடர்பை பொதுவாக காட்டவும்",
        "account_created": "✅ கணக்கு உருவாக்கப்பட்டது! தயவுசெய்து நுழைக.", "duplicate_id": "🚫 ஐடி ஏற்கனவே உள்ளது.",
        "missing_fields": "உருப்படிகளை நிரப்பவும்.", "logout": "வெளியேறு", "back": "பின்னால்", "success": "சமர்ப்பிப்பு சேமிக்கப்பட்டது.",
        "upload_image": "கழிவின் படத்தை பதிவேற்றவும்", "matched": "பொருந்தியது",
        "go_home": "முகப்புக்கு செல்", "invalid_contact": "தவறான தொடர்பு.",
        "filter_material": "வஸ்து மூலம் வடிகட்டவும்", "filter_location": "இடம் மூலம் வடிகட்டவும்",
        "browse_waste": "கழிவுகளை தேடுங்கள்", "all": "அனைத்தும்", "kg_week": "கி.கி/வாரம்",
        "clean": "தூய்மை", "mixed": "கலப்பு", "contaminated": "மாசுபட்டது",
        "my_submissions": "என் சமர்ப்பிப்புகள்", "analytics": "புள்ளிவிவரங்கள்", "microplanner": "மைக்ரோ-யூனிட் திட்டம்", "export": "தரவு ஏற்றுமதி",
        "admin_panel": "நிர்வாகப் பலகம்", "top_materials": "உச்ச சமர்ப்பிக்கப்பட்ட பொருட்கள்",
        "no_data": "தரவு இல்லை.", "no_entries": "நீங்கள் எந்த கழிவையும் சமர்ப்பிக்கவில்லை.",
        "delete_success": "✅ சமர்ப்பிப்பு நீக்கப்பட்டது.", "download_csv": "CSV பதிவிறக்கு",
        "browse": "வஸ்துக்களை தேடுங்கள்", "otp": "உங்கள் மின்னஞ்சலில் வந்த OTP ஐ உள்ளிடவும் (1234)",
        "verify": "சரிபார்க்கவும்", "verified": "சரிபார்க்கப்பட்ட MSME 🟢", "not_verified": "சரிபார்க்கப்படவில்லை 🔴",
        "rate": "இந்த பயனாளரை மதிப்பிடு", "rating": "மதிப்பீடு", "submit_rating": "மதிப்பீட்டை சமர்ப்பி", "thanks_rating": "மதிப்பீட்டுக்கு நன்றி!",
        "success_story": "🌟 வெற்றிக் கதைகள்", "share_story": "உங்கள் கதையை பகிருங்கள்", "submit_story": "கதை சமர்ப்பி",
        "story_submitted": "கதை சமர்ப்பிக்கப்பட்டது!", "impact_dash": "🌏 தாக்கம் டாஷ்போர்டு",
        "register_interest": "🔔 ஆர்வத்தை பதிவு செய்", "interest_material": "வஸ்து", "interest_location": "விருப்ப இடம்",
        "interest_registered": "ஆர்வம் பதிவு செய்யப்பட்டது! நீங்கள் டாஷ்போர்டில் பொருத்தங்களை பார்க்கலாம்.",
        "your_interests": "உங்கள் பதிவுசெய்யப்பட்ட ஆர்வங்கள்", "msg": "💬 செய்திகள்", "send": "அனுப்பு",
        "howto": "🎓 வீடியோ மற்றும் உதவி", "ai_help": "🤖 உதவி வேண்டுமா? கீழே FAQ பாட்டில் கேளுங்கள்:",
        "download_cert": "🎓 பசுமை MSME சான்றிதழ் பதிவிறக்கு",
        "profile": "சுயவிவரம்", "leaderboard": "🏆 சிறந்த பங்களிப்பாளர்கள்", "badge_gold": "🥇 தங்கம் பங்களிப்பாளர்",
        "badge_silver": "🥈 வெள்ளி பங்களிப்பாளர்", "badge_bronze": "🥉 வெண்கலம் பங்களிப்பாளர்",
        "add_story_video": "உங்கள் கதையையும்/வீடியோகையும் சேர்க்கவும்", "video_url": "உங்கள் YouTube வீடியோ லிங்க்",
        "story_title": "கதையின் தலைப்பு", "story_desc": "உங்கள் கதை/விளைவுகளை எழுதவும்", "submit_video": "வீடியோ/கதை சமர்ப்பி",
        "video_submitted": "வீடியோ/கதை சமர்ப்பிக்கப்பட்டது!", "faq_title": "❓ MSME கேள்வி பாட்டு", "ask_question": "உங்கள் கேள்வியை எழுதவும்",
        "ask": "கேள்", "video_section": "🎬 சமூகவீடியோக்கள் மற்றும் கதைகள்", "no_video_stories": "இப்போது வீடியோ கதைகள் இல்லை."
    },
    "हिन्दी": {
        "submit": "जमा करें", "material": "सामग्री प्रकार", "login": "एमएसएमई लॉगिन", "password": "पासवर्ड",
        "signup": "साइन अप", "location": "स्थान", "quantity": "मात्रा (किग्रा/सप्ताह)", "invalid_login": "🔐 अमान्य लॉगिन।",
        "header": "अपना कचरा जमा करें", "contact": "संपर्क जानकारी", "quality": "गुणवत्ता", "public_contact": "सार्वजनिक रूप से संपर्क दिखाएँ",
        "account_created": "✅ खाता बनाया गया! कृपया लॉग इन करें।", "duplicate_id": "🚫 आईडी पहले से मौजूद है।",
        "missing_fields": "कृपया सभी फ़ील्ड भरें।", "logout": "लॉगआउट", "back": "पीछे", "success": "जमा सफल।",
        "upload_image": "कचरे की तस्वीर अपलोड करें", "matched": "मेल खाया",
        "go_home": "मुखपृष्ठ पर जाएं", "invalid_contact": "अमान्य संपर्क।",
        "filter_material": "सामग्री द्वारा छाँटें", "filter_location": "स्थान द्वारा छाँटें",
        "browse_waste": "कचरा खोजें", "all": "सभी", "kg_week": "किग्रा/सप्ताह",
        "clean": "साफ़", "mixed": "मिश्रित", "contaminated": "प्रदूषित",
        "my_submissions": "मेरी प्रविष्टियाँ", "analytics": "विश्लेषण", "microplanner": "माइक्रो-यूनिट योजनाकार", "export": "डेटा निर्यात",
        "admin_panel": "प्रशासन पैनल", "top_materials": "शीर्ष जमा की गई सामग्री",
        "no_data": "कोई डेटा नहीं।", "no_entries": "आपने अभी तक कोई कचरा जमा नहीं किया है।",
        "delete_success": "✅ प्रविष्टि सफलतापूर्वक हटाई गई।", "download_csv": "CSV डाउनलोड करें",
        "browse": "सामग्री ब्राउज़ करें", "otp": "अपने ईमेल पर भेजा गया OTP दर्ज करें (1234)",
        "verify": "सत्यापित करें", "verified": "सत्यापित MSME 🟢", "not_verified": "असत्यापित 🔴",
        "rate": "इस उपयोगकर्ता को रेट करें", "rating": "रेटिंग", "submit_rating": "रेटिंग सबमिट करें", "thanks_rating": "रेटिंग के लिए धन्यवाद!",
        "success_story": "🌟 सफलता की कहानियाँ", "share_story": "अपनी कहानी साझा करें", "submit_story": "कहानी जमा करें",
        "story_submitted": "कहानी जमा हो गई!", "impact_dash": "🌏 प्रभाव डैशबोर्ड",
        "register_interest": "🔔 रुचि दर्ज करें", "interest_material": "सामग्री", "interest_location": "पसंदीदा स्थान",
        "interest_registered": "रुचि दर्ज हो गई! आपको डैशबोर्ड पर मिलान दिखाई देगा।",
        "your_interests": "आपकी पंजीकृत रुचियाँ", "msg": "💬 संदेश", "send": "भेजें",
        "howto": "🎓 वीडियो और सहायता", "ai_help": "🤖 सहायता चाहिए? नीचे FAQ बॉट में पूछें:",
        "download_cert": "🎓 ग्रीन MSME प्रमाणपत्र डाउनलोड करें",
        "profile": "प्रोफ़ाइल", "leaderboard": "🏆 शीर्ष योगदानकर्ता", "badge_gold": "🥇 गोल्ड योगदानकर्ता",
        "badge_silver": "🥈 सिल्वर योगदानकर्ता", "badge_bronze": "🥉 ब्रॉन्ज योगदानकर्ता",
        "add_story_video": "अपनी कहानी/वीडियो जोड़ें", "video_url": "अपनी कहानी/नवाचार का YouTube लिंक डालें",
        "story_title": "कहानी का शीर्षक", "story_desc": "यहाँ अपनी कहानी/प्रभाव लिखें", "submit_video": "वीडियो/कहानी जमा करें",
        "video_submitted": "वीडियो/कहानी जमा हो गई!", "faq_title": "❓ MSME FAQ बॉट", "ask_question": "अपना प्रश्न पूछें",
        "ask": "पूछें", "video_section": "🎬 सामुदायिक वीडियो और कहानियाँ", "no_video_stories": "अभी कोई वीडियो कहानी नहीं है।"
    }
}
def L(key): return labels[st.session_state["lang"]].get(key, key)

# --- UTILS ---
def load_users():
    with open(USER_FILE) as f:
        users = json.load(f)
        return users if isinstance(users, dict) else {}
def save_users(users):
    with open(USER_FILE, "w") as f: json.dump(users, f, indent=2)
def load_datafile(path, default=None):
    if not os.path.exists(path): return default
    with open(path) as f:
        try: return json.load(f)
        except: return default
def save_datafile(path, data):
    with open(path, "w") as f: json.dump(data, f, indent=2)
def load_data(): return load_datafile(DATA_FILE, [])
def save_data(data): save_datafile(DATA_FILE, data)

# --- NAVIGATION & LANG SELECTORS ---
def go(page):
    st.session_state["prev_page"] = st.session_state.get("page", "landing")
    st.session_state["page"] = page

def back_button(default="landing"):
    prev = st.session_state.get("prev_page", default)
    if st.button("⬅️ " + L("back")):
        st.session_state["page"] = prev
        st.experimental_rerun()

def lang_selector():
    lang = st.selectbox("🌍", list(labels.keys()),
                        index=list(labels.keys()).index(st.session_state["lang"]))
    st.session_state["lang"] = lang

def verify_user():
    if not st.session_state.get("verified"):
        otp = st.text_input(L("otp"))
        if st.button(L("verify")):
            if otp == "1234":
                st.session_state["verified"] = True
                st.success(L("verified"))
            else:
                st.error("Incorrect OTP.")

def user_badge(user_id):
    if user_id == "admin@bioloop.in":
        return "🛡 Admin"
    if st.session_state.get("verified"):
        return L("verified")
    return L("not_verified")

# --- Multilingual FAQ BOT ---
def faq_bot():
    st.header(L("faq_title"))
    faqs = {
        "English": {
            "how to submit waste": "Click 'Submit Waste', fill the form and submit.",
            "how to get certificate": "Contribute over 50kg and download from dashboard.",
            "how to register interest": "Go to 'Register Interest' and fill the form.",
            "how to contact buyer": "Use the message board on the listing.",
            "how to add video": "Go to 'Add Your Story/Video' and submit your video link."
        },
        "தமிழ்": {
            "கழிவை சமர்ப்பிப்பது எப்படி": "'Submit Waste' கிளிக் செய்து படிவத்தை நிரப்பி சமர்ப்பிக்கவும்.",
            "சான்றிதழ் பெற எப்படி": "50 கிலோவுக்கு மேல் பங்களிப்பில் 'Dashboard' இல் பதிவிறக்கம் செய்யவும்.",
            "ஆர்வம் பதிவு செய்வது எப்படி": "'Register Interest' சென்று படிவத்தை பூர்த்தி செய்யவும்.",
            "வாங்குபவரை தொடர்பு கொள்ளுவது எப்படி": "பதிவில் உள்ள 'message board' பயன்படுத்தவும்.",
            "வீடியோ சேர்க்க": "'Add Your Story/Video' சென்று உங்கள் YouTube லிங்கை சமர்ப்பிக்கவும்."
        },
        "हिन्दी": {
            "कचरा कैसे जमा करें": "'Submit Waste' पर क्लिक करें, फॉर्म भरें और जमा करें।",
            "प्रमाणपत्र कैसे प्राप्त करें": "50किग्रा से अधिक योगदान करें और डैशबोर्ड से डाउनलोड करें।",
            "रुचि दर्ज कैसे करें": "'Register Interest' जाएं और फॉर्म भरें।",
            "खरीदार से संपर्क कैसे करें": "लिस्टिंग में 'message board' का उपयोग करें।",
            "वीडियो कैसे जोड़ें": "'Add Your Story/Video' पर जाकर अपना YouTube लिंक सबमिट करें।"
        }
    }
    q = st.text_input(L("ask_question"))
    if st.button(L("ask")):
        answer = faqs[st.session_state["lang"]].get(q.lower().strip(), {
            "English": "Sorry, I can't answer that yet!",
            "தமிழ்": "மன்னிக்கவும், இதற்கு பதில் இல்லை!",
            "हिन्दी": "माफ़ कीजिए, इसका उत्तर मेरे पास नहीं है!"
        }[st.session_state["lang"]])
        st.info(answer)

# --- COMMUNITY VIDEO/STORY SUBMISSION ---
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
            st.experimental_rerun()
    back_button("home")

def show_video_stories():
    st.header(L("video_section"))
    stories = load_datafile(STORIES_FILE, [])
    if not stories:
        st.info(L("no_video_stories"))
    for s in stories[::-1]:
        st.markdown(f"### {s['title'] if s['title'] else '(No Title)'}")
        st.write(f"by **{s['user']}** at {s['time'][:16].replace('T',' ')}")
        if s.get("youtube"):
            st.video(s["youtube"])
        if s.get("desc"):
            st.write(s["desc"])
        st.markdown("---")
    back_button("home")
# --- CIRCULAR ECONOMY DB, MICRO UNITS, CARBON FACTORS, GEOLOCATOR ---
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
geolocator = Nominatim(user_agent="bioloop")

def generate_trace_hash(entry):
    raw = f"{entry['material']}{entry['quantity']}{entry['location']}_{entry['timestamp']}"
    return hashlib.sha256(raw.encode()).hexdigest()

# --- LOGIN/SIGNUP/HOME PAGES ---
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

def login_page():
    st.markdown(f"<div class='biol-title'>{L('login')}</div>", unsafe_allow_html=True)
    lang_selector()
    users = load_users()
    user = st.text_input("MSME ID")
    pw = st.text_input(L("password"), type="password")
    if st.button(L("login")):
        if user in users and users[user] == pw:
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user
            st.session_state["page"] = "home"
            st.experimental_rerun()
        else:
            st.error(L("invalid_login"))
    back_button("landing")

def signup_page():
    st.markdown(f"<div class='biol-title'>{L('signup')}</div>", unsafe_allow_html=True)
    lang_selector()
    users = load_users()
    new_id = st.text_input("Choose MSME ID")
    new_pw = st.text_input("Choose Password", type="password")
    if st.button(L("signup")):
        if new_id in users:
            st.error(L("duplicate_id"))
        elif not new_id or not new_pw:
            st.warning(L("missing_fields"))
        else:
            users[new_id] = new_pw
            save_users(users)
            st.success(L("account_created"))
            st.button(L("login"), on_click=go, args=("login",))
    back_button("landing")

def home_page():
    st.markdown(f"<div class='biol-title'>Hi, {st.session_state['user_id']}! {user_badge(st.session_state['user_id'])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='biol-sub'>{L('browse')}</div>", unsafe_allow_html=True)
    if not st.session_state.get("verified"):
        verify_user()
    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 " + L("submit"), on_click=go, args=("submit",), use_container_width=True)
        st.button("👤 " + L("my_submissions"), on_click=go, args=("dashboard",), use_container_width=True)
        st.button(L("register_interest"), on_click=go, args=("interest",), use_container_width=True)
        st.button("📈 " + L("analytics"), on_click=go, args=("analytics",), use_container_width=True)
    with col2:
        st.button("🔍 " + L("browse"), on_click=go, args=("browse",), use_container_width=True)
        st.button("🏭 " + L("microplanner"), on_click=go, args=("microplanner",), use_container_width=True)
        st.button("📤 " + L("export"), on_click=go, args=("export",), use_container_width=True)
        st.button(L("faq_title"), on_click=go, args=("faq",), use_container_width=True)
        st.button(L("add_story_video"), on_click=go, args=("addvideo",), use_container_width=True)
        st.button(L("video_section"), on_click=go, args=("videos",), use_container_width=True)
    st.button(L("logout"), on_click=logout, use_container_width=True)
    back_button("landing")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = ""
    st.session_state["page"] = "landing"
    st.experimental_rerun()

# --- SUBMIT WASTE ---
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
        show_contact = st.checkbox(L("public_contact"), value=True)
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
                    "user_id": st.session_state["user_id"]
                }
                entry["trace_id"] = generate_trace_hash(entry)
                data = load_data()
                data.append(entry)
                save_data(data)
                st.success(L("success"))
                st.button(L("go_home"), on_click=go, args=("home",))
                return
    back_button("home")

# --- BROWSE WASTE LISTINGS (MARKETPLACE) ---
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
            st.write(f"**{L('location')}:** {row['location']}")
            st.write(f"**{L('quality')}:** {row['quality']}")
            st.write(f"**{L('contact')}:** {row['contact']}")
            st.write(f"**{L('rating')}:** {get_user_rating(row['user_id'])} ⭐")
            st.write(f"**ID:** {row['trace_id'][:8]}")
            st.markdown("---")
    back_button("home")

# --- DASHBOARD (MY SUBMISSIONS) ---
def dashboard_page():
    st.header(L("my_submissions"))
    data = load_data()
    mydata = [d for d in data if d["user_id"] == st.session_state["user_id"]]
    if not mydata:
        st.info(L("no_entries"))
    else:
        for i, row in enumerate(mydata[::-1]):
            st.markdown(f"### {row['material'].title()} — {row['quantity']} {L('kg_week')}")
            st.write(f"**{L('location')}:** {row['location']}")
            if row.get("image"):
                st.image(base64.b64decode(row["image"]), width=200)
            st.write(f"**{L('quality')}:** {row['quality']}")
            st.write(f"**ID:** {row['trace_id'][:8]}")
            if st.button("❌ " + L("delete_success"), key=f"del-{i}"):
                data.remove(row)
                save_data(data)
                st.success(L("delete_success"))
                st.experimental_rerun()
            st.markdown("---")
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
    st.write(f"**Unit:** {unit['unit']}")
    st.write(f"**Tool/Cost:** {unit['tool']}")
    st.write(f"**ROI:** {unit['roi']}")
    st.write(f"**Sample Reusers:** {', '.join(reuse_db[mat])}")
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

# --- HELPER: USER RATING ---
def get_user_rating(user_id):
    ratings = load_datafile(RATINGS_FILE, [])
    user_ratings = [r["rating"] for r in ratings if r["user"] == user_id]
    if user_ratings:
        return round(sum(user_ratings) / len(user_ratings), 1)
    else:
        return "N/A"

# --- MAIN LOOP ---
def main():
    pages = {
        "landing": landing_page,
        "login": login_page,
        "signup": signup_page,
        "home": home_page,
        "submit": submit_page,
        "browse": browse_page,
        "dashboard": dashboard_page,
        "export": export_page,
        "analytics": analytics_page,
        "microplanner": microplanner_page,
        "faq": faq_bot,
        "addvideo": video_stories,
        "videos": show_video_stories,
        "interest": interest_registration,
        "certificate": certificate_page,
        # Add more pages as you expand (messaging, admin, etc.)
    }
    page = st.session_state.get("page", "landing")
    if page in pages:
        pages[page]()
    else:
        landing_page()

if __name__ == "__main__":
    main()
