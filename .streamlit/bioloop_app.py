import streamlit as st
import json, os, re, hashlib, base64
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from streamlit_lottie import st_lottie

st.set_page_config(page_title="BioLoop", page_icon="♻", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="stApp"] {font-family: 'Poppins', sans-serif;}
    .stButton > button {
        background-color: #008080 !important; color: white !important;
        border-radius: 8px !important; padding: 0.5em 1.5em;
        font-weight: 600; transition: background 0.3s;
    }
    .stButton > button:hover {background-color: #005c5c !important;}
    .biol-card {
        background: #fff; border-radius: 14px;
        box-shadow: 0 2px 16px #cde5e3; padding: 1.5rem; margin-bottom: 20px;
        transition: box-shadow 0.3s; max-width: 540px; margin-left:auto;margin-right:auto;
    }
    .biol-card:hover {box-shadow: 0 8px 24px #b6cfcf;}
    .biol-title {font-size: 2.2rem; font-weight: 700; letter-spacing: -1.5px; color: #008080;}
    .biol-sub {font-size: 1.2rem; color: #4b7974;}
    .biol-metric {font-size: 1.3rem; color: #008080; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "landing"
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"

DATA_FILE = "data/waste_profiles.json"
USER_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"admin@bioloop.in": "admin"}, f)

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
        "browse": "Browse Materials"
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
        "browse": "வஸ்துக்களை தேடுங்கள்"
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
        "browse": "सामग्री ब्राउज़ करें"
    }
}

def L(key): return labels[st.session_state["lang"]].get(key, key)

def lang_selector():
    lang = st.selectbox("🌍", ["English", "தமிழ்", "हिन्दी"],
                        index=["English", "தமிழ்", "हिन्दी"].index(st.session_state["lang"]))
    st.session_state["lang"] = lang

def load_lottie(filepath):
    with open(filepath, "r") as f: return json.load(f)
def load_users():
    with open(USER_FILE) as f: return json.load(f)
def save_users(users):
    with open(USER_FILE, "w") as f: json.dump(users, f, indent=2)
def load_data():
    with open(DATA_FILE) as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

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

def go(page): st.session_state["page"] = page

def landing_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown(f"<div class='biol-title' style='text-align:center;'>♻ BioLoop</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='biol-sub' style='text-align:center;'>Empowering Circular Economy for MSMEs</div>", unsafe_allow_html=True)
        if os.path.exists("assets/hero_animation.json"):
            st_lottie(load_lottie("assets/hero_animation.json"), height=180, key="hero")
        st.markdown("<br>", unsafe_allow_html=True)
        lang_selector()
        with st.container():
            st.button(L("login"), use_container_width=True, on_click=go, args=("login",))
            st.button(L("signup"), use_container_width=True, on_click=go, args=("signup",))

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
            st.rerun()
        else:
            st.error(L("invalid_login"))
    st.button(L("back"), on_click=go, args=("landing",))

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
    st.button(L("back"), on_click=go, args=("landing",))

def home_page():
    st.markdown(f"<div class='biol-title'>Hi, {st.session_state['user_id']}!</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='biol-sub'>{L('browse')}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 " + L("submit"), on_click=go, args=("submit",), use_container_width=True)
        st.button("👤 " + L("my_submissions"), on_click=go, args=("dashboard",), use_container_width=True)
        st.button("📈 " + L("analytics"), on_click=go, args=("analytics",), use_container_width=True)
    with col2:
        st.button("🔍 " + L("browse"), on_click=go, args=("browse",), use_container_width=True)
        st.button("🏭 " + L("microplanner"), on_click=go, args=("microplanner",), use_container_width=True)
        st.button("📤 " + L("export"), on_click=go, args=("export",), use_container_width=True)
        if st.session_state['user_id'] == "admin@bioloop.in":
            st.button("🛡 " + L("admin_panel"), on_click=go, args=("admin",), use_container_width=True)
    st.button(L("logout"), on_click=logout, use_container_width=True)

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = ""
    st.session_state["page"] = "landing"
    st.rerun()

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
                    "image": img_b64,  # store image as base64
                    "timestamp": datetime.now().isoformat(),
                    "user_id": st.session_state["user_id"]
                }
                entry["trace_id"] = generate_trace_hash(entry)
                data = load_data()
                data.append(entry)
                save_data(data)

                factor = carbon_factors.get(material, 2.4)
                co2_saved = quantity * factor

                st.markdown(f"""<div class="biol-card" style="background:#e6f2e6;">
                    <h3 style='color:#008080;'>🎉 {L('success')}</h3>
                    <p><b>🌱 CO₂ Saved:</b> {co2_saved:.2f} kg/month</p>
                    <p><b>💰 Estimated Revenue:</b> ₹{quantity * 5}/month</p>
                    <div style='background:#fffbe0;padding:1em;border-radius:8px;margin-top:12px;'>
                        <b>💡 Micro-Unit Suggestion:</b> {micro_units[material]['unit'] if material in micro_units else "-"}<br>
                        <b>🛠 Tool Needed:</b> {micro_units[material]['tool'] if material in micro_units else "-"}<br>
                        <b>📈 ROI:</b> {micro_units[material]['roi'] if material in micro_units else "-"}
                    </div>
                    <div style='margin-top:10px;'>
                        <b>🔁 Reuse Ideas:</b>
                        <ul>
                        {''.join([f"<li>{idea}</li>" for idea in reuse_db.get(material, [])])}
                        </ul>
                    </div>
                </div>""", unsafe_allow_html=True)
                st.button(L("go_home"), on_click=go, args=("home",))
                return
    st.button(L("back"), on_click=go, args=("home",))

