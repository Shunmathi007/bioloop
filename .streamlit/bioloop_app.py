import streamlit as st
import json, os, re, hashlib
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from streamlit_lottie import st_lottie

# --- PAGE SETUP & THEME ---
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

# --- SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "landing"
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"

# --- FILE PATHS ---
DATA_FILE = "data/waste_profiles.json"
USER_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"admin@bioloop.in": "admin"}, f)

# --- LABELS FOR LANGUAGES ---
labels = {
    "English": {
        "submit": "Submit Waste", "material": "Material Type", "login": "MSME Login", "password": "Password",
        "signup": "Sign Up", "location": "Location", "quantity": "Quantity (kg/week)", "invalid_login": "🔐 Invalid login.",
        "header": "Submit Your Waste", "contact": "Contact Info", "quality": "Quality", "public_contact": "Show contact publicly",
        "account_created": "✅ Account created! Please log in.", "duplicate_id": "🚫 ID already exists.",
        "missing_fields": "Please fill both fields.", "logout": "Logout", "back": "Back", "success": "Submission saved."
    },
    "தமிழ்": {
        "submit": "சமர்ப்பி", "material": "வஸ்து வகை", "login": "எம்.எஸ்.எம்.இ நுழைவு", "password": "கடவுச்சொல்",
        "signup": "பதிவு செய்", "location": "இடம்", "quantity": "அளவு (கி.கி/வாரம்)", "invalid_login": "🔐 தவறான நுழைவு.",
        "header": "உங்கள் கழிவுகளை சமர்ப்பிக்கவும்", "contact": "தொடர்பு தகவல்", "quality": "தரம்", "public_contact": "தொடர்பை பொதுவாக காட்டவும்",
        "account_created": "✅ கணக்கு உருவாக்கப்பட்டது! தயவுசெய்து நுழைக.", "duplicate_id": "🚫 ஐடி ஏற்கனவே உள்ளது.",
        "missing_fields": "உருப்படிகளை நிரப்பவும்.", "logout": "வெளியேறு", "back": "பின்னால்", "success": "சமர்ப்பிப்பு சேமிக்கப்பட்டது."
    },
    "हिन्दी": {
        "submit": "जमा करें", "material": "सामग्री प्रकार", "login": "एमएसएमई लॉगिन", "password": "पासवर्ड",
        "signup": "साइन अप", "location": "स्थान", "quantity": "मात्रा (किग्रा/सप्ताह)", "invalid_login": "🔐 अमान्य लॉगिन।",
        "header": "अपना कचरा जमा करें", "contact": "संपर्क जानकारी", "quality": "गुणवत्ता", "public_contact": "सार्वजनिक रूप से संपर्क दिखाएँ",
        "account_created": "✅ खाता बनाया गया! कृपया लॉग इन करें।", "duplicate_id": "🚫 आईडी पहले से मौजूद है।",
        "missing_fields": "कृपया सभी फ़ील्ड भरें।", "logout": "लॉगआउट", "back": "पीछे", "success": "जमा सफल।"
    }
}

def L(key): return labels[st.session_state["lang"]][key]

# --- LANGUAGE SELECTOR ---
def lang_selector():
    lang = st.selectbox("🌍 Choose Language", ["English", "தமிழ்", "हिन्दी"],
                        index=["English", "தமிழ்", "हिन्दी"].index(st.session_state["lang"]))
    st.session_state["lang"] = lang

# --- DATA UTILS ---
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

# --- APP DATA ---
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

