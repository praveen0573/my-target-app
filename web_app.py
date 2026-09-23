import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import os
import hashlib
import hmac
import time
import urllib.parse
import math

# --- Page Setup (3-Line Menu / Sidebar Default Enabled) ---
st.set_page_config(page_title="100 Cr Wealth Vault", page_icon="👑", layout="centered", initial_sidebar_state="expanded")

# --- Security & Crypto Hashing ---
def hash_pin(pin_str: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', pin_str.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"

def verify_pin(stored_hash: str, pin_input: str) -> bool:
    try:
        if not stored_hash: return False
        if "$" not in stored_hash: return stored_hash == pin_input
        salt_hex, key_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac('sha256', pin_input.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False

# Video Folder
UPLOADS_DIR = "uploaded_videos"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Database
DB_PATH = "wealth_data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (phone TEXT PRIMARY KEY, pin_hash TEXT, created_at TEXT)")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN pin_hash TEXT")
    conn.commit()
except Exception: pass
try:
    cursor.execute("UPDATE users SET pin_hash = pin WHERE pin_hash IS NULL AND pin IS NOT NULL")
    conn.commit()
except Exception: pass

cursor.execute("CREATE TABLE IF NOT EXISTS income_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, entry_date TEXT, daily_amount REAL, note TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS expense_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, entry_date TEXT, amount REAL, category TEXT, note TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS assets_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, entry_date TEXT, asset_type TEXT, quantity REAL, current_value REAL, note TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS debt_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, entry_date TEXT, debt_type TEXT, person_name TEXT, amount REAL, note TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS reels_feed (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, post_date TEXT, hook_title TEXT, gyan_content TEXT, video_filename TEXT, likes_count INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS daily_challenges (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, challenge_date TEXT, task_text TEXT, reward_type TEXT, reward_val REAL, is_completed INTEGER DEFAULT 0, UNIQUE(user_phone, challenge_date))")
cursor.execute("CREATE TABLE IF NOT EXISTS ludo_rooms (room_code TEXT PRIMARY KEY, room_name TEXT, host_phone TEXT, status TEXT DEFAULT 'WAITING', current_turn TEXT, last_dice INTEGER DEFAULT 0, winner TEXT DEFAULT '')")
cursor.execute("CREATE TABLE IF NOT EXISTS ludo_players (id INTEGER PRIMARY KEY AUTOINCREMENT, room_code TEXT, user_phone TEXT, color TEXT, token_pos INTEGER DEFAULT 0, joined_at TEXT, UNIQUE(room_code, user_phone))")
cursor.execute("CREATE TABLE IF NOT EXISTS wealth_squads (squad_id INTEGER PRIMARY KEY AUTOINCREMENT, squad_name TEXT, squad_code TEXT UNIQUE, creator_phone TEXT, monthly_target REAL DEFAULT 25000.0)")
cursor.execute("CREATE TABLE IF NOT EXISTS squad_members (id INTEGER PRIMARY KEY AUTOINCREMENT, squad_code TEXT, user_phone TEXT, joined_date TEXT, UNIQUE(squad_code, user_phone))")
conn.commit()

# Starter Reels
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                   ("OFFICIAL", str(date.today()), "👑 100 Crore Mindset", "गरीब लोग समय बेचकर कमाते हैं, अमीर लोग एसेट्स बनाकर सोते हुए कमाते हैं!", "", 45))
    conn.commit()

# Session State
if "logged_user" not in st.session_state: st.session_state["logged_user"] = None
if "selected_future_yrs" not in st.session_state: st.session_state["selected_future_yrs"] = 5
if "selected_ig_mins" not in st.session_state: st.session_state["selected_ig_mins"] = 30
if "reverse_horizon_yrs" not in st.session_state: st.session_state["reverse_horizon_yrs"] = 15

