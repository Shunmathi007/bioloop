import streamlit as st
import json, os, re, hashlib, base64, io
from fuzzywuzzy import process
from datetime import datetime
from geopy.geocoders import Nominatim
import pandas as pd
from streamlit_lottie import st_lottie
from fpdf import FPDF

# --- SESSION STATE & SETUP ---
st.set_page_config(page_title="BioLoop", page_icon="♻", layout="centered")
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "landing"
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"
if "verified" not in st.session_state:
    st.session_state["verified"] = False

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

# --- LABELS ---
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
        "howto": "🎓 How-to Videos & Support", "ai_help": "🤖 Need help? Ask our AI FAQ bot:",
        "download_cert": "🎓 Download Green MSME Certificate",
        "profile": "Profile", "leaderboard": "🏆 Top Contributors", "badge_gold": "🥇 Gold Contributor",
        "badge_silver": "🥈 Silver Contributor", "badge_bronze": "🥉 Bronze Contributor"
    }
    # Add Tamil/Hindi labels as before...
}
def L(key): return labels[st.session_state["lang"]].get(key, key)

# --- UTILS ---
def load_lottie(filepath):
    if not os.path.exists(filepath): return None
    with open(filepath, "r") as f: return json.load(f)
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

# --- LANG SELECTOR ---
def lang_selector():
    lang = st.selectbox("🌍", list(labels.keys()),
                        index=list(labels.keys()).index(st.session_state["lang"]))
    st.session_state["lang"] = lang

# --- USER VERIFY ---
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

# --- LEARNING & SUPPORT ---
def learning_support():
    st.header(L("howto"))
    st.video("https://www.youtube.com/embed/7fE8U1W1ZFk")  # Demo video, replace with your own
    st.write(L("ai_help"))
    # Simple FAQ bot (mock)
    q = st.text_input("Ask a question")
    if st.button("Ask"):
        faqs = {"how to submit waste": "Click 'Submit Waste' and fill the form!",
                "how to get certificate": "Contribute >50kg and download from dashboard."}
        st.info(faqs.get(q.lower(), "Sorry, I can't answer that yet!"))

# --- SUCCESS STORIES ---
def success_stories():
    st.header(L("success_story"))
    stories = load_datafile(STORIES_FILE, [])
    for s in stories:
        st.markdown(f"> *{s['story']}* \n— {s['user']}")
    if st.button(L("share_story")):
        txt = st.text_area("Your story")
        if st.button(L("submit_story")):
            stories.append({"user": st.session_state["user_id"], "story": txt})
            save_datafile(STORIES_FILE, stories)
            st.success(L("story_submitted"))
            st.experimental_rerun()

# --- IMPACT DASHBOARD ---
def impact_dashboard():
    st.subheader(L("impact_dash"))
    data = load_data()
    df = pd.DataFrame(data)
    if not df.empty:
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

# --- CERTIFICATE ---
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

# --- INTEREST REGISTRATION ---
def interest_registration():
    st.subheader(L("register_interest"))
    mat = st.selectbox(L("interest_material"), list(reuse_db.keys()))
    loc = st.text_input(L("interest_location"))
    if st.button(L("register_interest")):
        interests = load_datafile(INTERESTS_FILE, [])
        interests.append({"user": st.session_state["user_id"], "material": mat, "location": loc})
        save_datafile(INTERESTS_FILE, interests)
        st.success(L("interest_registered"))

def show_interest_matches():
    interests = load_datafile(INTERESTS_FILE, [])
    my_ints = [i for i in interests if i["user"] == st.session_state["user_id"]]
    if my_ints:
        st.write(f"🎯 {L('your_interests')}:")
        all_data = load_data()
        for i in my_ints:
            st.write(f"- {i['material']} in {i['location']}")
            matches = [d for d in all_data if d["material"] == i["material"] and i["location"].lower() in d["location"].lower()]
            if matches:
                st.write(f"Found {len(matches)} matching listings!")
    else:
        st.info("No interests registered yet.")