# --- PAGES ---
def landing_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='biol-title' style='text-align:center;'>♻ BioLoop</div>", unsafe_allow_html=True)
        st.markdown("<div class='biol-sub' style='text-align:center;'>Empowering Circular Economy for MSMEs</div>", unsafe_allow_html=True)
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
    st.markdown("<div class='biol-sub'>What would you like to do?</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 " + L("submit"), on_click=go, args=("submit",), use_container_width=True)
        st.button("👤 My Submissions", on_click=go, args=("dashboard",), use_container_width=True)
        st.button("📈 Analytics", on_click=go, args=("analytics",), use_container_width=True)
    with col2:
        st.button("🔍 Browse Materials", on_click=go, args=("browse",), use_container_width=True)
        st.button("🏭 Micro-unit Planner", on_click=go, args=("microplanner",), use_container_width=True)
        st.button("📤 Export Data", on_click=go, args=("export",), use_container_width=True)
        if st.session_state['user_id'] == "admin@bioloop.in":
            st.button("🛡 Admin Panel", on_click=go, args=("admin",), use_container_width=True)
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
            st.info(f"Matched: {material.title()} ({match[1]}%)")

    if material:
        quantity = st.number_input(L("quantity"), min_value=1)
        location = st.text_input(L("location"))
        contact = st.text_input(L("contact"))
        quality = st.selectbox(L("quality"), ["Clean", "Mixed", "Contaminated"])
        show_contact = st.checkbox(L("public_contact"), value=True)

        if st.button(L("submit")):
            valid = re.match(r"[^@]+@[^@]+\.[^@]+", contact) or re.match(r"\d{10}", contact)
            if not valid:
                st.warning("Invalid contact.")
            else:
                lat, lon = None, None
                try:
                    loc = geolocator.geocode(location)
                    if loc:
                        lat, lon = loc.latitude, loc.longitude
                except:
                    pass

                entry = {
                    "material": material,
                    "quantity": quantity,
                    "location": location,
                    "contact": contact if show_contact else "Hidden",
                    "lat": lat,
                    "lon": lon,
                    "quality": quality,
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
                st.button("Go Home", on_click=go, args=("home",))
                return
    st.button(L("back"), on_click=go, args=("home",))

def browse_page():
    st.markdown(f"<div class='biol-title'>🔍 Waste Listings</div>", unsafe_allow_html=True)
    data = load_data()
    materials = list(set([d["material"] for d in data]))
    selected = st.selectbox("Filter Material", ["All"] + materials)
    filtered = data if selected == "All" else [d for d in data if d["material"] == selected]
    for d in filtered:
        st.markdown(f"""
        <div class="biol-card">
            <h4 style='color:#008080'>{d['material'].title()} — {d['quantity']} kg/week</h4>
            <p>📍 {d['location']} | 📞 {d['contact']}</p>
            <p>🧾 Quality: {d.get('quality','-')} | Trace ID: {d.get('trace_id','-')}</p>
        </div>
        """, unsafe_allow_html=True)
    st.button(L("back"), on_click=go, args=("home",))

def dashboard_page():
    st.markdown(f"<div class='biol-title'>👤 My Submissions</div>", unsafe_allow_html=True)
    data = load_data()
    my_entries = [d for d in data if d.get("user_id") == st.session_state["user_id"]]
    if not my_entries:
        st.info("You haven't submitted any waste yet.")
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
            st.markdown(f"""
            <div class="biol-card">
                <b>{d['material'].title()} — {d['quantity']} kg/week</b><br>
                <span>📍 {d['location']} | 📞 {d['contact']}</span><br>
                <span>🧾 Quality: {d.get('quality','-')} | Trace ID: {d.get('trace_id','-')}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑 Delete Submission {i+1}", key=f"delete_{i}"):
                updated_data = [entry for entry in data if entry.get("trace_id") != d.get("trace_id")]
                save_data(updated_data)
                st.success("✅ Submission deleted successfully.")
                st.rerun()
    st.button(L("back"), on_click=go, args=("home",))

def analytics_page():
    st.markdown(f"<div class='biol-title'>📈 Analytics Dashboard</div>", unsafe_allow_html=True)
    data = load_data()
    df = pd.DataFrame(data)
    if df.empty:
        st.info("No data to analyze.")
    else:
        total_quantity = df["quantity"].sum()
        total_co2 = sum([
            d["quantity"] * carbon_factors.get(d["material"], 2.4) for d in data
        ])
        st.metric("Total Waste Submitted", f"{total_quantity} kg")
        st.metric("Estimated CO₂ Saved", f"{total_co2:.2f} kg")
        top_mats = df["material"].value_counts().head(5)
        st.subheader("🏆 Top Submitted Materials")
        for mat, count in top_mats.items():
            st.markdown(f"<div class='biol-card'>{mat.title()}: {count} entries</div>", unsafe_allow_html=True)
    st.button(L("back"), on_click=go, args=("home",))

def microplanner_page():
    st.markdown(f"<div class='biol-title'>🏭 Micro-Unit Planner</div>", unsafe_allow_html=True)
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
    st.markdown(f"<div class='biol-title'>📤 Download All Submissions</div>", unsafe_allow_html=True)
    data = load_data()
    if not data:
        st.info("No data found yet.")
    else:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "bioloop_data.csv", "text/csv")
    st.button(L("back"), on_click=go, args=("home",))

def admin_page():
    st.markdown(f"<div class='biol-title'>🛡 Admin Panel</div>", unsafe_allow_html=True)
    data = load_data()
    df = pd.DataFrame(data)
    if not df.empty:
        filter_material = st.selectbox("Filter by Material", ["All"] + list(df["material"].unique()))
        filtered_df = df if filter_material == "All" else df[df["material"] == filter_material]
        st.write(f"🧾 Showing {len(filtered_df)} entries")
        st.dataframe(filtered_df)
        csv = filtered_df.to_csv(index=False)
        st.download_button("Download Filtered CSV", csv, "filtered_submissions.csv", "text/csv")
    else:
        st.info("No data found yet.")
    st.button(L("back"), on_click=go, args=("home",))

# --- MAIN ROUTER ---
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
