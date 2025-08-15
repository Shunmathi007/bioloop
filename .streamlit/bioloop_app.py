import streamlit as st
import json, os, re, hashlib
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from streamlit_lottie import st_lottie

# --- Page settings ---
st.set_page_config(page_title="BioLoop", page_icon="♻", layout="wide")

# --- Custom CSS & fonts ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="stApp"] {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #f6f9fa 0%, #e6f2e6 100%);
    color: #1e3932;
}
.stButton > button {
    background-color: #008080 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.5em 1.5em;
    font-weight: 600;
    transition: background 0.3s;
}
.stButton > button:hover {
    background-color: #005c5c !important;
}
.biol-card {
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 2px 16px #cde5e3;
    padding: 1.5rem;
    margin-bottom: 20px;
    transition: box-shadow 0.3s;
}
.biol-card:hover {
    box-shadow: 0 8px 24px #b6cfcf;
}
.biol-section {
    margin-bottom: 2.5rem;
}
.biol-title {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -1.5px;
    color: #008080;
}
.biol-sub {
    font-size: 1.2rem;
    color: #4b7974;
}
.biol-metric {
    font-size: 1.6rem;
    color: #008080;
    font-weight: bold;
}
@media (max-width: 768px) {
    .biol-card { padding: 1rem; }
    .biol-title { font-size: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)

# --- Load Lottie animation ---
def load_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_hero = load_lottie("assets/hero_animation.json")

# --- Hero Section ---
with st.container():
    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="biol-title">♻ BioLoop</div>', unsafe_allow_html=True)
        st.markdown('<div class="biol-sub">Empowering Circular Economy for MSMEs</div>', unsafe_allow_html=True)
        st.markdown("Reduce waste. Empower reuse. Enable green innovation.")
        st.markdown('<br>', unsafe_allow_html=True)
    with right:
        st_lottie(lottie_hero, height=230, speed=1, key="hero-lottie")

# --- Language selector ---
lang = st.selectbox("🌍 Choose Language", ["English", "தமிழ்", "हिन्दी"])
labels = {
    "English": {
        "submit": "Submit", "material": "Material Type", "login": "MSME Login", "password": "Password",
        "signup": "Sign Up", "location": "Location", "quantity": "Quantity (kg/week)", "invalid_login": "🔐 Invalid login.",
        "header": "Submit Your Waste", "contact": "Contact Info", "quality": "Quality", "public_contact": "Show contact publicly",
        "account_created": "✅ Account created! Please log in.", "duplicate_id": "🚫 ID already exists.",
        "missing_fields": "Please fill both fields."
    },
    "தமிழ்": {
        "submit": "சமர்ப்பி", "material": "வஸ்து வகை", "login": "எம்.எஸ்.எம்.இ நுழைவு", "password": "கடவுச்சொல்",
        "signup": "பதிவு செய்", "location": "இடம்", "quantity": "அளவு (கி.கி/வாரம்)", "invalid_login": "🔐 தவறான நுழைவு.",
        "header": "உங்கள் கழிவுகளை சமர்ப்பிக்கவும்", "contact": "தொடர்பு தகவல்", "quality": "தரம்", "public_contact": "தொடர்பை பொதுவாக காட்டவும்",
        "account_created": "✅ கணக்கு உருவாக்கப்பட்டது! தயவுசெய்து நுழைக.", "duplicate_id": "🚫 ஐடி ஏற்கனவே உள்ளது.",
        "missing_fields": "உருப்படிகளை நிரப்பவும்."
    },
    "हिन्दी": {
        "submit": "जमा करें", "material": "सामग्री प्रकार", "login": "एमएसएमई लॉगिन", "password": "पासवर्ड",
        "signup": "साइन अप", "location": "स्थान", "quantity": "मात्रा (किग्रा/सप्ताह)", "invalid_login": "🔐 अमान्य लॉगिन।",
        "header": "अपना कचरा जमा करें", "contact": "संपर्क जानकारी", "quality": "गुणवत्ता", "public_contact": "सार्वजनिक रूप से संपर्क दिखाएँ",
        "account_created": "✅ खाता बनाया गया! कृपया लॉग इन करें।", "duplicate_id": "🚫 आईडी पहले से मौजूद है।",
        "missing_fields": "कृपया सभी फ़ील्ड भरें।"
    }
}

# --- Data paths ---
DATA_FILE = "data/waste_profiles.json"
USER_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

# --- Auto-create files ---
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"admin@bioloop.in": "admin"}, f)

