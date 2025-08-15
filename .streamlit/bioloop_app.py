import streamlit as st
import json, os, re, hashlib
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from streamlit_lottie import st_lottie

# --- CONFIGURATION ---
st.set_page_config(page_title="BioLoop", page_icon="♻", layout="centered")
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "landing"

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

# --- LOADERS ---
def load_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)
def load_users():
    with open(USER_FILE) as f:
        return json.load(f)
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)
def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

# --- HASH FUNCTION ---
def generate_trace_hash(entry):
    raw = f"{entry['material']}{entry['quantity']}{entry['location']}_{entry['timestamp']}"
    return hashlib.sha256(raw.encode()).hexdigest()

# --- PAGE NAVIGATION ---
def go(page):
    st.session_state["page"] = page

# --- PAGES ---
def landing_page():
    st.image("assets/bioloop_logo.png", width=120)
    st.title("♻️ BioLoop")
    st.subheader("Empowering Circular Economy for MSMEs")
    st.write("Reduce waste. Empower reuse. Enable green innovation.")
    st.lottie(load_lottie("assets/hero_animation.json"), height=180)
    st.write("---")
    st.button("Login", on_click=go, args=("login",))
    st.button("Sign Up", on_click=go, args=("signup",))

def login_page():
    st.title("Login")
    users = load_users()
    user = st.text_input("MSME ID")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user in users and users[user] == pw:
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user
            st.session_state["page"] = "home"
            st.rerun()
        else:
            st.error("🔐 Invalid login.")
    st.button("Back to Home", on_click=go, args=("landing",))

def signup_page():
    st.title("Sign Up")
    users = load_users()
    new_id = st.text_input("Choose MSME ID")
    new_pw = st.text_input("Choose Password", type="password")
    if st.button("Create Account"):
        if new_id in users:
            st.error("🚫 ID already exists.")
        elif not new_id or not new_pw:
            st.warning("Please fill both fields.")
        else:
            users[new_id] = new_pw
            save_users(users)
            st.success("✅ Account created! Please log in.")
            st.button("Go to Login", on_click=go, args=("login",))
    st.button("Back to Home", on_click=go, args=("landing",))

def home_page():
    st.title(f"Welcome, {st.session_state['user_id']}")
    st.write("What would you like to do?")
    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 Submit Waste", on_click=go, args=("submit",))
        st.button("👤 My Submissions", on_click=go, args=("dashboard",))
    with col2:
        st.button("🔍 Browse Materials", on_click=go, args=("browse",))
        if st.session_state['user_id'] == "admin@bioloop.in":
            st.button("🛡 Admin Panel", on_click=go, args=("admin",))
    st.button("Logout", on_click=logout)

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = ""
    st.session_state["page"] = "landing"
    st.rerun()

def submit_page():
    st.title("📝 Submit Waste")
    # Material fuzzy match
    material_input = st.text_input("Material Type")
    material = None
    if material_input:
        match = process.extractOne(material_input.lower(), reuse_db.keys())
        if match:
            material = match[0]
            st.info(f"Matched: {material.title()} ({match[1]}%)")
    if material:
        quantity = st.number_input("Quantity (kg/week)", min_value=1)
        location = st.text_input("Location")
        contact = st.text_input("Contact Info")
        quality = st.selectbox("Quality", ["Clean", "Mixed", "Contaminated"])
        show_contact = st.checkbox("Show contact publicly", value=True)
        if st.button("Submit"):
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
                st.success("✅ Submission saved.")
                st.button("Go Home", on_click=go, args=("home",))
                return
    st.button("Back to Home", on_click=go, args=("home",))

def browse_page():
    st.title("🔍 Waste Listings")
    data = load_data()
    materials = list(set([d["material"] for d in data]))
    selected = st.selectbox("Filter Material", ["All"] + materials)
    filtered = data if selected == "All" else [d for d in data if d["material"] == selected]
    for d in filtered:
        st.markdown(f"""
        <div style='background:#fff; border-radius:12px; margin-bottom:18px; 
        padding:16px; box-shadow:0 2px 10px #d1e7dd;'>
            <h4 style='color:#008080'>{d['material'].title()} — {d['quantity']} kg/week</h4>
            <p>📍 {d['location']} | 📞 {d['contact']}</p>
            <p>🧾 Quality: {d.get('quality','-')} | Trace ID: {d.get('trace_id','-')}</p>
        </div>
        """, unsafe_allow_html=True)
    st.button("Back to Home", on_click=go, args=("home",))

def dashboard_page():
    st.title("👤 My Submissions")
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
            <div style='background:#fff; border-radius:12px; margin-bottom:16px; 
            padding:14px; box-shadow:0 2px 8px #d1e7dd;'>
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
    st.button("Back to Home", on_click=go, args=("home",))

def admin_page():
    st.title("🛡 Admin Panel")
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
    st.button("Back to Home", on_click=go, args=("home",))

# --- MAIN ROUTER ---
def main():
    st.markdown("""<style>
    .stApp { background: linear-gradient(135deg, #f6f9fa 0%, #e6f2e6 100%) !important;}
    </style>""", unsafe_allow_html=True)
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
    elif st.session_state["page"] == "admin":
        admin_page()
    else:
        landing_page()

main()
