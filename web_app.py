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

# --- Page Setup ---
st.set_page_config(page_title="100 Cr Wealth Vault", page_icon="👑", layout="centered")

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
cursor.execute("CREATE TABLE IF NOT EXISTS reels_comments (id INTEGER PRIMARY KEY AUTOINCREMENT, reel_id INTEGER, user_phone TEXT, comment_text TEXT, created_date TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS user_saved_reels (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, reel_id INTEGER, saved_date TEXT, UNIQUE(user_phone, reel_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS daily_challenges (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, challenge_date TEXT, task_text TEXT, reward_type TEXT, reward_val REAL, is_completed INTEGER DEFAULT 0, UNIQUE(user_phone, challenge_date))")
cursor.execute("CREATE TABLE IF NOT EXISTS user_loot_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT, loot_date TEXT, nugget TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS ludo_rooms (room_code TEXT PRIMARY KEY, room_name TEXT, host_phone TEXT, status TEXT DEFAULT 'WAITING', current_turn TEXT, last_dice INTEGER DEFAULT 0, winner TEXT DEFAULT '')")
cursor.execute("CREATE TABLE IF NOT EXISTS ludo_players (id INTEGER PRIMARY KEY AUTOINCREMENT, room_code TEXT, user_phone TEXT, color TEXT, token_pos INTEGER DEFAULT 0, joined_at TEXT, UNIQUE(room_code, user_phone))")
cursor.execute("CREATE TABLE IF NOT EXISTS wealth_squads (squad_id INTEGER PRIMARY KEY AUTOINCREMENT, squad_name TEXT, squad_code TEXT UNIQUE, creator_phone TEXT, monthly_target REAL DEFAULT 25000.0)")
cursor.execute("CREATE TABLE IF NOT EXISTS squad_members (id INTEGER PRIMARY KEY AUTOINCREMENT, squad_code TEXT, user_phone TEXT, joined_date TEXT, UNIQUE(squad_code, user_phone))")
conn.commit()

# Starter Reels
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                   ("OFFICIAL", str(date.today()), "👑 100 Crore Mindset", "Gareeb log waqt bechte hain, ameer log assets banakar sote huye kamate hain!", "", 45))
    conn.commit()

# Session State
if "logged_user" not in st.session_state: st.session_state["logged_user"] = None
if "selected_future_yrs" not in st.session_state: st.session_state["selected_future_yrs"] = 5
if "selected_ig_mins" not in st.session_state: st.session_state["selected_ig_mins"] = 30
if "reverse_horizon_yrs" not in st.session_state: st.session_state["reverse_horizon_yrs"] = 15

# Clean Visual Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117 !important;
        color: #f0f6fc !important;
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

    auth_tab1, auth_tab2 = st.tabs(["🔑 Safe Login", "📝 New Account"])
    with auth_tab1:
        with st.form("login_form"):
            l_phone = st.text_input("Mobile No:", max_chars=10, value="9983204295")
            l_pin = st.text_input("4-Digit PIN:", type="password", max_chars=4)
            if st.form_submit_button("LOGIN 🔓", type="primary", use_container_width=True):
                cursor.execute("SELECT pin_hash FROM users WHERE phone = ?", (l_phone,))
                res = cursor.fetchone()
                if res and verify_pin(res[0], l_pin):
                    st.session_state["logged_user"] = l_phone
                    st.rerun()
                else: st.error("Galat PIN ya number!")

    with auth_tab2:
        with st.form("signup_form"):
            s_phone = st.text_input("10-Digit Mobile:", max_chars=10, value="9983204295")
            s_pin = st.text_input("Choose 4-Digit PIN:", type="password", max_chars=4)
            s_pin2 = st.text_input("Confirm PIN:", type="password", max_chars=4)
            if st.form_submit_button("CREATE ACCOUNT 🚀", use_container_width=True):
                if s_pin == s_pin2 and len(s_pin) == 4:
                    h = hash_pin(s_pin)
                    cursor.execute("INSERT OR REPLACE INTO users (phone, pin_hash, created_at) VALUES (?, ?, ?)", (s_phone, h, str(date.today())))
                    conn.commit()
                    st.session_state["logged_user"] = s_phone
                    st.rerun()
                else: st.error("PIN check karein!")
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

# Header Bar
c_head1, c_head2 = st.columns([2, 1])
with c_head1:
    st.write(f"👤 **Vault:** `@{USER[:5]}*****` | 🔥 **Streak:** `{streak} Days`")
with c_head2:
    if st.button("Logout 🔒", use_container_width=True):
        st.session_state["logged_user"] = None
        st.rerun()