users = json.load(open(USER_FILE))

# --- Sidebar login/signup ---
st.sidebar.markdown('<div class="biol-title" style="font-size:1.3rem;">{}</div>'.format(labels[lang]["login"]), unsafe_allow_html=True)
auth_mode = st.sidebar.radio("Auth Mode", ["Login", labels[lang]["signup"]])
authenticated = False
user_id = ""

if auth_mode == "Login":
    user_id = st.sidebar.text_input("MSME ID")
    password = st.sidebar.text_input(labels[lang]["password"], type="password")
    if st.sidebar.button("Login"):
        if user_id in users and users[user_id] == password:
            authenticated = True
        else:
            st.sidebar.warning(labels[lang]["invalid_login"])
            st.stop()
elif auth_mode == labels[lang]["signup"]:
    new_id = st.sidebar.text_input("Choose MSME ID")
    new_pass = st.sidebar.text_input("Choose Password", type="password")
    if st.sidebar.button("Create Account"):
        if new_id in users:
            st.sidebar.error(labels[lang]["duplicate_id"])
            st.stop()
        elif not new_id or not new_pass:
            st.sidebar.warning(labels[lang]["missing_fields"])
            st.stop()
        else:
            users[new_id] = new_pass
            with open(USER_FILE, "w") as f:
                json.dump(users, f)
            st.sidebar.success(labels[lang]["account_created"])
            st.stop()
    user_id = new_id
    authenticated = True

# --- Geolocation ---
geolocator = Nominatim(user_agent="bioloop")
def generate_trace_hash(entry):
    raw = f"{entry['material']}{entry['quantity']}{entry['location']}_{entry['timestamp']}"
    return hashlib.sha256(raw.encode()).hexdigest()

# --- Databases ---
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

# --- Main Nav ---
roles = [
    "I have waste", "I need materials", "My Dashboard",
    "Analytics", "Micro-unit planner", "Export data"
]
if user_id == "admin@bioloop.in":
    roles.append("Admin Panel")
role = st.sidebar.radio("Choose Role", roles)

