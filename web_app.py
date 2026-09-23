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

# Fix: Agar purani table me 'pin' tha toh 'pin_hash' column jod do
try:
    cursor.execute("ALTER TABLE users ADD COLUMN pin_hash TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

# Agar purane users ke paas 'pin' tha, toh use pin_hash me copy kar do
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

# Starter Reels
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    starter_reels = [
        ("👑 100 Crore Ka Niyam", "Gareeb log waqt bechte hain, ameer log assets banakar sote huye kamate hain!", ""),
        ("⚡ Charlie Munger Formula", "Pehla 10 Lakh bachana sabse mushkil hai, uske baad compounding asan ho jati hai!", "")
    ]
    for r_title, r_gyan, r_vid in starter_reels:
        cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                       ("OFFICIAL", str(date.today()), r_title, r_gyan, r_vid, 45))
    conn.commit()

# --- Session State ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None
if "failed_attempts" not in st.session_state:
    st.session_state["failed_attempts"] = 0
if "lockout_until" not in st.session_state:
    st.session_state["lockout_until"] = 0

# --- Login & Sign Up Screen ---
if not st.session_state["logged_user"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("Secure SHA-256 Vault")

    current_time = time.time()
    if current_time < st.session_state["lockout_until"]:
        wait_seconds = int(st.session_state["lockout_until"] - current_time)
        st.error(f"🚨 Security Lock: Kripya {wait_seconds} seconds wait karein.")
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
                    st.error("10 ank ka sahi number dalein!")
                else:
                    cursor.execute("SELECT pin_hash FROM users WHERE phone = ?", (l_phone,))
                    user_data = cursor.fetchone()
                    if user_data:
                        stored_hash = user_data[0]
                        if verify_pin(stored_hash, l_pin):
                            st.session_state["logged_user"] = l_phone
                            st.session_state["failed_attempts"] = 0
                            st.success("Login safal raha!")
                            st.rerun()
                        else:
                            st.session_state["failed_attempts"] += 1
                            if st.session_state["failed_attempts"] >= 5:
                                st.session_state["lockout_until"] = time.time() + 60
                                st.error("🚨 5 baar galat PIN! Account 60s ke liye lock hua.")
                            else:
                                st.error(f"Galat PIN! Koshish bachi: {5 - st.session_state['failed_attempts']}")
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
                    st.error("10 digit valid number dalein!")
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

# ==================== Logged In App ====================
ACTIVE_USER = st.session_state["logged_user"]
TARGET = 1000000000

st.title("👑 100 Crore Wealth Hub")
st.caption(f"User: **{ACTIVE_USER[:5]}***** | Online Ludo & Wealth App")

tab_ludo, tab_spin, tab_squad, tab_lead, tab_dash, tab_tracker = st.tabs([
    "🎲 Online Ludo",
    "🎯 Daily Spin",
    "👥 Wealth Squad",
    "🏆 Leaderboard", 
    "📊 Dashboard",
    "💵 Income & Expense"
])

# ----------------- TAB: LUDO -----------------
with tab_ludo:
    st.subheader("🎲 100 Crore Online Ludo Arena")
    cursor.execute("""
        SELECT r.room_code, r.room_name, r.status, r.current_turn, r.last_dice, r.winner
        FROM ludo_rooms r
        INNER JOIN ludo_players p ON r.room_code = p.room_code
        WHERE p.user_phone = ? AND r.status != 'FINISHED'
    """, (ACTIVE_USER,))
    joined_room = cursor.fetchone()

    if not joined_room:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🛡️ Room Banayein")
            with st.form("create_ludo_form", clear_on_submit=True):
                r_name = st.text_input("Match Name:", placeholder="Champions Battle")
                r_code = st.text_input("4-digit Code:", max_chars=4, placeholder="4455")
                if st.form_submit_button("Room Banayein 🎲", type="primary") and r_name and len(r_code) == 4:
                    try:
                        cursor.execute("INSERT INTO ludo_rooms (room_code, room_name, host_phone, current_turn) VALUES (?, ?, ?, ?)",
                                       (r_code, r_name, ACTIVE_USER, ACTIVE_USER))
                        cursor.execute("INSERT INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🔴 Red', ?)",
                                       (r_code, ACTIVE_USER, str(date.today())))
                        conn.commit()
                        st.rerun()
                    except Exception:
                        st.error("Code pehle se chuna hua hai!")

        with c2:
            st.markdown("#### 🤝 Room Join Karein")
            with st.form("join_ludo_form", clear_on_submit=True):
                join_c = st.text_input("4-digit Room Code Dalein:", max_chars=4)
                if st.form_submit_button("Join Karein ⚡") and len(join_c) == 4:
                    cursor.execute("SELECT room_name FROM ludo_rooms WHERE room_code = ? AND status != 'FINISHED'", (join_c,))
                    if cursor.fetchone():
                        cursor.execute("INSERT OR IGNORE INTO ludo_players (room_code, user_phone, color, joined_at) VALUES (?, ?, '🟢 Green', ?)",
                                       (join_c, ACTIVE_USER, str(date.today())))
                        conn.commit()
                        st.rerun()
                    else:
                        st.error("Room nahi mila!")
    else:
        r_code, r_name, r_status, r_turn, r_dice, r_winner = joined_room
        st.info(f"Room: **{r_name}** ({r_code}) | Turn: `@{r_turn[:5]}*****` | Last Dice: 🎲 {r_dice}")

        if r_turn == ACTIVE_USER:
            if st.button("🎲 Dice Phenkein (Roll Dice)", type="primary"):
                dice_v = random.randint(1, 6)
                cursor.execute("SELECT token_pos FROM ludo_players WHERE room_code = ? AND user_phone = ?", (r_code, ACTIVE_USER))
                c_pos = cursor.fetchone()[0]
                n_pos = min(c_pos + dice_v, 50)

                # Players turn switch
                p_list = pd.read_sql_query("SELECT user_phone FROM ludo_players WHERE room_code = ?", conn, params=(r_code,))['user_phone'].tolist()
                next_p = p_list[(p_list.index(ACTIVE_USER) + 1) % len(p_list)]

                cursor.execute("UPDATE ludo_players SET token_pos = ? WHERE room_code = ? AND user_phone = ?", (n_pos, r_code, ACTIVE_USER))
                cursor.execute("UPDATE ludo_rooms SET current_turn = ?, last_dice = ? WHERE room_code = ?", (next_p, dice_v, r_code))
                conn.commit()
                st.rerun()
        else:
            st.caption("Doosre player ka turn hai...")
            if st.button("🔄 Refresh"): st.rerun()

        if st.button("🚪 Match Chhodein"):
            cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (r_code, ACTIVE_USER))
            conn.commit()
            st.rerun()