# --- TABS WITH HOME AS FIRST TAB ---
(
    tab_home, tab_reels, tab_games, tab_squad, tab_elite, tab_detox,
    tab_coach, tab_rev, tab_cal, tab_fire, tab_roundup, tab_tax,
    tab_wish, tab_inc, tab_exp, tab_debt
) = st.tabs([
    "🏠 Home", "📱 Reels", "🎲 Ludo & Games", "👥 Squad", "👑 Top 1%",
    "🔥 Detox", "🎙️ AI Coach", "🎯 Reverse Goal", "📅 Calendar", "🌴 Passive FIRE",
    "🪙 UPI Gold", "⚖️ Tax Buffer", "🏎️ Luxury Sim", "💵 Income", "💸 Expenses", "⚖️ Karz & Assets"
])

# ==================== 1. HOME (MUKHYA DASHBOARD) ====================
with tab_home:
    prog_pct = min((networth / TARGET) * 100, 100.0)
    
    st.markdown(f"""
        <div class="hero-card">
            <span style="color:#8b949e; font-size:0.85rem; font-weight:700; text-transform:uppercase; letter-spacing:1px;">TOTAL CLEAN NETWORTH</span>
            <h1 style="color:#f59e0b; font-size:2.4rem; margin:6px 0; font-weight:900;">₹{networth:,.0f}</h1>
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#8b949e; margin-top:8px;">
                <span>🎯 Target: ₹100 Crore</span>
                <span style="color:#f59e0b; font-weight:bold;">{prog_pct:.6f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.progress(min(networth / TARGET, 1.0))

    # Live Stat Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat-tile"><small style="color:#8b949e;">CASH IN HAND</small><h3 style="color:#22c55e; margin:4px 0;">₹{net_cash:,.0f}</h3></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-tile"><small style="color:#8b949e;">GOLD & ASSETS</small><h3 style="color:#eab308; margin:4px 0;">₹{asset_val:,.0f}</h3></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-tile"><small style="color:#8b949e;">LIABILITIES</small><h3 style="color:#ef4444; margin:4px 0;">₹{tot_liab:,.0f}</h3></div>""", unsafe_allow_html=True)

    st.write("---")
    st.markdown("#### ⚡ Quick Action Booster")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("🟡 ₹10 Sona Kharidein (1-Tap)", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K)', 0.0013, 10.0, 'Home SIP')", (USER, today_str))
            conn.commit()
            st.success("₹10 ka 24K Sona jud gaya!")
            st.rerun()
    with col_q2:
        if st.button("🔥 Reels Detox (+₹20 Sona)", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Detox)', 0.0026, 20.0, 'Detox Reward')", (USER, today_str))
            conn.commit()
            st.success("₹20 Gold jud gaya!")
            st.rerun()