# --- Waste Submission Form ---
if role == "I have waste":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">📝 {}</div>'.format(labels[lang]["header"]), unsafe_allow_html=True)
    material_input = st.text_input(labels[lang]["material"])
    material = None
    if material_input:
        match = process.extractOne(material_input.lower(), reuse_db.keys())
        if match:
            material = match[0]
            st.info(f"Matched: {material.title()} ({match[1]}%)")
    if material:
        quantity = st.number_input(labels[lang]["quantity"], min_value=1)
        location = st.text_input(labels[lang]["location"])
        contact = st.text_input(labels[lang]["contact"])
        quality = st.selectbox(labels[lang]["quality"], ["Clean", "Mixed", "Contaminated"])
        show_contact = st.checkbox(labels[lang]["public_contact"], value=True)

        if st.button(labels[lang]["submit"]):
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
                    "user_id": user_id
                }
                entry["trace_id"] = generate_trace_hash(entry)
                data = json.load(open(DATA_FILE))
                data.append(entry)
                with open(DATA_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                st.success("✅ Submission saved.")
                st.subheader("🔍 Reuse Suggestions")
                for r in reuse_db.get(material, []):
                    st.markdown(f"<div class='biol-card'>{r}</div>", unsafe_allow_html=True)
                factor = carbon_factors.get(material, 2.4)
                st.metric("🌱 CO₂ Saved", f"{quantity * factor:.2f} kg/month")
                st.metric("💰 Revenue", f"₹{quantity * 5}/month")
                if material in micro_units:
                    mu = micro_units[material]
                    st.subheader("💡 Micro-Unit Plan")
                    st.markdown(
                        f"<div class='biol-card'>"
                        f"🏭 <b>Unit:</b> {mu['unit']}<br>"
                        f"🛠 <b>Tool:</b> {mu['tool']}<br>"
                        f"📈 <b>ROI:</b> {mu['roi']}"
                        f"</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Waste Listings ---
elif role == "I need materials":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">🔍 Waste Listings</div>', unsafe_allow_html=True)
    data = json.load(open(DATA_FILE))
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
    coords = pd.DataFrame([
        {"lat": d["lat"], "lon": d["lon"]}
        for d in filtered if d["lat"] and d["lon"]
    ])
    if not coords.empty:
        st.subheader("📍 Map View")
        st.map(coords)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Dashboard ---
elif role == "My Dashboard":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">👤 My Dashboard</div>', unsafe_allow_html=True)
    all_data = json.load(open(DATA_FILE))
    my_entries = [d for d in all_data if d.get("user_id") == user_id]
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
        st.subheader("🎯 Your Monthly Goals")
        goal_co2 = st.number_input("Target CO₂ Savings (kg/month)", min_value=0, key="goal_co2")
        goal_rev = st.number_input("Target Revenue (₹/month)", min_value=0, key="goal_rev")
        progress = lambda actual, target: min(100, (actual / target * 100)) if target else 0
        st.progress(progress(co2_saved, goal_co2))
        st.write(f"CO₂ Goal: {progress(co2_saved, goal_co2):.1f}% achieved")
        st.progress(progress(total * 5, goal_rev))
        st.write(f"Revenue Goal: {progress(total * 5, goal_rev):.1f}% achieved")
        st.subheader("📝 Your Submissions")
        for i, d in enumerate(my_entries):
            st.markdown(f"""
            <div class="biol-card">
                <b>{d['material'].title()} — {d['quantity']} kg/week</b><br>
                <span>📍 {d['location']} | 📞 {d['contact']}</span><br>
                <span>🧾 Quality: {d.get('quality','-')} | Trace ID: {d.get('trace_id','-')}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑 Delete Submission {i+1}", key=f"delete_{i}"):
                updated_data = [entry for entry in all_data if entry.get("trace_id") != d.get("trace_id")]
                with open(DATA_FILE, "w") as f:
                    json.dump(updated_data, f, indent=2)
                st.success("✅ Submission deleted successfully.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Analytics Dashboard ---
elif role == "Analytics":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">📈 Analytics Dashboard</div>', unsafe_allow_html=True)
    data = json.load(open(DATA_FILE))
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
    st.markdown('</div>', unsafe_allow_html=True)

# --- Micro-unit Planner ---
elif role == "Micro-unit planner":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">🏭 Micro-Unit Planner</div>', unsafe_allow_html=True)
    budget = st.number_input("Enter your budget (₹)", min_value=100)
    def extract_price(tool_str):
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
    st.markdown('</div>', unsafe_allow_html=True)

# --- Export CSV ---
elif role == "Export data":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">📥 Download All Submissions</div>', unsafe_allow_html=True)
    data = json.load(open(DATA_FILE))
    if not data:
        st.info("No data found yet.")
    else:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "bioloop_data.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Admin Panel ---
elif role == "Admin Panel":
    st.markdown('<div class="biol-section">', unsafe_allow_html=True)
    st.markdown('<div class="biol-title">🛡 Admin Panel</div>', unsafe_allow_html=True)
    data = json.load(open(DATA_FILE))
    df = pd.DataFrame(data)
    filter_material = st.selectbox("Filter by Material", ["All"] + list(df["material"].unique()))
    filtered_df = df if filter_material == "All" else df[df["material"] == filter_material]
    st.write(f"🧾 Showing {len(filtered_df)} entries")
    st.dataframe(filtered_df)
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download Filtered CSV", csv, "filtered_submissions.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)
