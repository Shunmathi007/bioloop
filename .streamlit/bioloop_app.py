# bioloop_app.py (Part 1/3)

import streamlit as st
from fuzzywuzzy import process
import json, os, re, hashlib
from geopy.geocoders import Nominatim
from datetime import datetime
import pandas as pd

# 🌍 App Config
st.set_page_config(page_title="BioLoop – Circular Economy for MSMEs", page_icon="♻", layout="wide")

# 🌐 PWA Support
st.markdown("""
<link rel="manifest" href="https://raw.githubusercontent.com/Shunmathi007/bioloop/main/manifest.json" />
<meta name="theme-color" content="#008080" />
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('https://raw.githubusercontent.com/Shunmathi007/bioloop/main/sw.js')
    .then(reg => console.log('ServiceWorker registered:', reg))
    .catch(err => console.error('ServiceWorker registration failed:', err));
  }
</script>
""", unsafe_allow_html=True)

# 🎨 Custom Styling and Animation
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins&display=swap');

html, body, [class*="stApp"] {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #e6f2e6, #ccf2ff);
    color: #1e3932;
}

.block-container {
    padding: 1rem 2rem;
    animation: slideIn 0.8s ease-in-out;
}

@keyframes slideIn {
    0% {opacity: 0; transform: translateY(20px);}
    100% {opacity: 1; transform: translateY(0);}
}

.stButton>button {
    background-color: #008080;
    color: white;
    border-radius: 8px;
    padding: 0.4em 1em;
    margin-top: 10px;
}

.metric {
    background-color: #ffffff77;
    padding: 10px;
    border-radius: 12px;
    margin-bottom: 10px;
}

h1, h2 {
    color: #004d40;
}
</style>
""", unsafe_allow_html=True)

# 🌿 Logo Banner
st.markdown("""
<div style='text-align: center; padding: 10px 0;'>
    <img src='https://raw.githubusercontent.com/Shunmathi007/bioloop/main/data/logo.png' width='120'>
    <h1>♻ BioLoop</h1>
    <p style='color:#00695c;'>Empowering Circular Economy for MSMEs</p>