# ==================== 2. REELS (WITH UPLOAD & SHARE) ====================
with tab_reels:
    st.markdown("### 📱 100 Cr Wealth Reels & Community")
    with st.expander("➕ Nayi Reel Banayein / Upload Karein", expanded=False):
        with st.form("create_reel_f", clear_on_submit=True):
            r_title = st.text_input("Reel Title / Hook:", placeholder="Jaise: 90% log ye galti karte hain...")
            r_text = st.text_area("Gyan / Wealth Lesson:", placeholder="Apna lesson likhein jo dusron ko inspire kare...")
            r_file = st.file_uploader("Upload Video (MP4 / MOV, Max 40MB):", type=["mp4", "mov"])
            if st.form_submit_button("🚀 Publish Reel", type="primary", use_container_width=True):
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
                    st.success("Aapki reel publish ho gayi!")
                    st.rerun()
                else: st.error("Title aur text zaroor bharein!")

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
                if st.button("🪙 ₹10 Gold", key=f"rg_{r['id']}", use_container_width=True):
                    cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Reel Reward)', 0.0013, 10.0, 'Reel Reward')", (USER, today_str))
                    conn.commit()
                    st.success("₹10 Gold mila!")
            with c_act3:
                share_msg = f"🔥 100 Crore Mindset Reel:\n*{r['hook_title']}*\n\n\"{r['gyan_content']}\"\n\nJoin 100 Crore Vault App: https://100-crore-target.streamlit.app"
                wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(share_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; font-weight:bold; border:none; padding:8px; border-radius:10px; cursor:pointer;">📲 WhatsApp Share</button></a>', unsafe_allow_html=True)
            st.write("---")

# ==================== 3. GAMES & LUDO ====================
with tab_games:
    st.markdown("### 🎲 Online Multi-Player Ludo")
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
                r_code = st.text_input("Room Code:", max_chars=4, value="4455")
                if st.form_submit_button("Room Banayein 🎲", use_container_width=True):
                    try:
                        cursor.execute("INSERT INTO ludo_rooms (room_code, room_name, host_phone, current_turn) VALUES (?, 'Battle Arena', ?, ?)", (r_code, USER, USER))
                        cursor.execute("INSERT INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🔴 Red', ?)", (r_code, USER, today_str))
                        conn.commit()
                        st.rerun()
                    except Exception: st.error("Code pehle se chuna hai!")
        with c_l2:
            with st.form("ludo_join_f"):
                j_code = st.text_input("Friend Code:", max_chars=4)
                if st.form_submit_button("Join Match ⚡", use_container_width=True):
                    cursor.execute("INSERT OR IGNORE INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🟢 Green', ?)", (j_code, USER, today_str))
                    conn.commit()
                    st.rerun()
    else:
        rc, rn, rturn, rdice = room_data
        st.info(f"Room: **{rc}** | Turn: `@{rturn[:5]}*****` | Last Dice: 🎲 {rdice}")
        if rturn == USER:
            if st.button("ROLL DICE 🎲", type="primary", use_container_width=True):
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
            if st.button("🔄 Refresh Turn", use_container_width=True): st.rerun()

        if st.button("Leave Match", use_container_width=True):
            cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, USER))
            conn.commit()
            st.rerun()

    st.write("---")
    st.markdown("### 🎡 Daily Wealth Spin")
    cursor.execute("SELECT task_text, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (USER, today_str))
    ch_data = cursor.fetchone()
    if not ch_data:
        if st.button("SPIN TODAY'S WHEEL 🎯", type="primary", use_container_width=True):
            cursor.execute("INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed) VALUES (?, ?, 'Zero Faltu Kharch: Aaj bahar koi chai-nashta nahi!', 'XP', 100, 0)", (USER, today_str))
            conn.commit()
            st.rerun()
    else:
        st.info(f"📌 Mission: {ch_data[0]}")
        if ch_data[1] == 0:
            if st.button("✅ Claim Done (+100 XP)", use_container_width=True):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE user_phone = ? AND challenge_date = ?", (USER, today_str))
                conn.commit()
                st.balloons()
                st.rerun()
        else: st.success("✅ Mission Completed!")

# ==================== 4. SQUAD & LEADERBOARD ====================
with tab_squad:
    st.subheader("👥 Wealth Squad")
    cursor.execute("SELECT s.squad_name, s.squad_code FROM wealth_squads s INNER JOIN squad_members m ON s.squad_code = m.squad_code WHERE m.user_phone = ?", (USER,))
    sq_user = cursor.fetchone()
    if sq_user:
        st.success(f"Group: **{sq_user[0]}** | Invite Code: `{sq_user[1]}`")
    else:
        with st.form("sq_f"):
            sn = st.text_input("Squad Name:")
            sc = st.text_input("4-Digit Code:", max_chars=4)
            if st.form_submit_button("Create Squad 🛡️", use_container_width=True) and sn and len(sc) == 4:
                try:
                    cursor.execute("INSERT INTO wealth_squads (squad_name, squad_code, creator_phone) VALUES (?, ?, ?)", (sn, sc, USER))
                    cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)", (sc, USER, today_str))
                    conn.commit()
                    st.rerun()
                except Exception: st.error("Code used!")

    st.write("---")
    st.subheader("🏆 All-India Leaderboard")
    lead_rows = pd.read_sql_query("SELECT phone FROM users LIMIT 8", conn)
    for idx, r in lead_rows.iterrows():
        me = " (आप ⭐)" if r['phone'] == USER else ""
        st.write(f"**Rank {idx+1}** • `@{r['phone'][:5]}*****`{me} — **🔥 Active**")