def browse_page():
    st.markdown(f"<div class='biol-title'>{L('browse_waste')}</div>", unsafe_allow_html=True)
    data = load_data()
    materials = list(set([d["material"] for d in data]))
    locations = sorted(set([d["location"] for d in data if d["location"]]))
    selected_material = st.selectbox(L("filter_material"), [L("all")] + materials)
    selected_location = st.selectbox(L("filter_location"), [L("all")] + locations)
    filtered = data
    if selected_material != L("all"):
        filtered = [d for d in filtered if d["material"] == selected_material]
    if selected_location != L("all"):
        filtered = [d for d in filtered if selected_location.lower() in d["location"].lower()]
    for d in filtered:
        img_html = ""
        if d.get("image"):
            img_html = f"<img src='data:image/png;base64,{d['image']}' width='140' style='margin:8px 0 8px 0;border-radius:10px;box-shadow:0 2px 8px #cde5e3;'>"
        st.markdown(f"""
        <div class="biol-card">
            {img_html}
            <h4 style='color:#008080'>{d['material'].title()} — {d['quantity']} {L('kg_week')}</h4>
            <p>📍 {d['location']} | 📞 {d['contact']}</p>
            <p>🧾 {L('quality')}: {d.get('quality','-')} | Trace ID: {d.get('trace_id','-')}</p>
        </div>
        """, unsafe_allow_html=True)
    st.button(L("back"), on_click=go, args=("home",))