# ----------------- TAB: DASHBOARD -----------------
with tab_dash:
    st.subheader("📊 100 Crore Dashboard")
    cash_df = pd.read_sql_query("SELECT daily_amount as 'amt' FROM income_history WHERE user_phone = ?", conn, params=(ACTIVE_USER,))
    t_inc = cash_df['amt'].sum() if not cash_df.empty else 0.0
    st.metric("Networth", f"₹{t_inc:,.0f}")
    st.progress(min(t_inc / TARGET, 1.0))
    if st.button("Logout 🔒"):
        st.session_state["logged_user"] = None
        st.rerun()

# ----------------- TAB: TRACKER -----------------
with tab_tracker:
    st.subheader("💵 Income Record")
    with st.form("inc_form", clear_on_submit=True):
        amt = st.number_input("Amount (₹):", min_value=0.0, step=500.0)
        note = st.text_input("Source:", value="Daily")
        if st.form_submit_button("Save") and amt > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                           (ACTIVE_USER, str(date.today()), amt, note))
            conn.commit()
            st.success("Saved!")
            st.rerun()

# ----------------- OTHER TABS -----------------
with tab_spin: st.write("🎯 Daily Spin Ready!")
with tab_squad: st.write("👥 Wealth Squad Active!")
with tab_lead: st.write("🏆 All-India Leaderboard Running!")
