import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import os
import hashlib
import hmac
import time

# --- Page Setup (Mobile Native App Look) ---
st.set_page_config(page_title="100 Cr Wealth Vault", page_icon="👑", layout="centered", initial_sidebar_state="collapsed")

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
conn.commit()

# Starter Reels Check
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                   ("OFFICIAL", str(date.today()), "👑 100 Crore Mindset", "Gareeb log waqt bechte hain, ameer log assets banate hain!", "", 45))
    conn.commit()

# Session States
if "logged_user" not in st.session_state: st.session_state["logged_user"] = None
if "failed_attempts" not in st.session_state: st.session_state["failed_attempts"] = 0
if "lockout_until" not in st.session_state: st.session_state["lockout_until"] = 0
if "nav_bar" not in st.session_state: st.session_state["nav_bar"] = "🏠 Vault"

# --- Mobile App CSS Styling (Glow Cards, Glassmorphism, App Feel) ---
st.markdown("""
<style>
    /* Mobile App Background & Fonts */
    .stApp {
        background-color: #0b0e14 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Top Bar */
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 4px 14px 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 15px;
    }
    
    /* Native App Cards */
    .app-card {
        background: linear-gradient(145deg, #151a24 0%, #0e121a 100%);
        border: 1px solid rgba(229, 169, 60, 0.25);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    }
    
    .networth-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .networth-val {
        color: #f59e0b;
        font-size: 2.1rem;
        font-weight: 900;
        margin: 4px 0 10px 0;
    }
    
    /* Grid Stat Tiles */
    .stat-tile {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 12px;
        text-align: center;
    }
    .stat-label { font-size: 0.75rem; color: #94a3b8; font-weight: 600; }
    .stat-num { font-size: 1.15rem; color: #ffffff; font-weight: 800; margin-top: 4px; }
    
    /* Quick Action Pill Buttons */
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 10px 18px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
    }
    
    /* Hide Default Header & Padding for Native App feel */
    header[data-testid="stHeader"] { visibility: hidden; height: 0%; }
    .block-container { padding-top: 1rem !important; padding-bottom: 4rem !important; }
</style>
""", unsafe_allow_html=True)