def dashboard_page():
    st.markdown(f"<div class='biol-title'>👤 {L('my_submissions')}</div>", unsafe_allow_html=True)
    data = load_data()
    my_entries = [d for d in data if d.get("user_id") == st.session_state["user_id"]]
    if not my_entries:
        st.info(L("no_entries"))
    else:
        df = pd.DataFrame(my_entries)
        total = df["quantity"].sum()
        co2_saved = sum([
            d["quantity"] * carbon_factors.get(d["material"], 2.4)
            for d in my_entries
        ])
        st.metric("Your Total Waste", f"{total} kg/week")
        st.metric("Your CO₂ Saved", f"{co2_saved:.2f} kg/month")
        for i, d in enumerate(my_entries):
            img_html = ""
            if d.get("image"):
                img_html = f"<img src='data:image/png;base64,{d['image']}' width='120' style='margin:6px 0 8px 0;border-radius:8px;box-shadow:0 2px 8px #cde5e3;'>"
            st.markdown(f"""
            <div class="biol-card">
                {img_html}
                <b>{d['material'].title()} — {d['quantity']} {L('kg_week')}</b><br>
                <span>📍 {d['location']} | 📞 {d['contact']}</span><br>
                <span>🧾 {L('quality')}: {d.get('quality','-')} | Trace ID: {d.get('trace_id','-')}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑 Delete Submission {i+1}", key=f"delete_{i}"):
                updated_data = [entry for entry in data if entry.get("trace_id") != d.get("trace_id")]
                save_data(updated_data)
                st.success(L("delete_success"))
                st.rerun()
    st.button(L("back"), on_click=go, args=("home",))

def analytics_page():
    st.markdown(f"<div class='biol-title'>📈 {L('analytics')}</div>", unsafe_allow_html=True)
    data = load_data()
    df = pd.DataFrame(data)
    if df.empty:
        st.info(L("no_data"))
    else:
        total_quantity = df["quantity"].sum()
        total_co2 = sum([
            d["quantity"] * carbon_factors.get(d["material"], 2.4) for d in data
        ])
        st.metric("Total Waste Submitted", f"{total_quantity} kg")
        st.metric("Estimated CO₂ Saved", f"{total_co2:.2f} kg")
        top_mats = df["material"].value_counts().head(5)
        st.subheader("🏆 " + L("top_materials"))
        for mat, count in top_mats.items():
            st.markdown(f"<div class='biol-card'>{mat.title()}: {count} entries</div>", unsafe_allow_html=True)
    st.button(L("back"), on_click=go, args=("home",))

def microplanner_page():
    st.markdown(f"<div class='biol-title'>🏭 {L('microplanner')}</div>", unsafe_allow_html=True)
    budget = st.number_input("Enter your budget (₹)", min_value=100)
    def extract_price(tool_str):
        import re
        match = re.search(r"₹(\d[\d,]*)", tool_str)
        return int(match.group(1).replace(",", "")) if match else 0
    affordable = {
        mat: unit for mat, unit in micro_units.items()
        if extract_price(unit["tool"]) <= budget
    }
    if affordable:
        for mat, unit in affordable.items():
            st.markdown(f"""
            <div class="biol-card">
                <h4>{mat.title()}</h4>
                🛠 <b>Tool:</b> {unit['tool']}<br>
                💰 <b>ROI:</b> {unit['roi']}<br>
                🏭 <b>Unit:</b> {unit['unit']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No micro-units found within your budget.")
    st.button(L("back"), on_click=go, args=("home",))

def export_page():
    st.markdown(f"<div class='biol-title'>📤 {L('export')}</div>", unsafe_allow_html=True)
    data = load_data()
    if not data:
        st.info(L("no_data"))
    else:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button(L("download_csv"), csv, "bioloop_data.csv", "text/csv")
    st.button(L("back"), on_click=go, args=("home",))

def admin_page():
    st.markdown(f"<div class='biol-title'>🛡 {L('admin_panel')}</div>", unsafe_allow_html=True)
    data = load_data()
    df = pd.DataFrame(data)
    if not df.empty:
        filter_material = st.selectbox(L("filter_material"), [L("all")] + list(df["material"].unique()))
        filtered_df = df if filter_material == L("all") else df[df["material"] == filter_material]
        st.write(f"🧾 Showing {len(filtered_df)} entries")
        st.dataframe(filtered_df)
        csv = filtered_df.to_csv(index=False)
        st.download_button(L("download_csv"), csv, "filtered_submissions.csv", "text/csv")
    else:
        st.info(L("no_data"))
    st.button(L("back"), on_click=go, args=("home",))

def main():
    if st.session_state["page"] == "landing":
        landing_page()
    elif st.session_state["page"] == "login":
        login_page()
    elif st.session_state["page"] == "signup":
        signup_page()
    elif not st.session_state["authenticated"]:
        landing_page()
    elif st.session_state["page"] == "home":
        home_page()
    elif st.session_state["page"] == "submit":
        submit_page()
    elif st.session_state["page"] == "browse":
        browse_page()
    elif st.session_state["page"] == "dashboard":
        dashboard_page()
    elif st.session_state["page"] == "analytics":
        analytics_page()
    elif st.session_state["page"] == "microplanner":
        microplanner_page()
    elif st.session_state["page"] == "export":
        export_page()
    elif st.session_state["page"] == "admin":
        admin_page()
    else:
        landing_page()

main()
