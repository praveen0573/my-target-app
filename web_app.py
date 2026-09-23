import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import io
import math
import os
import hashlib
import hmac
import time
from PIL import Image, ImageDraw

# --- Page Config ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- Security & Cryptographic Hashing ---
def hash_pin(pin_str: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', pin_str.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"

def verify_pin(stored_hash: str, pin_input: str) -> bool:
    try:
        if not stored_hash:
            return False
        if "$" not in stored_hash:
            return stored_hash == pin_input
        salt_hex, key_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac('sha256', pin_input.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False

# --- Video Storage Folder ---
UPLOADS_DIR = "uploaded_videos"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Database Setup & Auto Migration ---
DB_PATH = "wealth_data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY,
        pin_hash TEXT,
        created_at TEXT
    )
""")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN pin_hash TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("UPDATE users SET pin_hash = pin WHERE pin_hash IS NULL AND pin IS NOT NULL")
    conn.commit()
except sqlite3.OperationalError:
    pass

cursor.execute("""
    CREATE TABLE IF NOT EXISTS income_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        entry_date TEXT,
        daily_amount REAL,
        note TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        entry_date TEXT,
        amount REAL,
        category TEXT,
        note TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        entry_date TEXT,
        asset_type TEXT,
        quantity REAL,
        current_value REAL,
        note TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS debt_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        entry_date TEXT,
        debt_type TEXT,
        person_name TEXT,
        amount REAL,
        note TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS wealth_squads (
        squad_id INTEGER PRIMARY KEY AUTOINCREMENT,
        squad_name TEXT,
        squad_code TEXT UNIQUE,
        creator_phone TEXT,
        monthly_target REAL DEFAULT 25000.0
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS squad_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        squad_code TEXT,
        user_phone TEXT,
        joined_date TEXT,
        UNIQUE(squad_code, user_phone)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS reels_feed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        post_date TEXT,
        hook_title TEXT,
        gyan_content TEXT,
        video_filename TEXT,
        likes_count INTEGER DEFAULT 0
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS reels_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reel_id INTEGER,
        user_phone TEXT,
        comment_text TEXT,
        created_date TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_saved_reels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        reel_id INTEGER,
        saved_date TEXT,
        UNIQUE(user_phone, reel_id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        challenge_date TEXT,
        task_text TEXT,
        reward_type TEXT,
        reward_val REAL,
        is_completed INTEGER DEFAULT 0,
        UNIQUE(user_phone, challenge_date)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_loot_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        loot_date TEXT,
        nugget TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ludo_rooms (
        room_code TEXT PRIMARY KEY,
        room_name TEXT,
        host_phone TEXT,
        status TEXT DEFAULT 'WAITING',
        current_turn TEXT,
        last_dice INTEGER DEFAULT 0,
        winner TEXT DEFAULT ''
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ludo_players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT,
        user_phone TEXT,
        color TEXT,
        token_pos INTEGER DEFAULT 0,
        joined_at TEXT,
        UNIQUE(room_code, user_phone)
    )
""")
conn.commit()

# --- Starter Reels ---
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    starter_reels = [
        ("👑 100 Crore Ka Niyam", "Gareeb log waqt bechte hain, ameer log assets banakar sote huye kamate hain!", ""),
        ("⚡ Charlie Munger Formula", "Pehla 10 Lakh bachana sabse mushkil hai, uske baad compounding asan ho jati hai!", ""),
        ("🛡️ Warren Buffett 50% Rule", "Faltu cheezon par kharch band karo, compounding magic karegi!", "")
    ]
    for r_title, r_gyan, r_vid in starter_reels:
        cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                       ("OFFICIAL", str(date.today()), r_title, r_gyan, r_vid, 50))
    conn.commit()

# --- Session State ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None
if "failed_attempts" not in st.session_state:
    st.session_state["failed_attempts"] = 0
if "lockout_until" not in st.session_state:
    st.session_state["lockout_until"] = 0
if "selected_future_yrs" not in st.session_state:
    st.session_state["selected_future_yrs"] = 5
if "selected_ig_mins" not in st.session_state:
    st.session_state["selected_ig_mins"] = 30
if "reverse_horizon_yrs" not in st.session_state:
    st.session_state["reverse_horizon_yrs"] = 15
if "current_reel_index" not in st.session_state:
    st.session_state["current_reel_index"] = 0

# --- Login & Sign Up ---
if not st.session_state["logged_user"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("Secure Salted SHA-256 Vault")

    current_time = time.time()
    if current_time < st.session_state["lockout_until"]:
        wait_seconds = int(st.session_state["lockout_until"] - current_time)
        st.error(f"🚨 Security Lock: Please wait {wait_seconds} seconds.")
        st.stop()

    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 New Sign Up"])

    with auth_tab1:
        st.subheader("Login Karein")
        with st.form("login_form"):
            l_phone = st.text_input("Mobile Number (10 digit):", max_chars=10, value="9983204295")
            l_pin = st.text_input("4-digit PIN:", type="password", max_chars=4)
            submit_login = st.form_submit_button("Login Karein 🔓", type="primary")

            if submit_login:
                if len(l_phone) != 10 or not l_phone.isdigit():
                    st.error("10 ank ka valid number dalein!")
                else:
                    cursor.execute("SELECT pin_hash FROM users WHERE phone = ?", (l_phone,))
                    user_data = cursor.fetchone()
                    if user_data:
                        stored_hash = user_data[0]
                        if verify_pin(stored_hash, l_pin):
                            st.session_state["logged_user"] = l_phone
                            st.session_state["failed_attempts"] = 0
                            if "$" not in stored_hash:
                                cursor.execute("UPDATE users SET pin_hash = ? WHERE phone = ?", (hash_pin(l_pin), l_phone))
                                conn.commit()
                            st.success("Login safal raha!")
                            st.rerun()
                        else:
                            st.session_state["failed_attempts"] += 1
                            if st.session_state["failed_attempts"] >= 5:
                                st.session_state["lockout_until"] = time.time() + 60
                                st.error("🚨 5 attempts failed! Locked for 60s.")
                            else:
                                st.error(f"Galat PIN! Attempts left: {5 - st.session_state['failed_attempts']}")
                    else:
                        st.error("Number register nahi hai! 'New Sign Up' karein.")

    with auth_tab2:
        st.subheader("Naya Account Banayein")
        with st.form("signup_form"):
            s_phone = st.text_input("10-digit Mobile Number:", max_chars=10, value="9983204295")
            s_pin = st.text_input("Naya 4-digit PIN:", type="password", max_chars=4)
            s_pin_confirm = st.text_input("Confirm PIN:", type="password", max_chars=4)
            submit_signup = st.form_submit_button("Account Banayein 🚀")

            if submit_signup:
                if len(s_phone) != 10 or not s_phone.isdigit():
                    st.error("10 ank ka number dalein!")
                elif len(s_pin) != 4 or not s_pin.isdigit():
                    st.error("PIN 4 ank ka hona chahiye!")
                elif s_pin != s_pin_confirm:
                    st.error("Dono PIN match nahi huye!")
                else:
                    secure_pin_hash = hash_pin(s_pin)
                    cursor.execute("SELECT phone FROM users WHERE phone = ?", (s_phone,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE users SET pin_hash = ? WHERE phone = ?", (secure_pin_hash, s_phone))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("PIN update hua!")
                        st.rerun()
                    else:
                        cursor.execute("INSERT INTO users (phone, pin_hash, created_at) VALUES (?, ?, ?)",
                                       (s_phone, secure_pin_hash, str(date.today())))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("Account ban gaya!")
                        st.rerun()
    st.stop()

# ==================== Logged In App Interface ====================
ACTIVE_USER = st.session_state["logged_user"]
TARGET = 1000000000  # 100 Crore

with st.sidebar:
    st.title("👤 User Profile")
    st.success(f"Khata: **{ACTIVE_USER}**")
    theme_choice = st.selectbox("Theme:", ["🌟 Royal Gold Dark", "☀️ Bright Light", "🌌 Deep Navy Blue"])
    if st.button("Logout 🔒", type="primary"):
        st.session_state["logged_user"] = None
        st.rerun()

st.markdown("""
    <style>
    .stApp { background-color: #0a0c10 !important; color: #ffffff !important; }
    label, p, h1, h2, h3, span, div { color: #ffffff !important; }
    .vip-card {
        background: linear-gradient(135deg, #1e1b18 0%, #0d0c0a 100%);
        border: 2px solid #e5a93c;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 15px;
    }
    .box-card {
        background: #161a23;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Data Queries
cash_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', daily_amount as 'Raqam (₹)', note as 'Vivran' FROM income_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
exp_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', amount as 'Raqam (₹)', category as 'Category', note as 'Vivran' FROM expense_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
asset_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', asset_type as 'Type', quantity as 'Qty', current_value as 'Value (₹)', note as 'Vivran' FROM assets_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
debt_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', debt_type as 'Type', person_name as 'Naam', amount as 'Raqam (₹)', note as 'Vivran' FROM debt_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))

tot_inc = cash_df["Raqam (₹)"].sum() if not cash_df.empty else 0.0
tot_exp = exp_df["Raqam (₹)"].sum() if not exp_df.empty else 0.0
net_cash = max(tot_inc - tot_exp, 0.0)
tot_asset = asset_df["Value (₹)"].sum() if not asset_df.empty else 0.0

tot_liab = debt_df[debt_df["Type"].str.contains("लायबिलिटी|Liability", case=False, na=False)]["Raqam (₹)"].sum() if not debt_df.empty else 0.0
tot_rec = debt_df[debt_df["Type"].str.contains("एसेट|Asset", case=False, na=False)]["Raqam (₹)"].sum() if not debt_df.empty else 0.0
networth = max(net_cash + tot_asset + tot_rec - tot_liab, 0.0)

today_str = str(date.today())
unique_dates = sorted(cash_df["Tariqh"].unique().tolist(), reverse=True) if not cash_df.empty else []
streak = 0
chk = date.today()
if today_str not in unique_dates: chk = date.today() - timedelta(days=1)
while str(chk) in unique_dates:
    streak += 1
    chk = chk - timedelta(days=1)

st.title("👑 100 Crore Wealth Hub")
st.caption(f"Account: **{ACTIVE_USER[:5]}***** | All Features Restored")

# --- All Tabs ---
(
    tab_dash, tab_elite, tab_ludo, tab_reels, tab_detox, tab_spin, tab_squad,
    tab_lead, tab_cal, tab_fire, tab_roundup, tab_tax, tab_ai, tab_wishlist,
    tab_inc, tab_exp, tab_debt, tab_asset, tab_rev
) = st.tabs([
    "📊 Dashboard", "👑 Top 1%", "🎲 Online Ludo", "📱 Reels", "🔥 Detox",
    "🎯 Daily Spin", "👥 Squad", "🏆 Leaderboard", "📅 Calendar", "🌴 Passive FIRE",
    "🪙 UPI Gold", "⚖️ Tax Buffer", "🧠 AI Coach", "🏎️ Luxury Sim",
    "💵 Income", "💸 Expenses", "⚖️ Karz/Debt", "🥇 Gold/Assets", "🎯 Reverse Goal"
])

# 1. DASHBOARD
with tab_dash:
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Cash In Hand", f"₹{net_cash:,.0f}")
    with c2: st.metric("Gold & Assets", f"₹{tot_asset:,.0f}")
    with c3: st.metric("Karz/Liabilities", f"₹{tot_liab:,.0f}")
    with c4: st.metric("Clean Networth 👑", f"₹{networth:,.0f}")
    prog = min(networth / TARGET, 1.0)
    st.write(f"### 🎯 100 Crore Progress: `{prog * 100:.6f}%`")
    st.progress(prog)

# 2. TOP 1% CLUB & TIME MACHINE
with tab_elite:
    st.subheader("👑 Top 1% Wealth Club & Time Machine")
    badge = "🔱 TITAN" if networth >= 10000000 else "🐺 LONE HUSTLER"
    st.markdown(f"""
    <div class="vip-card">
        <h4 style="color:#e5a93c;">STATUS: {badge}</h4>
        <h1>Networth: ₹{networth:,.0f}</h1>
        <p>Streak: 🔥 {streak} Days Active</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("#### ⏳ Future Time Machine (Buttons):")
    b1, b2, b3, b4 = st.columns(4)
    with b1: 
        if st.button("🚀 3 Saal", key="tm3"): st.session_state["selected_future_yrs"] = 3
    with b2: 
        if st.button("🚀 5 Saal", key="tm5"): st.session_state["selected_future_yrs"] = 5
    with b3: 
        if st.button("🚀 10 Saal", key="tm10"): st.session_state["selected_future_yrs"] = 10
    with b4: 
        if st.button("👑 15 Saal", key="tm15"): st.session_state["selected_future_yrs"] = 15

    y = st.session_state["selected_future_yrs"]
    f_val = networth * ((1 + 0.15)**y) + (10000 * (((1 + 0.0125)**(y * 12) - 1) / 0.0125))
    col1, col2 = st.columns(2)
    with col1: st.metric(f"{y} Saal Baad Networth", f"₹{f_val:,.0f}")
    with col2: st.metric("Monthly Passive Income", f"₹{(f_val * 0.05) / 12:,.0f} / mo")

# 3. ONLINE LUDO
with tab_ludo:
    st.subheader("🎲 Online Multiplayer Ludo Arena")
    cursor.execute("""
        SELECT r.room_code, r.room_name, r.current_turn, r.last_dice 
        FROM ludo_rooms r 
        INNER JOIN ludo_players p ON r.room_code = p.room_code 
        WHERE p.user_phone = ? AND r.status != 'FINISHED'
    """, (ACTIVE_USER,))
    room_data = cursor.fetchone()

    if not room_data:
        cl1, cl2 = st.columns(2)
        with cl1:
            with st.form("create_ludo_form"):
                r_n = st.text_input("Match Name:", value="Champions Battle")
                r_c = st.text_input("4-digit Room Code:", max_chars=4, value="4455")
                if st.form_submit_button("Room Banayein 🎲"):
                    try:
                        cursor.execute("INSERT INTO ludo_rooms (room_code, room_name, host_phone, current_turn) VALUES (?, ?, ?, ?)",
                                       (r_c, r_n, ACTIVE_USER, ACTIVE_USER))
                        cursor.execute("INSERT INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🔴 Red', ?)",
                                       (r_c, ACTIVE_USER, today_str))
                        conn.commit()
                        st.rerun()
                    except Exception: st.error("Code pehle se chuna hua hai!")
        with cl2:
            with st.form("join_ludo_form"):
                j_c = st.text_input("4-digit Code Dalein:", max_chars=4)
                if st.form_submit_button("Join Karein ⚡"):
                    cursor.execute("SELECT room_name FROM ludo_rooms WHERE room_code = ? AND status != 'FINISHED'", (j_c,))
                    if cursor.fetchone():
                        cursor.execute("INSERT OR IGNORE INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🟢 Green', ?)",
                                       (j_c, ACTIVE_USER, today_str))
                        conn.commit()
                        st.rerun()
                    else: st.error("Room nahi mila!")
    else:
        rc, rn, rturn, rdice = room_data
        st.info(f"Room: **{rn}** ({rc}) | Turn: `@{rturn[:5]}*****` | Last Dice: 🎲 {rdice}")
        if rturn == ACTIVE_USER:
            if st.button("🎲 Roll Dice", type="primary"):
                dv = random.randint(1, 6)
                cursor.execute("SELECT token_pos FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, ACTIVE_USER))
                cur_pos = cursor.fetchone()[0]
                n_pos = min(cur_pos + dv, 50)
                p_list = pd.read_sql_query("SELECT user_phone FROM ludo_players WHERE room_code = ?", conn, params=(rc,))['user_phone'].tolist()
                next_p = p_list[(p_list.index(ACTIVE_USER) + 1) % len(p_list)]
                cursor.execute("UPDATE ludo_players SET token_pos = ? WHERE room_code = ? AND user_phone = ?", (n_pos, rc, ACTIVE_USER))
                cursor.execute("UPDATE ludo_rooms SET current_turn = ?, last_dice = ? WHERE room_code = ?", (next_p, dv, rc))
                conn.commit()
                st.rerun()
        else:
            if st.button("🔄 Refresh Board"): st.rerun()
        if st.button("🚪 Leave Match"):
            cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, ACTIVE_USER))
            conn.commit()
            st.rerun()

# 4. REELS FEED
with tab_reels:
    st.subheader("📱 100 Cr Wealth Reels")
    reels_list = pd.read_sql_query("SELECT id, user_phone, post_date, hook_title, gyan_content, likes_count FROM reels_feed ORDER BY id DESC", conn)
    if not reels_list.empty:
        idx = st.session_state["current_reel_index"] % len(reels_list)
        cur_r = reels_list.iloc[idx]
        rid = int(cur_r['id'])
        c_nav1, c_nav2 = st.columns(2)
        with c_nav1:
            if st.button("⬆️ Previous", key="prev_r"):
                st.session_state["current_reel_index"] = (idx - 1) % len(reels_list)
                st.rerun()
        with c_nav2:
            if st.button("⬇️ Next Reel", key="next_r", type="primary"):
                st.session_state["current_reel_index"] = (idx + 1) % len(reels_list)
                st.rerun()
        st.markdown(f"""
        <div class="box-card">
            <h3 style="color:#e5a93c;">{cur_r['hook_title']}</h3>
            <p style="font-size:1.1rem;">{cur_r['gyan_content']}</p>
            <small style="color:#94a3b8;">By @{cur_r['user_phone'][:5]}***** • {cur_r['post_date']}</small>
        </div>
        """, unsafe_allow_html=True)
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button(f"❤️ {cur_r['likes_count']} Likes", key=f"lk_{rid}"):
                cursor.execute("UPDATE reels_feed SET likes_count = likes_count + 1 WHERE id = ?", (rid,))
                conn.commit()
                st.rerun()
        with col_act2:
            if st.button("🪙 Seekha ➔ ₹10 Gold", key=f"gld_{rid}"):
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K Reward)', 0.0013, 10.0, 'Reel Reward')", (ACTIVE_USER, today_str))
                conn.commit()
                st.success("₹10 gold added!")

# 5. REELS DETOX
with tab_detox:
    st.subheader("🔥 Reels Detox Calculator (Buttons)")
    cd1, cd2, cd3, cd4 = st.columns(4)
    with cd1:
        if st.button("15 Min", key="d15"): st.session_state["selected_ig_mins"] = 15
    with cd2:
        if st.button("30 Min", key="d30"): st.session_state["selected_ig_mins"] = 30
    with cd3:
        if st.button("60 Min", key="d60"): st.session_state["selected_ig_mins"] = 60
    with cd4:
        if st.button("120 Min", key="d120"): st.session_state["selected_ig_mins"] = 120
    m = st.session_state["selected_ig_mins"]
    burn = (m / 60.0) * 300.0
    st.error(f"⚠️ {m} minute reels dekhne se ₹{burn:,.0f} ka samay jala diya!")

# 6. DAILY SPIN
with tab_spin:
    st.subheader("🎯 Daily Wealth Roulette Spin")
    cursor.execute("SELECT task_text, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (ACTIVE_USER, today_str))
    ch_data = cursor.fetchone()
    if not ch_data:
        if st.button("🎡 Spin Wheel", type="primary"):
            cursor.execute("INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed) VALUES (?, ?, 'Zero-Waste Day: Aaj koi faltu kharch nahi karna!', 'XP', 100, 0)", (ACTIVE_USER, today_str))
            conn.commit()
            st.rerun()
    else:
        st.info(f"Task: {ch_data[0]}")
        if ch_data[1] == 0:
            if st.button("✅ Task Completed"):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE user_phone = ? AND challenge_date = ?", (ACTIVE_USER, today_str))
                conn.commit()
                st.balloons()
                st.rerun()
        else:
            st.success("Mission Completed!")

# 7. SQUAD
with tab_squad:
    st.subheader("👥 Wealth Squad")
    cursor.execute("SELECT s.squad_name, s.squad_code FROM wealth_squads s INNER JOIN squad_members m ON s.squad_code = m.squad_code WHERE m.user_phone = ?", (ACTIVE_USER,))
    sq_user = cursor.fetchone()
    if sq_user:
        st.success(f"Group: **{sq_user[0]}** | Invite Code: `{sq_user[1]}`")
    else:
        st.info("Naya squad banayein ya code se join karein.")

# 8. LEADERBOARD
with tab_lead:
    st.subheader("🏆 All-India Leaderboard")
    lead_rows = pd.read_sql_query("SELECT phone FROM users LIMIT 10", conn)
    for idx, r in lead_rows.iterrows():
        me = " (आप ⭐)" if r['phone'] == ACTIVE_USER else ""
        st.write(f"**Rank {idx+1}** • `@{r['phone'][:5]}*****`{me} — **🔥 10 Days Streak**")

# 9. CALENDAR
with tab_cal:
    st.subheader("📅 Financial Calendar")
    sel_dt = str(st.date_input("Date Chunein:", value=date.today()))
    d_inc = cash_df[cash_df["Tariqh"] == sel_dt]["Raqam (₹)"].sum() if not cash_df.empty else 0.0
    d_exp = exp_df[exp_df["Tariqh"] == sel_dt]["Raqam (₹)"].sum() if not exp_df.empty else 0.0
    st.metric("Net Daily Savings", f"₹{d_inc - d_exp:,.0f}")

# 10. PASSIVE FIRE
with tab_fire:
    st.subheader("🌴 Passive FIRE Engine")
    st.metric("Monthly Passive Income (4% Rule)", f"₹{(networth * 0.04) / 12:,.0f} / mo")

# 11. UPI GOLD
with tab_roundup:
    st.subheader("🪙 Micro Gold SIP")
    if st.button("🟡 ₹10 Sona Kharidein"):
        cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K Micro SIP)', 0.0013, 10.0, 'Daily SIP')", (ACTIVE_USER, today_str))
        conn.commit()
        st.success("₹10 gold added!")
        st.rerun()

# 12. TAX BUFFER
with tab_tax:
    st.subheader("⚖️ Tax Buffer")
    st.metric("Clean Networth", f"₹{max(net_cash - (tot_inc * 0.15), 0.0) + tot_asset:,.0f}")

# 13. AI COACH
with tab_ai:
    st.subheader("🧠 AI Wealth Coach")
    st.info(f"Namaskar! Aapki networth ₹{networth:,.0f} hai. Daily discipline hi 100 Cr ka rasta hai.")

# 14. LUXURY SIMULATOR
with tab_wishlist:
    st.subheader("🏎️ Luxury Simulator")
    st.progress(min(networth / 8500000, 1.0))
    st.caption("Sports Car Goal Progress")

# 15. INCOME
with tab_inc:
    st.subheader("💵 Income Record")
    with st.form("inc_form_master", clear_on_submit=True):
        i_amt = st.number_input("Amount (₹):", min_value=0.0, step=500.0)
        i_note = st.text_input("Source:", value="Business")
        if st.form_submit_button("Save Income") and i_amt > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)", (ACTIVE_USER, today_str, i_amt, i_note))
            conn.commit()
            st.rerun()
    if not cash_df.empty: st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)

# 16. EXPENSES
with tab_exp:
    st.subheader("💸 Expense Record")
    with st.form("exp_form_master", clear_on_submit=True):
        e_amt = st.number_input("Amount (₹):", min_value=0.0, step=100.0)
        e_note = st.text_input("Category:", value="Daily")
        if st.form_submit_button("Save Expense") and e_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)", (ACTIVE_USER, today_str, e_amt, e_note, e_note))
            conn.commit()
            st.rerun()
    if not exp_df.empty: st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)

# 17. DEBT
with tab_debt:
    st.subheader("⚖️ Karz / Debt Manager")
    if not debt_df.empty: st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)

# 18. ASSETS
with tab_asset:
    st.subheader("🥇 Gold & Assets")
    if not asset_df.empty: st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)

# 19. REVERSE GOAL
with tab_rev:
    st.subheader("🎯 Target Reverse-Engine")
    st.metric("15 Saal me 100 Cr ka Daily Target", f"₹{(TARGET / (15 * 365)):,.0f} / din")