</div>
""", unsafe_allow_html=True)

# 🔠 Language Selection
lang = st.selectbox("🌐 Choose Language", ["English", "தமிழ்", "हिन्दी"])

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

# 📁 File Setup
DATA_FILE = "data/waste_profiles.json"
USER_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"admin@bioloop.in": "admin"}, f)

users = json.load(open(USER_FILE))

# 🔐 Sidebar Auth
st.sidebar.header(labels[lang]["login"])
auth_mode = st.sidebar.radio("Auth Mode", ["Login", labels[lang]["signup"]])
authenticated = False

if auth_mode == "Login":
    user_id = st.sidebar.text_input("MSME ID")
    password = st.sidebar.text_input(labels[lang]["password"], type="password")
    authenticated = user_id in users and users[user_id] == password
    if not authenticated:
        st.warning(labels[lang]["invalid_login"])
        st.stop()
elif auth_mode == labels[lang]["signup"]:
    new_id = st.sidebar.text_input("Choose MSME ID")
    new_pass = st.sidebar.text_input("Choose Password", type="password")
    if st.sidebar.button("Create Account"):
        if new_id in users:
            st.sidebar.error(labels[lang]["duplicate_id"])
        elif not new_id or not new_pass:
            st.sidebar.warning(labels[lang]["missing_fields"])
        else:
            users[new_id] = new_pass
            with open(USER_FILE, "w") as f:
                json.dump(users, f)
            st.sidebar.success(labels[lang]["account_created"])
            st.stop()
    user_id = new_id
# bioloop_app.py (Part 2/3 – Waste Form & Suggestions)

# 🌍 Geolocation setup
geolocator = Nominatim(user_agent="bioloop")

# Reuse ideas based on materials
reuse_db = {
    "cotton scraps": ["🧸 Toy Stuffing", "🧵 Yarn Recyclers"],
    "metal scraps": ["⚙ Metal Artist", "🪑 Furniture Maker"],
    "food waste": ["🌱 Composting", "🔥 Biogas"],
    "sawdust": ["🪵 Board Makers", "🔥 Briquette Units"],
    "paper waste": ["📚 Stationery", "📦 Packaging"]
}

# Micro-unit data
micro_units = {
    "cotton scraps": {"unit": "Stuffing Unit", "tool": "Shredder (₹8,000)", "roi": "2 months"},
    "metal scraps": {"unit": "Art Studio", "tool": "Welder (₹12,000)", "roi": "₹6,000/month"},
    "food waste": {"unit": "Compost Bin", "tool": "Bin (₹2,000)", "roi": "₹1,500/month"},
    "sawdust": {"unit": "Briquette Unit", "tool": "Press (₹15,000)", "roi": "₹3,000/month"},
    "paper waste": {"unit": "Paper Unit", "tool": "Pulper (₹10,000)", "roi": "₹2,500/month"}
}

# Carbon savings per kg
carbon_factors = {
    "cotton scraps": 2.5,
    "metal scraps": 6.0,
    "food waste": 1.8,
    "sawdust": 2.2,
    "paper waste": 2.9
}

def generate_trace_hash(entry):
    raw = f"{entry['material']}{entry['quantity']}{entry['location']}_{entry['timestamp']}"
    return hashlib.sha256(raw.encode()).hexdigest()

# 🎛 Role Selector
roles = [
    "I have waste", "I need materials", "My Dashboard",
    "Analytics", "Micro-unit planner", "Export data"
]
if user_id == "admin@bioloop.in":
    roles.append("Admin Panel")

role = st.radio("🔘 Choose Role", roles)

# 📝 Waste Submission
if role == "I have waste":
    st.header("📝 " + labels[lang]["header"])
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
                st.warning("❗ Invalid contact info.")
            else:
                lat, lon = None, None
                try:
                    loc = geolocator.geocode(location)
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

                st.success("✅ Submission saved!")

                # ♻ Suggestions
                st.subheader("🔄 Reuse Suggestions")
                for r in reuse_db.get(material, []):
                    st.write(f"✅ {r}")

                factor = carbon_factors.get(material, 2.4)
                st.metric("🌱 CO₂ Saved", f"{quantity * factor:.2f} kg/month")
                st.metric("💰 Revenue", f"₹{quantity * 5}/month")

                if material in micro_units:
                    mu = micro_units[material]
                    st.subheader("💡 Micro-Unit Plan")
                    st.write(f"🏭 Unit: {mu['unit']} | 🛠 Tool: {mu['tool']} | 📈 ROI: {mu['roi']}")
# 📦 Waste Listings (Buyers)
elif role == "I need materials":
    st.header("🔍 Waste Listings")
    data = json.load(open(DATA_FILE))
    materials = list(set([d["material"] for d in data]))
    selected = st.selectbox("Filter Material", ["All"] + materials)
    filtered = data if selected == "All" else [d for d in data if d["material"] == selected]

    for d in filtered:
        st.markdown(f"{d['material'].title()}** — {d['quantity']} kg/week")
        st.markdown(f"📍 {d['location']} | 📞 {d['contact']}")
        st.markdown(f"🧾 Quality: {d.get('quality', '-')}, Trace ID: {d.get('trace_id', '-')}")
        st.markdown("---")

    coords = pd.DataFrame([
        {"lat": d["lat"], "lon": d["lon"]}
        for d in filtered if d["lat"] and d["lon"]
    ])
    if not coords.empty:
        st.subheader("🗺 Map View")
        st.map(coords)

# 👤 My Dashboard
elif role == "My Dashboard":
    st.header("👤 My Dashboard")
    data = json.load(open(DATA_FILE))
    my_entries = [d for d in data if d.get("user_id") == user_id]

    if not my_entries:
        st.info("You haven't submitted any waste yet.")
    else:
        df = pd.DataFrame(my_entries)
        total = df["quantity"].sum()
        co2_saved = sum([
            d["quantity"] * carbon_factors.get(d["material"], 2.4)
            for d in my_entries
        ])
        st.metric("📦 Total Waste", f"{total} kg/week")
        st.metric("🌱 CO₂ Saved", f"{co2_saved:.2f} kg/month")

        st.subheader("🎯 Monthly Goals")
        goal_co2 = st.number_input("Target CO₂ Savings (kg/month)", min_value=0, key="goal_co2")
        goal_rev = st.number_input("Target Revenue (₹/month)", min_value=0, key="goal_rev")

        st.progress(min(100, (co2_saved / goal_co2 * 100)) if goal_co2 else 0)
        st.write(f"CO₂ Goal: {co2_saved:.1f}/{goal_co2} kg")

        st.progress(min(100, (total * 5 / goal_rev * 100)) if goal_rev else 0)
        st.write(f"Revenue Goal: ₹{total*5:.1f}/₹{goal_rev}")

        st.subheader("📝 Submissions")
        for d in my_entries:
            st.markdown(f"{d['material'].title()}** — {d['quantity']} kg/week")
            st.markdown(f"📍 {d['location']} | 📞 {d['contact']}")
            st.markdown(f"🧾 Quality: {d.get('quality','-')}, Trace ID: {d.get('trace_id','-')}")
            st.markdown("---")

# 📈 Analytics
elif role == "Analytics":
    st.header("📊 Analytics Dashboard")
    data = json.load(open(DATA_FILE))
    df = pd.DataFrame(data)

    if df.empty:
        st.info("No data available.")
    else:
        total_quantity = df["quantity"].sum()
        total_co2 = sum([
            d["quantity"] * carbon_factors.get(d["material"], 2.4) for d in data
        ])
        st.metric("📦 Total Waste Submitted", f"{total_quantity} kg")
        st.metric("🌱 Total CO₂ Saved", f"{total_co2:.2f} kg")

        top_mats = df["material"].value_counts().head(5)
        st.subheader("🏆 Top Waste Types")
        for mat, count in top_mats.items():
            st.write(f"✅ {mat.title()}: {count} entries")

# 🧪 Micro-unit Planner
elif role == "Micro-unit planner":
    st.header("🛠 Micro-Unit Planner")
    budget = st.number_input("Your budget (₹)", min_value=100)

    def extract_price(tool_str):
        match = re.search(r"₹(\d[\d,]*)", tool_str)
        return int(match.group(1).replace(",", "")) if match else 0

    affordable = {
        mat: unit for mat, unit in micro_units.items()
        if extract_price(unit["tool"]) <= budget
    }

    if affordable:
        for mat, unit in affordable.items():
            st.markdown(f"{mat.title()}")
            st.write(f"🛠 Tool: {unit['tool']}")
            st.write(f"🏭 Unit: {unit['unit']}")
            st.write(f"📈 ROI: {unit['roi']}")
            st.markdown("---")
    else:
        st.warning("No units found within your budget.")

# ⬇ Export Data
elif role == "Export data":
    st.header("📥 Download Waste Records")
    data = json.load(open(DATA_FILE))
    if not data:
        st.info("No submissions yet.")
    else:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button("📁 Download CSV", csv, "bioloop_data.csv", "text/csv")

# 🛡 Admin Panel
elif role == "Admin Panel":
    st.header("🛡 Admin Panel")
    data = json.load(open(DATA_FILE))
    df = pd.DataFrame(data)

    filter_material = st.selectbox("Filter by Material", ["All"] + list(df["material"].unique()))
    filtered_df = df if filter_material == "All" else df[df["material"] == filter_material]
    st.write(f"🔎 Showing {len(filtered_df)} entries")
    st.dataframe(filtered_df)

    csv = filtered_df.to_csv(index=False)
    st.download_button("📁 Download Filtered CSV", csv, "filtered_submissions.csv", "text/csv")