# --- RECOMMENDATION ---
def recommend_microunit(user_entry):
    material = user_entry["material"]
    location = user_entry["location"]
    suggestions = []
    for mat, unit in micro_units.items():
        if mat == material:
            suggestions.append(unit)
    buyers = [d for d in load_data() if d["material"] == material and location.lower() in d["location"].lower()]
    return suggestions, buyers[:3]

# --- MESSAGING SYSTEM ---
def message_board(trace_id):
    st.subheader(L("msg"))
    path = f"{MESSAGES_DIR}/messages_{trace_id}.json"
    messages = load_datafile(path, [])
    for m in messages:
        st.write(f"**{m['user']}**: {m['msg']} ({m['time'][:16].replace('T',' ')})")
    msg = st.text_input("Write a message", key=f"msg_{trace_id}")
    if st.button(L("send"), key=f"send_{trace_id}"):
        messages.append({"user": st.session_state["user_id"], "msg": msg, "time": datetime.now().isoformat()})
        save_datafile(path, messages)
        st.experimental_rerun()

# --- RATINGS ---
def rate_user(to_user):
    ratings = load_datafile(RATINGS_FILE, [])
    my_rating = next((r for r in ratings if r["from"]==st.session_state["user_id"] and r["to"]==to_user), None)
    if my_rating:
        st.info(f"{L('rating')}: {my_rating['score']}/5")
    else:
        score = st.slider(L("rate"), 1, 5, 5)
        if st.button(L("submit_rating")):
            ratings.append({"from": st.session_state["user_id"], "to": to_user, "score": score})
            save_datafile(RATINGS_FILE, ratings)
            st.success(L("thanks_rating"))

def get_user_rating(user_id):
    ratings = load_datafile(RATINGS_FILE, [])
    rlist = [r["score"] for r in ratings if r["to"]==user_id]
    if rlist: return round(sum(rlist)/len(rlist),2)
    return None

# --- PAGES ---
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
            st.button(L("howto"), use_container_width=True, on_click=go, args=("learn",))
            st.button(L("success_story"), use_container_width=True, on_click=go, args=("stories",))
            st.button(L("impact_dash"), use_container_width=True, on_click=go, args=("impact",))

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
        if st.session_state['user_id'] == "admin@bioloop.in":
            st.button("🛡 " + L("admin_panel"), on_click=go, args=("admin",), use_container_width=True)
        st.button(L("howto"), on_click=go, args=("learn",), use_container_width=True)
        st.button(L("success_story"), on_click=go, args=("stories",), use_container_width=True)
        st.button(L("impact_dash"), on_click=go, args=("impact",), use_container_width=True)
    st.button(L("logout"), on_click=logout, use_container_width=True)
    show_interest_matches()

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
                    "image": img_b64,
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
                # --- RECOMMEND BUYERS ---
                micro_suggestions, buyer_matches = recommend_microunit(entry)
                if buyer_matches:
                    st.write("🤝 Potential buyers/recyclers nearby:")
                    for b in buyer_matches:
                        st.markdown(f"- {b['contact']} ({b['location']})")
                        if b["user_id"] != st.session_state["user_id"]:
                            rate_user(b["user_id"])
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
            <p>{user_badge(d['user_id'])} | Rating: {get_user_rating(d['user_id']) or '-'} /5</p>
        </div>
        """, unsafe_allow_html=True)
        message_board(d["trace_id"])
        if d["user_id"] != st.session_state["user_id"]:
            rate_user(d["user_id"])
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
        generate_certificate(st.session_state["user_id"], total)
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
    pages = {
        "landing": landing_page,
        "login": login_page,
        "signup": signup_page,
        "home": home_page,
        "submit": submit_page,
        "browse": browse_page,
        "dashboard": dashboard_page,
        "analytics": analytics_page,
        "microplanner": microplanner_page,
        "export": export_page,
        "admin": admin_page,
        "learn": learning_support,
        "stories": success_stories,
        "impact": impact_dashboard,
        "interest": interest_registration,
    }
    pages[st.session_state["page"]]()
main()