# --- Login Check ---
if not st.session_state["logged_user"]:
    st.markdown("""
        <div class="app-card" style="text-align:center; border-color: #f59e0b; margin-top: 20px;">
            <h1 style="color: #f59e0b; margin:0;">👑 100 CR VAULT</h1>
            <p style="color: #94a3b8; font-size:0.9rem; margin-top:5px;">Top 1% Financial Operating System</p>
        </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Safe Login", "📝 New Account"])
    with auth_tab1:
        with st.form("login_form"):
            l_phone = st.text_input("Mobile No:", max_chars=10, value="9983204295")
            l_pin = st.text_input("4-Digit PIN:", type="password", max_chars=4)
            if st.form_submit_button("UNLOAD VAULT 🔓", type="primary", use_container_width=True):
                cursor.execute("SELECT pin_hash FROM users WHERE phone = ?", (l_phone,))
                res = cursor.fetchone()
                if res and verify_pin(res[0], l_pin):
                    st.session_state["logged_user"] = l_phone
                    st.rerun()
                else:
                    st.error("Galat PIN ya number!")

    with auth_tab2:
        with st.form("signup_form"):
            s_phone = st.text_input("10-Digit Mobile:", max_chars=10, value="9983204295")
            s_pin = st.text_input("Choose 4-Digit PIN:", type="password", max_chars=4)
            s_pin2 = st.text_input("Confirm PIN:", type="password", max_chars=4)
            if st.form_submit_button("CREATE VAULT 🚀", use_container_width=True):
                if s_pin == s_pin2 and len(s_pin) == 4:
                    h = hash_pin(s_pin)
                    cursor.execute("INSERT OR REPLACE INTO users (phone, pin_hash, created_at) VALUES (?, ?, ?)",
                                   (s_phone, h, str(date.today())))
                    conn.commit()
                    st.session_state["logged_user"] = s_phone
                    st.rerun()
                else: st.error("PIN check karein!")
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

# App Top Header Bar
st.markdown(f"""
    <div class="app-header">
        <div>
            <span style="font-size: 0.8rem; color:#94a3b8; font-weight:700;">USER VAULT</span><br>
            <b style="color:#ffffff; font-size:1.05rem;">@{USER[:5]}*****</b>
        </div>
        <div style="background: rgba(245, 158, 11, 0.15); border:1px solid #f59e0b; padding:4px 12px; border-radius:15px;">
            <span style="color:#f59e0b; font-weight:800; font-size:0.85rem;">👑 ELITE CLUB</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Main App Navigation (Horizontal segmented bar like true mobile app)
nav_choice = st.radio(
    "Navigation",
    ["🏠 Vault", "🎲 Games", "📱 Reels", "💵 Ledger"],
    horizontal=True,
    label_visibility="collapsed"
)

# ----------------- SECTION 1: VAULT (HOME) -----------------
if nav_choice == "🏠 Vault":
    # Hero Networth Card
    prog_pct = min((networth / TARGET) * 100, 100.0)
    st.markdown(f"""
        <div class="app-card" style="border-color: #f59e0b;">
            <div class="networth-title">Current Networth</div>
            <div class="networth-val">₹{networth:,.0f}</div>
            <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#94a3b8; margin-bottom:6px;">
                <span>Goal: ₹100 Crore</span>
                <span style="color:#f59e0b; font-weight:bold;">{prog_pct:.6f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.progress(min(networth / TARGET, 1.0))

    # Grid Tiles (Mini Dash)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div class="stat-tile">
                <div class="stat-label">CASH SAVINGS</div>
                <div class="stat-num" style="color:#22c55e;">₹{max(inc_val - exp_val, 0.0):,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="stat-tile">
                <div class="stat-label">GOLD & ASSETS</div>
                <div class="stat-num" style="color:#eab308;">₹{asset_val:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    # Quick 1-Tap Wealth Boosters
    st.markdown("#### ⚡ 1-Tap Quick Action")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        if st.button("🟡 ₹10 Gold Buy", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (24K)', 0.0013, 10.0, '1-Tap SIP')",
                           (USER, str(date.today())))
            conn.commit()
            st.toast("₹10 Sona jud gaya!")
            st.rerun()
    with q_col2:
        if st.button("🔥 Anti-IG (+₹20 Gold)", use_container_width=True):
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Detox)', 0.0026, 20.0, 'Saved Time')",
                           (USER, str(date.today())))
            conn.commit()
            st.toast("₹20 Gold Detox Reward!")
            st.rerun()

    # Time Machine 1-Tap Button
    st.markdown("#### 🔮 1-Tap Future Calculator")
    t_btn1, t_btn2, t_btn3 = st.columns(3)
    future_yrs = 5
    with t_btn1:
        if st.button("3 Saal", use_container_width=True): future_yrs = 3
    with t_btn2:
        if st.button("5 Saal", use_container_width=True): future_yrs = 5
    with t_btn3:
        if st.button("10 Saal", use_container_width=True): future_yrs = 10

    f_cash = networth * ((1 + 0.15)**future_yrs) + (10000 * (((1 + 0.0125)**(future_yrs * 12) - 1) / 0.0125))
    st.info(f"💡 **{future_yrs} Saal Baad Networth:** ₹{f_cash:,.0f} | **Passive Salary:** ₹{(f_cash*0.04)/12:,.0f}/mahina")

# ----------------- SECTION 2: GAMES (LUDO & SPIN) -----------------
elif nav_choice == "🎲 Games":
    st.markdown("### 🎲 Online Multi-Player Ludo Arena")
    
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
                r_code = st.text_input("4-Digit Room Code:", max_chars=4, value="4455")
                if st.form_submit_button("Create Room 🎲", use_container_width=True):
                    try:
                        cursor.execute("INSERT INTO ludo_rooms (room_code, room_name, host_phone, current_turn) VALUES (?, 'Battle Arena', ?, ?)", (r_code, USER, USER))
                        cursor.execute("INSERT INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🔴 Red', ?)", (r_code, USER, str(date.today())))
                        conn.commit()
                        st.rerun()
                    except Exception: st.error("Code pehle se bana hai!")
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
                <h3 style="color:#38bdf8; margin:0;">MATCH: {rc}</h3>
                <div style="font-size:2.8rem; margin:10px 0;">🎲 {rdice if rdice > 0 else '-'}</div>
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
            if st.button("🔄 Refresh Turn", use_container_width=True): st.rerun()

        if st.button("Leave Match", use_container_width=True):
            cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (rc, USER))
            conn.commit()
            st.rerun()

    st.write("---")
    # Daily Spin Section
    st.markdown("### 🎡 Daily Wealth Spin")
    cursor.execute("SELECT task_text, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (USER, str(date.today())))
    ch_data = cursor.fetchone()
    if not ch_data:
        if st.button("SPIN TODAY'S WHEEL 🎯", type="primary", use_container_width=True):
            cursor.execute("INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed) VALUES (?, ?, 'Zero Faltu Kharch: Aaj koi chai-nashta bahar nahi!', 'XP', 100, 0)",
                           (USER, str(date.today())))
            conn.commit()
            st.rerun()
    else:
        st.info(f"📌 Task: {ch_data[0]}")
        if ch_data[1] == 0:
            if st.button("✅ Claim Done (+100 XP)", use_container_width=True):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE user_phone = ? AND challenge_date = ?", (USER, str(date.today())))
                conn.commit()
                st.balloons()
                st.rerun()
        else:
            st.success("✅ Today's Task Done!")

# ----------------- SECTION 3: REELS -----------------
elif nav_choice == "📱 Reels":
    st.markdown("### 📱 100 Cr Wealth Reels")
    reels = pd.read_sql_query("SELECT id, hook_title, gyan_content, likes_count FROM reels_feed ORDER BY id DESC", conn)
    if not reels.empty:
        for _, r in reels.iterrows():
            st.markdown(f"""
                <div class="app-card" style="border-color:#e5a93c;">
                    <h3 style="color:#f59e0b; margin-top:0;">{r['hook_title']}</h3>
                    <p style="font-size:1.05rem; line-height:1.6; color:#f1f5f9;">{r['gyan_content']}</p>
                </div>
            """, unsafe_allow_html=True)
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                if st.button(f"❤️ {r['likes_count']} Like", key=f"rk_{r['id']}", use_container_width=True):
                    cursor.execute("UPDATE reels_feed SET likes_count = likes_count + 1 WHERE id = ?", (r['id'],))
                    conn.commit()
                    st.rerun()
            with col_l2:
                if st.button("🪙 Seekha ➔ ₹10 Gold", key=f"rg_{r['id']}", use_container_width=True):
                    cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, 'Gold (Gyan)', 0.0013, 10.0, 'Reel')", (USER, str(date.today())))
                    conn.commit()
                    st.toast("₹10 Gold jud gaya!")

# ----------------- SECTION 4: LEDGER -----------------
elif nav_choice == "💵 Ledger":
    st.markdown("### 💵 Quick Income & Expense")
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