# App Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0b0e14 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    .hero-card {
        background: linear-gradient(135deg, #1f1b16 0%, #0d0f12 100%);
        border: 2px solid #f59e0b;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(245, 158, 11, 0.2);
    }
    .stat-tile {
        background: #161b22;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 14px;
        text-align: center;
        margin-bottom: 10px;
    }
    .app-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
    }
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Login Guard
if not st.session_state["logged_user"]:
    st.markdown("""
        <div class="hero-card" style="margin-top: 10px;">
            <h1 style="color: #f59e0b; margin:0;">👑 100 CR WEALTH VAULT</h1>
            <p style="color: #8b949e; font-size:0.9rem; margin-top:5px;">Secure Financial Operating System</p>
        </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 सुरक्षित लॉगिन", "📝 नया खाता"])
    with auth_tab1:
        with st.form("login_form"):
            l_phone = st.text_input("मोबाइल नंबर:", max_chars=10, value="9983204295")
            l_pin = st.text_input("4-अंकों का गुप्त पिन:", type="password", max_chars=4)
            if st.form_submit_button("लॉगिन करें 🔓", type="primary", use_container_width=True):
                cursor.execute("SELECT pin_hash FROM users WHERE phone = ?", (l_phone,))
                res = cursor.fetchone()
                if res and verify_pin(res[0], l_pin):
                    st.session_state["logged_user"] = l_phone
                    st.rerun()
                else: st.error("गलत पिन या नंबर!")

    with auth_tab2:
        with st.form("signup_form"):
            s_phone = st.text_input("10-अंकों का मोबाइल नंबर:", max_chars=10, value="9983204295")
            s_pin = st.text_input("नया 4-अंकों का पिन बनाएँ:", type="password", max_chars=4)
            s_pin2 = st.text_input("पिन दोबारा डालें:", type="password", max_chars=4)
            if st.form_submit_button("नया खाता बनाएँ 🚀", use_container_width=True):
                if s_pin == s_pin2 and len(s_pin) == 4:
                    h = hash_pin(s_pin)
                    cursor.execute("INSERT OR REPLACE INTO users (phone, pin_hash, created_at) VALUES (?, ?, ?)", (s_phone, h, str(date.today())))
                    conn.commit()
                    st.session_state["logged_user"] = s_phone
                    st.rerun()
                else: st.error("पिन दोनों जगह एक जैसा डालें!")
    st.stop()

# ==================== Logged In App ====================
USER = st.session_state["logged_user"]
TARGET = 1000000000

# Queries
cash_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', daily_amount as 'Raqam (₹)', note as 'Vivran' FROM income_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(USER,))
exp_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', amount as 'Raqam (₹)', category as 'Category', note as 'Vivran' FROM expense_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(USER,))
asset_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', asset_type as 'Type', quantity as 'Qty', current_value as 'Value (₹)', note as 'Vivran' FROM assets_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(USER,))
debt_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', debt_type as 'Type', person_name as 'Naam', amount as 'Raqam (₹)', note as 'Vivran' FROM debt_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(USER,))

inc_val = cash_df['Raqam (₹)'].sum() if not cash_df.empty else 0.0
exp_val = exp_df['Raqam (₹)'].sum() if not exp_df.empty else 0.0
net_cash = max(inc_val - exp_val, 0.0)
asset_val = asset_df['Value (₹)'].sum() if not asset_df.empty else 0.0

tot_liab = debt_df[debt_df["Type"].str.contains("लायबिलिटी|Liability", case=False, na=False)]["Raqam (₹)"].sum() if not debt_df.empty else 0.0
tot_rec = debt_df[debt_df["Type"].str.contains("एसेट|Asset", case=False, na=False)]["Raqam (₹)"].sum() if not debt_df.empty else 0.0
networth = max(net_cash + asset_val + tot_rec - tot_liab, 0.0)

today_str = str(date.today())
unique_dates = sorted(cash_df["Tariqh"].unique().tolist(), reverse=True) if not cash_df.empty else []
streak = 0
chk = date.today()
if today_str not in unique_dates: chk = date.today() - timedelta(days=1)
while str(chk) in unique_dates:
    streak += 1
    chk = chk - timedelta(days=1)

# ==================== ☰ तीन लाइनों वाला मेनू (SIDEBAR NAVIGATION) ====================
with st.sidebar:
    st.markdown(f"""
        <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 12px; border-radius: 12px; text-align: center; margin-bottom: 12px;">
            <b style="color: #f59e0b; font-size: 1.1rem;">👑 100 CR CLUB</b><br>
            <span style="font-size: 0.85rem; color: #cbd5e1;">यूज़र: @{USER[:5]}*****</span><br>
            <small style="color: #22c55e; font-weight: bold;">🔥 {streak} दिन स्ट्रीक</small>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### ☰ ऑल सेटिंग्स व मेनू")
    menu_choice = st.radio(
        "कहाँ जाना चाहते हैं?",
        [
            "🏠 होम (मुख्य डैशबोर्ड)",
            "📱 वेल्थ रील्स व ज्ञान",
            "🎲 ऑनलाइन लूडो मैच",
            "👥 वेल्थ स्क्वाड (दोस्तों का ग्रुप)",
            "🏆 ऑल-इंडिया लीडरबोर्ड",
            "🎯 डेली वेल्थ स्पिन",
            "👑 टॉप 1% व टाइम-मशीन",
            "🔥 रील्स डिटॉक्स कैलकुलेटर",
            "🎙️ AI वेल्थ वॉइस कोच",
            "🎯 100 Cr रिवर्स गोल",
            "📅 वित्तीय डायरी व कैलेंडर",
            "🌴 पैसिव FIRE सैलरी",
            "🪙 UPI गोल्ड व माइक्रो SIP",
            "⚖️ टैक्स बफ़र व असली नेटवर्थ",
            "🏎️ लग्ज़री सिमुलेटर",
            "💵 कमाई दर्ज करें",
            "💸 ख़र्च दर्ज करें",
            "⚖️ कर्ज़ व संपत्तियां"
        ],
        index=0
    )

    st.write("---")
    if st.button("लॉगआउट करें 🔒", use_container_width=True):
        st.session_state["logged_user"] = None
        st.rerun()

# ==================== 1. 🏠 होम (मुख्य डैशबोर्ड) ====================
if menu_choice == "🏠 होम (मुख्य डैशबोर्ड)":
    prog_pct = min((networth / TARGET) * 100, 100.0)
    
    st.markdown(f"""
        <div class="hero-card">
            <span style="color:#8b949e; font-size:0.85rem; font-weight:700; text-transform:uppercase; letter-spacing:1px;">TOTAL CLEAN NETWORTH</span>
            <h1 style="color:#f59e0b; font-size:2.4rem; margin:6px 0; font-weight:900;">₹{networth:,.0f}</h1>
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#8b949e; margin-top:8px;">
                <span>🎯 लक्ष्य: ₹100 करोड़</span>
                <span style="color:#f59e0b; font-weight:bold;">{prog_pct:.6f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.progress(min(networth / TARGET, 1.0))

    # Live Stat Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat-tile"><small style="color:#8b949e;">नकद बचत</small><h3 style="color:#22c55e; margin:4px 0;">₹{net_cash:,.0f}</h3></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-tile"><small style="color:#8b949e;">सोना व एसेट्स</small><h3 style="color:#eab308; margin:4px 0;">₹{asset_val:,.0f}</h3></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-tile"><small style="color:#8b949e;">कर्ज़ (देनदारी)</small><h3 style="color:#ef4444; margin:4px 0;">₹{tot_liab:,.0f}</h3></div>""", unsafe_allow_html=True)

    st.write("---")
    st.markdown("#### ⚡ 1-क्लिक क्विक एक्शन")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("🟡 ₹10 सोना खरीदें", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K)', 0.0013, 10.0, 'Home SIP')", (USER, today_str))
            conn.commit()
            st.success("₹10 का 24K सोना जुड़ गया!")
            st.rerun()
    with col_q2:
        if st.button("🔥 डिटॉक्स (+₹20 सोना)", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Detox)', 0.0026, 20.0, 'Detox Reward')", (USER, today_str))
            conn.commit()
            st.success("₹20 गोल्ड रिवॉर्ड जुड़ गया!")
            st.rerun()

# ==================== 2. 📱 वेल्थ रील्स व ज्ञान ====================
elif menu_choice == "📱 वेल्थ रील्स व ज्ञान":
    st.markdown("### 📱 100 Cr वेल्थ रील्स व कम्युनिटी")
    with st.expander("➕ नई रील बनाएँ / वीडियो पोस्ट करें", expanded=False):
        with st.form("create_reel_f", clear_on_submit=True):
            r_title = st.text_input("रील का मुख्य शीर्षक:", placeholder="उदा. 90% लोग यह गलती करते हैं...")
            r_text = st.text_area("ज्ञान / सीख:", placeholder="अपना सबक लिखें जिससे दूसरों को सीख मिले...")
            r_file = st.file_uploader("शॉर्ट वीडियो अपलोड करें (MP4, Max 40MB):", type=["mp4", "mov"])
            if st.form_submit_button("🚀 रील पब्लिश करें", type="primary", use_container_width=True):
                if r_title and r_text:
                    saved_fn = ""
                    if r_file is not None:
                        clean_fn = "".join(c for c in r_file.name if c.isalnum() or c in "._-")
                        saved_fn = f"{USER}_{int(time.time())}_{clean_fn}"
                        with open(os.path.join(UPLOADS_DIR, saved_fn), "wb") as f:
                            f.write(r_file.getbuffer())

                    cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, 0)",
                                   (USER, today_str, r_title, r_text, saved_fn))
                    conn.commit()
                    st.success("आपकी रील पब्लिश हो गई!")
                    st.rerun()
                else: st.error("शीर्षक और ज्ञान विवरण दोनों भरें!")

    reels = pd.read_sql_query("SELECT id, user_phone, post_date, hook_title, gyan_content, video_filename, likes_count FROM reels_feed ORDER BY id DESC LIMIT 20", conn)
    if not reels.empty:
        for _, r in reels.iterrows():
            st.markdown(f"""
                <div class="app-card">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#8b949e; margin-bottom:4px;">
                        <span style="color:#f59e0b; font-weight:bold;">👤 @{r['user_phone'][:5]}*****</span>
                        <span>📅 {r['post_date']}</span>
                    </div>
                    <h3 style="color:#f59e0b; margin: 4px 0 8px 0;">{r['hook_title']}</h3>
                    <p style="font-size:1.02rem; line-height:1.5; color:#f0f6fc;">{r['gyan_content']}</p>
                </div>
            """, unsafe_allow_html=True)

            if r['video_filename']:
                vp = os.path.join(UPLOADS_DIR, r['video_filename'])
                if os.path.exists(vp): st.video(vp)

            c_act1, c_act2, c_act3 = st.columns([1.2, 1.4, 2])
            with c_act1:
                if st.button(f"❤️ {r['likes_count']}", key=f"rk_{r['id']}", use_container_width=True):
                    cursor.execute("UPDATE reels_feed SET likes_count = likes_count + 1 WHERE id = ?", (r['id'],))
                    conn.commit()
                    st.rerun()
            with c_act2:
                if st.button("🪙 ₹10 गोल्ड", key=f"rg_{r['id']}", use_container_width=True):
                    cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Reel Reward)', 0.0013, 10.0, 'Reel Reward')", (USER, today_str))
                    conn.commit()
                    st.success("₹10 का सोना मिला!")
            with c_act3:
                share_msg = f"🔥 100 Crore Mindset Reel:\n*{r['hook_title']}*\n\n\"{r['gyan_content']}\"\n\nJoin 100 Crore Vault App: https://100-crore-target.streamlit.app"
                wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(share_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; font-weight:bold; border:none; padding:8px; border-radius:10px; cursor:pointer;">📲 WhatsApp शेयर</button></a>', unsafe_allow_html=True)
            st.write("---")

# ==================== 3. 🎲 ऑनलाइन लूडो मैच ====================
elif menu_choice == "🎲 ऑनलाइन लूडो मैच":
    st.markdown("### 🎲 ऑनलाइन मल्टीप्लेयर लूडो")
    cursor.execute("""
        SELECT r.room_code, r.room_name, r.current_turn, r.last_dice 
        FROM ludo_rooms r 
        INNER JOIN ludo_players p ON r.room_code = p.room_code 
        WHERE p.user_phone = ? AND r.status != 'FINISHED'
    """, (USER,))
    room_data = cursor.fetchone()

    if not room_data:
        c_l1, c_l2 = st.columns(2)
        with c_l1:
            with st.form("ludo_create_f"):
                r_code = st.text_input("रूम कोड बनाएँ:", max_chars=4, value="4455")
                if st.form_submit_button("रूम बनाएँ 🎲", use_container_width=True):
                    try:
                        cursor.execute("INSERT INTO ludo_rooms (room_code, room_name, host_phone, current_turn) VALUES (?, 'Battle Arena', ?, ?)", (r_code, USER, USER))
                        cursor.execute("INSERT INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🔴 लाल', ?)", (r_code, USER, today_str))
                        conn.commit()
                        st.rerun()
                    except Exception: st.error("कोड पहले से उपयोग में है!")
        with c_l2:
            with st.form("ludo_join_f"):
                j_code = st.text_input("दोस्त का रूम कोड:", max_chars=4)
                if st.form_submit_button("मैच जॉइन करें ⚡", use_container_width=True):
                    cursor.execute("INSERT OR IGNORE INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🟢 हरा', ?)", (j_code, USER, today_str))
                    conn.commit()
                    st.rerun()
    else:
        rc, rn, rturn, rdice = room_data
        st.info(f"रूम कोड: **{rc}** | बारी: `@{rturn[:5]}*****` | डाइस: 🎲 {rdice}")
        if rturn == USER:
            if st.button("🎲 डाइस रोल करें (Roll Dice)", type="primary", use_container_width=True):
                dv = random.randint(1, 6)
                cursor.execute("SELECT token_pos FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, USER))
                cp = cursor.fetchone()[0]
                cursor.execute("UPDATE ludo_players SET token_pos = ? WHERE room_code = ? AND user_phone = ?", (min(cp + dv, 50), rc, USER))
                p_list = pd.read_sql_query("SELECT user_phone FROM ludo_players WHERE room_code = ?", conn, params=(rc,))['user_phone'].tolist()
                next_p = p_list[(p_list.index(USER) + 1) % len(p_list)]
                cursor.execute("UPDATE ludo_rooms SET current_turn = ?, last_dice = ? WHERE room_code = ?", (next_p, dv, rc))
                conn.commit()
                st.rerun()
        else:
            if st.button("🔄 बोर्ड रीफ़्रेश करें", use_container_width=True): st.rerun()

        if st.button("मैच छोड़ें", use_container_width=True):
            cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, USER))
            conn.commit()
            st.rerun()

