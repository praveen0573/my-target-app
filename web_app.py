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

# --- Page Setup ---
st.set_page_config(page_title="100 Cr Wealth Vault", page_icon="👑", layout="centered", initial_sidebar_state="collapsed")

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
                   ("OFFICIAL", str(date.today()), "👑 100 Crore Mindset", "Gareeb log waqt bechte hain, ameer log assets banakar sote huye kamate hain!", "", 45))
    conn.commit()

# Session State
if "logged_user" not in st.session_state: st.session_state["logged_user"] = None
if "selected_future_yrs" not in st.session_state: st.session_state["selected_future_yrs"] = 5

# --- Mobile Native CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #0b0e14 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 4px 12px 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 12px;
    }
    .app-card {
        background: linear-gradient(145deg, #151a24 0%, #0e121a 100%);
        border: 1px solid rgba(229, 169, 60, 0.28);
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    }
    .networth-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .networth-val {
        color: #f59e0b;
        font-size: 2.2rem;
        font-weight: 900;
        margin: 4px 0 8px 0;
    }
    .stat-tile {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 12px;
        text-align: center;
    }
    .stat-label { font-size: 0.72rem; color: #94a3b8; font-weight: 600; }
    .stat-num { font-size: 1.15rem; color: #ffffff; font-weight: 800; margin-top: 4px; }
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 8px 14px !important;
    }
    header[data-testid="stHeader"] { visibility: hidden; height: 0%; }
    .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; }
</style>
""", unsafe_allow_html=True)

# Login Guard
if not st.session_state["logged_user"]:
    st.markdown("""
        <div class="app-card" style="text-align:center; border-color: #f59e0b; margin-top: 20px;">
            <h1 style="color: #f59e0b; margin:0;">👑 100 CR VAULT</h1>
            <p style="color: #94a3b8; font-size:0.85rem; margin-top:5px;">Secure Financial Operating System</p>
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
                else: st.error("PIN sahi dalein!")
    st.stop()

# ==================== Logged In App ====================
USER = st.session_state["logged_user"]
TARGET = 1000000000

# Queries
cash_df = pd.read_sql_query("SELECT daily_amount FROM income_history WHERE user_phone = ?", conn, params=(USER,))
exp_df = pd.read_sql_query("SELECT amount FROM expense_history WHERE user_phone = ?", conn, params=(USER,))
asset_df = pd.read_sql_query("SELECT current_value FROM assets_history WHERE user_phone = ?", conn, params=(USER,))

inc_val = cash_df['daily_amount'].sum() if not cash_df.empty else 0.0
exp_val = exp_df['amount'].sum() if not exp_df.empty else 0.0
asset_val = asset_df['current_value'].sum() if not asset_df.empty else 0.0
networth = max(inc_val - exp_val + asset_val, 0.0)

# Top Bar
st.markdown(f"""
    <div class="app-header">
        <div>
            <span style="font-size: 0.75rem; color:#94a3b8; font-weight:700;">USER VAULT</span><br>
            <b style="color:#ffffff; font-size:1.05rem;">@{USER[:5]}*****</b>
        </div>
        <div style="background: rgba(245, 158, 11, 0.15); border:1px solid #f59e0b; padding:4px 10px; border-radius:14px;">
            <span style="color:#f59e0b; font-weight:800; font-size:0.8rem;">👑 100 CR CLUB</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# 5 Native Navigation Tabs
nav_choice = st.radio(
    "Navigation",
    ["🏠 Vault", "📱 Reels Feed", "🎲 Games & Spin", "👥 Squad & Rank", "💵 Ledger"],
    horizontal=True,
    label_visibility="collapsed"
)

# ----------------- 1. VAULT (HOME) -----------------
if nav_choice == "🏠 Vault":
    prog_pct = min((networth / TARGET) * 100, 100.0)
    st.markdown(f"""
        <div class="app-card" style="border-color: #f59e0b;">
            <div class="networth-title">Current Networth</div>
            <div class="networth-val">₹{networth:,.0f}</div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#94a3b8; margin-bottom:4px;">
                <span>100 Cr Mission</span>
                <span style="color:#f59e0b; font-weight:bold;">{prog_pct:.6f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.progress(min(networth / TARGET, 1.0))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="stat-tile"><div class="stat-label">CASH SAVINGS</div><div class="stat-num" style="color:#22c55e;">₹{max(inc_val - exp_val, 0.0):,.0f}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="stat-tile"><div class="stat-label">GOLD & ASSETS</div><div class="stat-num" style="color:#eab308;">₹{asset_val:,.0f}</div></div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown("#### ⚡ 1-Tap Quick Action")
    q1, q2 = st.columns(2)
    with q1:
        if st.button("🟡 ₹10 Gold Buy", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K)', 0.0013, 10.0, '1-Tap SIP')", (USER, str(date.today())))
            conn.commit()
            st.toast("₹10 Sona jud gaya!")
            st.rerun()
    with q2:
        if st.button("🔥 Detox (+₹20 Gold)", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Detox)', 0.0026, 20.0, 'Detox Reward')", (USER, str(date.today())))
            conn.commit()
            st.toast("₹20 Gold Reward!")
            st.rerun()

    st.markdown("#### ⏳ Future Time Machine")
    tb1, tb2, tb3 = st.columns(3)
    with tb1:
        if st.button("3 Saal", use_container_width=True): st.session_state["selected_future_yrs"] = 3
    with tb2:
        if st.button("5 Saal", use_container_width=True): st.session_state["selected_future_yrs"] = 5
    with tb3:
        if st.button("10 Saal", use_container_width=True): st.session_state["selected_future_yrs"] = 10

    fy = st.session_state["selected_future_yrs"]
    fc = networth * ((1 + 0.15)**fy) + (10000 * (((1 + 0.0125)**(fy * 12) - 1) / 0.0125))
    st.info(f"💡 **{fy} Saal Baad Networth:** ₹{fc:,.0f} | **Passive Salary:** ₹{(fc*0.04)/12:,.0f}/mo")

# ----------------- 2. REELS FEED (CREATE & SHARE) -----------------
elif nav_choice == "📱 Reels Feed":
    st.markdown("### 📱 100 Cr Wealth Reels & Community")

    # Reel Create & Upload Expander
    with st.expander("➕ Nayi Reel Banayein / Video Post Karein", expanded=False):
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
                                   (USER, str(date.today()), r_title, r_text, saved_fn))
                    conn.commit()
                    st.toast("Aapki reel publish ho gayi!")
                    st.rerun()
                else: st.error("Title aur text zaroor bharein!")

    # Live Feed
    reels = pd.read_sql_query("SELECT id, user_phone, post_date, hook_title, gyan_content, video_filename, likes_count FROM reels_feed ORDER BY id DESC LIMIT 20", conn)
    if not reels.empty:
        for _, r in reels.iterrows():
            st.markdown(f"""
                <div class="app-card" style="border-color:#e5a93c;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#94a3b8; margin-bottom:4px;">
                        <span style="color:#e5a93c; font-weight:bold;">👤 @{r['user_phone'][:5]}*****</span>
                        <span>📅 {r['post_date']}</span>
                    </div>
                    <h3 style="color:#f59e0b; margin: 4px 0 8px 0;">{r['hook_title']}</h3>
                    <p style="font-size:1.02rem; line-height:1.5; color:#f1f5f9;">{r['gyan_content']}</p>
                </div>
            """, unsafe_allow_html=True)

            if r['video_filename']:
                vp = os.path.join(UPLOADS_DIR, r['video_filename'])
                if os.path.exists(vp): st.video(vp)

            # Action Buttons: Like, Gold, WhatsApp Share
            c_act1, c_act2, c_act3 = st.columns([1.2, 1.4, 2])
            with c_act1:
                if st.button(f"❤️ {r['likes_count']}", key=f"rk_{r['id']}", use_container_width=True):
                    cursor.execute("UPDATE reels_feed SET likes_count = likes_count + 1 WHERE id = ?", (r['id'],))
                    conn.commit()
                    st.rerun()

            with c_act2:
                if st.button("🪙 ₹10 Gold", key=f"rg_{r['id']}", use_container_width=True):
                    cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Reel Reward)', 0.0013, 10.0, 'Reel Reward')", (USER, str(date.today())))
                    conn.commit()
                    st.toast("₹10 Gold mila!")

            with c_act3:
                # WhatsApp Share Link
                share_msg = f"🔥 100 Crore Mindset Reel:\n*{r['hook_title']}*\n\n\"{r['gyan_content']}\"\n\nJoin 100 Crore Vault App: https://100-crore-target.streamlit.app"
                wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(share_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; font-weight:bold; border:none; padding:8px; border-radius:12px; cursor:pointer;">📲 WhatsApp Share</button></a>', unsafe_allow_html=True)

            st.write("---")

# ----------------- 3. GAMES (LUDO & DAILY SPIN) -----------------
elif nav_choice == "🎲 Games & Spin":
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
                r_code = st.text_input("Create 4-Digit Code:", max_chars=4, value="4455")
                if st.form_submit_button("Room Banayein 🎲", use_container_width=True):
                    try:
                        cursor.execute("INSERT INTO ludo_rooms (room_code, room_name, host_phone, current_turn) VALUES (?, 'Battle Arena', ?, ?)", (r_code, USER, USER))
                        cursor.execute("INSERT INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🔴 Red', ?)", (r_code, USER, str(date.today())))
                        conn.commit()
                        st.rerun()
                    except Exception: st.error("Code pehle se chuna hai!")
        with c_l2:
            with st.form("ludo_join_f"):
                j_code = st.text_input("Friend's Code:", max_chars=4)
                if st.form_submit_button("Join Match ⚡", use_container_width=True):
                    cursor.execute("INSERT OR IGNORE INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🟢 Green', ?)", (j_code, USER, str(date.today())))
                    conn.commit()
                    st.rerun()
    else:
        rc, rn, rturn, rdice = room_data
        st.markdown(f"""
            <div class="app-card" style="text-align:center; border-color:#38bdf8;">
                <h3 style="color:#38bdf8; margin:0;">MATCH ROOM: {rc}</h3>
                <div style="font-size:2.6rem; margin:8px 0;">🎲 {rdice if rdice > 0 else '-'}</div>
                <small style="color:#94a3b8;">Turn: @{rturn[:5]}*****</small>
            </div>
        """, unsafe_allow_html=True)

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
            if st.button("🔄 Refresh Board", use_container_width=True): st.rerun()

        if st.button("Leave Match", use_container_width=True):
            cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, USER))
            conn.commit()
            st.rerun()

    st.write("---")
    st.markdown("### 🎡 Daily Wealth Roulette Spin")
    cursor.execute("SELECT task_text, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (USER, str(date.today())))
    ch_data = cursor.fetchone()
    if not ch_data:
        if st.button("SPIN TODAY'S WHEEL 🎯", type="primary", use_container_width=True):
            cursor.execute("INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed) VALUES (?, ?, 'Zero Faltu Kharch: Aaj bahar koi chai-nashta nahi!', 'XP', 100, 0)", (USER, str(date.today())))
            conn.commit()
            st.rerun()
    else:
        st.info(f"📌 Mission: {ch_data[0]}")
        if ch_data[1] == 0:
            if st.button("✅ Claim Done (+100 XP)", use_container_width=True):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE user_phone = ? AND challenge_date = ?", (USER, str(date.today())))
                conn.commit()
                st.toast("Claimed +100 XP!")
                st.rerun()
        else: st.success("✅ Mission Completed!")

# ----------------- 4. SQUAD & LEADERBOARD -----------------
elif nav_choice == "👥 Squad & Rank":
    st.markdown("### 👥 Wealth Squad & Leaderboard")
    cursor.execute("SELECT s.squad_name, s.squad_code FROM wealth_squads s INNER JOIN squad_members m ON s.squad_code = m.squad_code WHERE m.user_phone = ?", (USER,))
    sq_user = cursor.fetchone()
    if sq_user:
        st.success(f"Group: **{sq_user[0]}** | Code: `{sq_user[1]}`")
    else:
        with st.form("sq_f"):
            sn = st.text_input("Squad Name:")
            sc = st.text_input("4-Digit Code:", max_chars=4)
            if st.form_submit_button("Create Squad 🛡️", use_container_width=True) and sn and len(sc) == 4:
                try:
                    cursor.execute("INSERT INTO wealth_squads (squad_name, squad_code, creator_phone) VALUES (?, ?, ?)", (sn, sc, USER))
                    cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)", (sc, USER, str(date.today())))
                    conn.commit()
                    st.rerun()
                except Exception: st.error("Code used!")

    st.write("---")
    st.markdown("### 🏆 All-India Leaderboard")
    lead_rows = pd.read_sql_query("SELECT phone FROM users LIMIT 8", conn)
    for idx, r in lead_rows.iterrows():
        me = " (आप ⭐)" if r['phone'] == USER else ""
        st.write(f"**Rank {idx+1}** • `@{r['phone'][:5]}*****`{me} — **🔥 Active**")

# ----------------- 5. LEDGER (INCOME / EXPENSE) -----------------
elif nav_choice == "💵 Ledger":
    st.markdown("### 💵 Quick Income & Expense Ledger")
    c_in, c_ex = st.columns(2)
    with c_in:
        with st.form("in_f", clear_on_submit=True):
            amt = st.number_input("+ Kamai (₹):", min_value=0.0, step=500.0)
            if st.form_submit_button("Save Kamai 💾", type="primary", use_container_width=True) and amt > 0:
                cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, 'Cash')", (USER, str(date.today()), amt))
                conn.commit()
                st.rerun()
    with c_ex:
        with st.form("ex_f", clear_on_submit=True):
            e_amt = st.number_input("- Kharch (₹):", min_value=0.0, step=100.0)
            if st.form_submit_button("Save Kharch 💸", use_container_width=True) and e_amt > 0:
                cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, 'Daily', 'Kharch')", (USER, str(date.today()), e_amt))
                conn.commit()
                st.rerun()

    st.write("---")
    if st.button("Logout 🔒", use_container_width=True):
        st.session_state["logged_user"] = None
        st.rerun()