# ==================== 5. TOP 1% CLUB ====================
with tab_elite:
    st.subheader("👑 Top 1% Wealth Club")
    badge = "🔱 TITAN" if networth >= 10000000 else "🐺 LONE HUSTLER"
    st.markdown(f"""
    <div class="app-card" style="text-align:center;">
        <h4 style="color:#f59e0b;">STATUS: {badge}</h4>
        <h2>Networth: ₹{networth:,.0f}</h2>
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
    st.metric(f"{y} Saal Baad Networth", f"₹{f_val:,.0f}")

# ==================== 6. DETOX ====================
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

# ==================== 7. AI COACH ====================
with tab_coach:
    st.subheader("🎙️ AI Wealth Voice Coach")
    speech_text = f"Namaskar! Aapki networth ₹{networth:,.0f} hai. Daily discipline hi 100 Crore ka rasta hai."
    st.info(f"📜 {speech_text}")
    safe_speech_js = speech_text.replace('"', '\\"').replace('\n', ' ')
    audio_html = f"""
    <div style="text-align: center; margin-top: 10px;">
        <button onclick="speakAudio()" style="background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%); color: #111; font-weight: bold; border: none; padding: 10px 24px; border-radius: 20px; cursor: pointer;">
            🔊 Audio Coach Suney (Play)
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

# ==================== 8. REVERSE GOAL ====================
with tab_rev:
    st.subheader("🎯 100 Crore Reverse-Engine Goal")
    r1, r2, r3 = st.columns(3)
    with r1:
        if st.button("⏱️ 10 Saal", key="rv10"): st.session_state["reverse_horizon_yrs"] = 10
    with r2:
        if st.button("⏱️ 15 Saal", key="rv15"): st.session_state["reverse_horizon_yrs"] = 15
    with r3:
        if st.button("⏱️ 20 Saal", key="rv20"): st.session_state["reverse_horizon_yrs"] = 20
    sy = st.session_state["reverse_horizon_yrs"]
    st.metric(f"{sy} Saal me 100 Cr ka Daily Target", f"₹{(TARGET / (sy * 365)):,.0f} / din")

# ==================== 9. CALENDAR ====================
with tab_cal:
    st.subheader("📅 Financial Calendar Diary")
    sel_dt = str(st.date_input("Date Chunein:", value=date.today()))
    d_inc = cash_df[cash_df["Tariqh"] == sel_dt]["Raqam (₹)"].sum() if not cash_df.empty else 0.0
    d_exp = exp_df[exp_df["Tariqh"] == sel_dt]["Raqam (₹)"].sum() if not exp_df.empty else 0.0
    st.metric("Net Daily Savings", f"₹{d_inc - d_exp:,.0f}")

# ==================== 10. PASSIVE FIRE ====================
with tab_fire:
    st.subheader("🌴 Passive FIRE Engine")
    st.metric("Monthly Passive Income (4% Rule)", f"₹{(networth * 0.04) / 12:,.0f} / mo")

# ==================== 11. UPI GOLD ====================
with tab_roundup:
    st.subheader("🪙 Micro Gold SIP")
    if st.button("🟡 ₹10 Sona Kharidein"):
        cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K Micro SIP)', 0.0013, 10.0, 'Daily SIP')", (USER, today_str))
        conn.commit()
        st.success("₹10 gold added!")
        st.rerun()

# ==================== 12. TAX BUFFER ====================
with tab_tax:
    st.subheader("⚖️ Tax Buffer & Clean Wealth")
    st.metric("Clean In-Hand Networth", f"₹{max(net_cash - (inc_val * 0.15), 0.0) + asset_val:,.0f}")

# ==================== 13. LUXURY SIMULATOR ====================
with tab_wish:
    st.subheader("🏎️ Luxury Simulator")
    st.progress(min(networth / 8500000, 1.0))
    st.caption("Sports Car Goal Progress")

# ==================== 14. INCOME ====================
with tab_inc:
    st.subheader("💵 Income Record")
    with st.form("inc_form_master", clear_on_submit=True):
        i_amt = st.number_input("Amount (₹):", min_value=0.0, step=500.0)
        i_note = st.text_input("Source / Note:", value="Business")
        if st.form_submit_button("Save Income") and i_amt > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)", (USER, today_str, i_amt, i_note))
            conn.commit()
            st.rerun()
    if not cash_df.empty: st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)

# ==================== 15. EXPENSES ====================
with tab_exp:
    st.subheader("💸 Expense Record")
    with st.form("exp_form_master", clear_on_submit=True):
        e_amt = st.number_input("Amount (₹):", min_value=0.0, step=100.0)
        e_note = st.text_input("Category / Note:", value="Daily")
        if st.form_submit_button("Save Expense") and e_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)", (USER, today_str, e_amt, e_note, e_note))
            conn.commit()
            st.rerun()
    if not exp_df.empty: st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)

# ==================== 16. KARZ & ASSETS ====================
with tab_debt:
    st.subheader("⚖️ Karz, Debt & Physical Assets")
    st.write("#### Assets:")
    if not asset_df.empty: st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
    st.write("#### Liabilities (Karz):")
    if not debt_df.empty: st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