# ==================== 4. 👥 वेल्थ स्क्वाड (दोस्तों का ग्रुप) ====================
elif menu_choice == "👥 वेल्थ स्क्वाड (दोस्तों का ग्रुप)":
    st.subheader("👥 5 दोस्तों का सीक्रेट वेल्थ स्क्वाड")
    cursor.execute("SELECT s.squad_name, s.squad_code FROM wealth_squads s INNER JOIN squad_members m ON s.squad_code = m.squad_code WHERE m.user_phone = ?", (USER,))
    sq_user = cursor.fetchone()
    if sq_user:
        st.success(f"ग्रुप का नाम: **{sq_user[0]}** | इनवाइट कोड: `{sq_user[1]}`")
    else:
        with st.form("sq_f"):
            sn = st.text_input("स्क्वाड का नाम:")
            sc = st.text_input("4-अंकों का कोड रखें:", max_chars=4)
            if st.form_submit_button("नया स्क्वाड बनाएँ 🛡️", use_container_width=True) and sn and len(sc) == 4:
                try:
                    cursor.execute("INSERT INTO wealth_squads (squad_name, squad_code, creator_phone) VALUES (?, ?, ?)", (sn, sc, USER))
                    cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)", (sc, USER, today_str))
                    conn.commit()
                    st.rerun()
                except Exception: st.error("कोड पहले से किसी ग्रुप का है!")

# ==================== 5. 🏆 ऑल-इंडिया लीडरबोर्ड ====================
elif menu_choice == "🏆 ऑल-इंडिया लीडरबोर्ड":
    st.subheader("🏆 ऑल-इंडिया वेल्थ अनुशासन लीडरबोर्ड")
    lead_rows = pd.read_sql_query("SELECT phone FROM users LIMIT 10", conn)
    for idx, r in lead_rows.iterrows():
        me = " (आप ⭐)" if r['phone'] == USER else ""
        st.write(f"**रैंक {idx+1}** • `@{r['phone'][:5]}*****`{me} — **🔥 एक्टिव**")

# ==================== 6. 🎯 डेली वेल्थ स्पिन ====================
elif menu_choice == "🎯 डेली वेल्थ स्पिन":
    st.subheader("🎯 डेली वेल्थ स्पिन व सीक्रेट चैलेंज")
    cursor.execute("SELECT task_text, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (USER, today_str))
    ch_data = cursor.fetchone()
    if not ch_data:
        if st.button("🎡 आज का व्हील स्पिन करें", type="primary", use_container_width=True):
            cursor.execute("INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed) VALUES (?, ?, 'ज़ीरो फ़ालतू ख़र्च: आज बाहर कोई चाय-नाश्ता नहीं!', 'XP', 100, 0)", (USER, today_str))
            conn.commit()
            st.rerun()
    else:
        st.info(f"📌 आज का मिशन: {ch_data[0]}")
        if ch_data[1] == 0:
            if st.button("✅ चैलेंज पूरा किया (+100 XP)", use_container_width=True):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE user_phone = ? AND challenge_date = ?", (USER, today_str))
                conn.commit()
                st.balloons()
                st.rerun()
        else: st.success("✅ आज का चैलेंज पूरा हो चुका है!")

# ==================== 7. 👑 टॉप 1% व टाइम-मशीन ====================
elif menu_choice == "👑 टॉप 1% व टाइम-मशीन":
    st.subheader("👑 टॉप 1% क्लब व टाइम-मशीन")
    badge = "🔱 TITAN" if networth >= 10000000 else "🐺 LONE HUSTLER"
    st.markdown(f"""
    <div class="hero-card">
        <h4 style="color:#f59e0b;">स्टेटस: {badge}</h4>
        <h2>नेटवर्थ: ₹{networth:,.0f}</h2>
        <p>स्ट्रीक: 🔥 {streak} दिन एक्टिव</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("#### ⏳ फ़्यूचर टाइम मशीन (1-क्लिक बटन):")
    b1, b2, b3, b4 = st.columns(4)
    with b1: 
        if st.button("🚀 3 साल", key="tm3"): st.session_state["selected_future_yrs"] = 3
    with b2: 
        if st.button("🚀 5 साल", key="tm5"): st.session_state["selected_future_yrs"] = 5
    with b3: 
        if st.button("🚀 10 साल", key="tm10"): st.session_state["selected_future_yrs"] = 10
    with b4: 
        if st.button("👑 15 साल", key="tm15"): st.session_state["selected_future_yrs"] = 15

    y = st.session_state["selected_future_yrs"]
    f_val = networth * ((1 + 0.15)**y) + (10000 * (((1 + 0.0125)**(y * 12) - 1) / 0.0125))
    st.metric(f"{y} साल बाद संभावित नेटवर्थ", f"₹{f_val:,.0f}")

# ==================== 8. 🔥 रील्स डिटॉक्स ====================
elif menu_choice == "🔥 रील्स डिटॉक्स कैलकुलेटर":
    st.subheader("🔥 रील्स डिटॉक्स कैलकुलेटर (बटन सिस्टम)")
    cd1, cd2, cd3, cd4 = st.columns(4)
    with cd1:
        if st.button("15 मिनट", key="d15"): st.session_state["selected_ig_mins"] = 15
    with cd2:
        if st.button("30 मिनट", key="d30"): st.session_state["selected_ig_mins"] = 30
    with cd3:
        if st.button("60 मिनट", key="d60"): st.session_state["selected_ig_mins"] = 60
    with cd4:
        if st.button("120 मिनट", key="d120"): st.session_state["selected_ig_mins"] = 120
    m = st.session_state["selected_ig_mins"]
    burn = (m / 60.0) * 300.0
    st.error(f"⚠️ {m} मिनट रील्स देखने से ₹{burn:,.0f} का समय जलकर राख हो गया!")

# ==================== 9. 🎙️ AI वेल्थ वॉइस कोच ====================
elif menu_choice == "🎙️ AI वेल्थ वॉइस कोच":
    st.subheader("🎙️ AI वेल्थ वॉइस कोच")
    speech_text = f"नमस्कार! आपकी नेटवर्थ ₹{networth:,.0f} है। रोज़ का अनुशासन ही 100 करोड़ का रास्ता है।"
    st.info(f"📜 {speech_text}")
    safe_speech_js = speech_text.replace('"', '\\"').replace('\n', ' ')
    audio_html = f"""
    <div style="text-align: center; margin-top: 10px;">
        <button onclick="speakAudio()" style="background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%); color: #111; font-weight: bold; border: none; padding: 10px 24px; border-radius: 20px; cursor: pointer;">
            🔊 ऑडियो कोच सुनें (Play)
        </button>
    </div>
    <script>
    function speakAudio() {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{safe_speech_js}");
        msg.lang = 'hi-IN';
        window.speechSynthesis.speak(msg);
    }}
    </script>
    """
    st.components.v1.html(audio_html, height=70)

# ==================== 10. 🎯 100 Cr रिवर्स गोल ====================
elif menu_choice == "🎯 100 Cr रिवर्स गोल":
    st.subheader("🎯 100 करोड़ का रिवर्स-गणित")
    r1, r2, r3 = st.columns(3)
    with r1:
        if st.button("⏱️ 10 साल", key="rv10"): st.session_state["reverse_horizon_yrs"] = 10
    with r2:
        if st.button("⏱️ 15 साल", key="rv15"): st.session_state["reverse_horizon_yrs"] = 15
    with r3:
        if st.button("⏱️ 20 साल", key="rv20"): st.session_state["reverse_horizon_yrs"] = 20
    sy = st.session_state["reverse_horizon_yrs"]
    st.metric(f"{sy} साल में 100 Cr का दैनिक लक्ष्य", f"₹{(TARGET / (sy * 365)):,.0f} / दिन")

# ==================== 11. 📅 वित्तीय डायरी व कैलेंडर ====================
elif menu_choice == "📅 वित्तीय डायरी व कैलेंडर":
    st.subheader("📅 दैनिक वित्तीय डायरी")
    sel_dt = str(st.date_input("तारीख चुनें:", value=date.today()))
    d_inc = cash_df[cash_df["Tariqh"] == sel_dt]["Raqam (₹)"].sum() if not cash_df.empty else 0.0
    d_exp = exp_df[exp_df["Tariqh"] == sel_dt]["Raqam (₹)"].sum() if not exp_df.empty else 0.0
    st.metric("उस दिन की शुद्ध बचत", f"₹{d_inc - d_exp:,.0f}")

# ==================== 12. 🌴 पैसिव FIRE सैलरी ====================
elif menu_choice == "🌴 पैसिव FIRE सैलरी":
    st.subheader("🌴 पैसिव कैशफ़्लो व वित्तीय आज़ादी")
    st.metric("मासिक पैसिव सैलरी (4% नियम)", f"₹{(networth * 0.04) / 12:,.0f} / माह")

# ==================== 13. 🪙 UPI गोल्ड व माइक्रो SIP ====================
elif menu_choice == "🪙 UPI गोल्ड व माइक्रो SIP":
    st.subheader("🪙 माइक्रो 24K गोल्ड SIP")
    if st.button("🟡 ₹10 सोना खरीदें"):
        cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K Micro SIP)', 0.0013, 10.0, 'Daily SIP')", (USER, today_str))
        conn.commit()
        st.success("₹10 का सोना जुड़ गया!")
        st.rerun()

# ==================== 14. ⚖️ टैक्स बफ़र व असली नेटवर्थ ====================
elif menu_choice == "⚖️ टैक्स बफ़र व असली नेटवर्थ":
    st.subheader("⚖️ स्मार्ट टैक्स बफ़र")
    st.metric("टैक्स-कटी असली इन-हैंड नेटवर्थ", f"₹{max(net_cash - (inc_val * 0.15), 0.0) + asset_val:,.0f}")

# ==================== 15. 🏎️ लग्ज़री सिमुलेटर ====================
elif menu_choice == "🏎️ लग्ज़री सिमुलेटर":
    st.subheader("🏎️ लग्ज़री विशलिस्ट सिमुलेटर")
    st.progress(min(networth / 8500000, 1.0))
    st.caption("स्पोर्ट्स कार गोल प्रोग्रेस (BMW/Mercedes)")

# ==================== 16. 💵 कमाई दर्ज करें ====================
elif menu_choice == "💵 कमाई दर्ज करें":
    st.subheader("💵 नई कमाई दर्ज करें")
    with st.form("inc_form_master", clear_on_submit=True):
        i_amt = st.number_input("रकम (₹ में):", min_value=0.0, step=500.0)
        i_note = st.text_input("स्रोत / नोट:", value="Business")
        if st.form_submit_button("कमाई सेव करें 💾") and i_amt > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)", (USER, today_str, i_amt, i_note))
            conn.commit()
            st.success("कमाई जुड़ गई!")
            st.rerun()
    if not cash_df.empty: st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)

# ==================== 17. 💸 ख़र्च दर्ज करें ====================
elif menu_choice == "💸 ख़र्च दर्ज करें":
    st.subheader("💸 ख़र्च दर्ज करें")
    with st.form("exp_form_master", clear_on_submit=True):
        e_amt = st.number_input("रकम (₹ में):", min_value=0.0, step=100.0)
        e_note = st.text_input("श्रेणी / विवरण:", value="Daily")
        if st.form_submit_button("ख़र्च सेव करें 💸") and e_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)", (USER, today_str, e_amt, e_note, e_note))
            conn.commit()
            st.warning("ख़र्च दर्ज हुआ!")
            st.rerun()
    if not exp_df.empty: st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)

# ==================== 18. ⚖️ कर्ज़ व संपत्तियां ====================
elif menu_choice == "⚖️ कर्ज़ व संपत्तियां":
    st.subheader("⚖️ कर्ज़, उधारी व संपत्तियां")
    st.write("#### संपत्तियां (Assets):")
    if not asset_df.empty: st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
    st.write("#### देनदारियां / कर्ज़ (Liabilities):")
    if not debt_df.empty: st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
