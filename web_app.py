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
        if not stored_hash or "$" not in stored_hash:
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

# --- Database Setup ---
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

# डमी यूज़र्स अगर लीडरबोर्ड नया हो (ताकि यूज़र को कंपटीशन दिखे)
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] <= 1:
    dummy_users = [
        ("9829012345", hash_pin("1234"), "2026-08-01"),
        ("9414098765", hash_pin("1234"), "2026-08-10"),
        ("9166054321", hash_pin("1234"), "2026-08-15")
    ]
    for p, h, dt in dummy_users:
        cursor.execute("INSERT OR IGNORE INTO users (phone, pin_hash, created_at) VALUES (?, ?, ?)", (p, h, dt))
        cursor.execute("INSERT OR IGNORE INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                       (p, str(date.today()), random.randint(2500, 6000), "Business Income"))
    conn.commit()

# --- Starter Reels ---
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    starter_reels = [
        ("👑 100 करोड़ का पहला नियम", "गरीब लोग समय बेचकर कमाते हैं। अमीर लोग एसेट्स (Assets) बनाकर सोते हुए कमाते हैं। आज ही कोई ऐसा एसेट या स्किल शुरू करो जो तुम्हारे बिना भी चले!", ""),
        ("⚡ चार्ली मुंगेर का ₹10 लाख सीक्रेट", "पहला ₹10 लाख बचाना सबसे मुश्किल काम है। चाहे ख़र्चे कम करने पड़ें, इसे पूरा करो। 10 लाख के बाद कम्पाउंडिंग जादू की तरह काम करती है!", ""),
        ("🛡️ वारेन बफ़ेट का 50% रूल", "अगर तुम ऐसी चीज़ें खरीदते हो जिनकी ज़रूरत नहीं है, तो जल्द ही तुम्हें वो चीज़ें बेचनी पड़ेंगी जिनकी सख्त ज़रूरत है। हर ख़र्च पर 24 घंटे सोचो!", "")
    ]
    for r_title, r_gyan, r_vid in starter_reels:
        cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                       ("OFFICIAL", str(date.today()), r_title, r_gyan, r_vid, random.randint(35, 95)))
    conn.commit()

# --- Session State ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None
if "failed_attempts" not in st.session_state:
    st.session_state["failed_attempts"] = 0
if "lockout_until" not in st.session_state:
    st.session_state["lockout_until"] = 0
if "current_reel_index" not in st.session_state:
    st.session_state["current_reel_index"] = 0

# --- Login & Sign Up Screen ---
if not st.session_state["logged_user"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("सैन्य-स्तर (SHA-256 Salted Encryption) से सुरक्षित वित्तीय खाता।")

    current_time = time.time()
    if current_time < st.session_state["lockout_until"]:
        wait_seconds = int(st.session_state["lockout_until"] - current_time)
        st.error(f"🚨 सुरक्षा अलार्म: बहुत अधिक गलत प्रयास! कृपया {wait_seconds} सेकंड प्रतीक्षा करें।")
        st.stop()

    auth_tab1, auth_tab2 = st.tabs(["🔑 सुरक्षित लॉगिन", "📝 नया सुरक्षित खाता"])

    with auth_tab1:
        st.subheader("अपने रजिस्टर्ड नंबर से लॉगिन करें")
        with st.form("login_form"):
            l_phone = st.text_input("मोबाइल नंबर (10 अंक):", max_chars=10, value="9983204295")
            l_pin = st.text_input("अपना 4-अंकों का गुप्त पिन:", type="password", max_chars=4)
            submit_login = st.form_submit_button("सुरक्षित लॉगिन करें 🔓", type="primary")

            if submit_login:
                if len(l_phone) != 10 or not l_phone.isdigit():
                    st.error("कृपया 10 अंकों का मान्य मोबाइल नंबर डालें!")
                else:
                    cursor.execute("SELECT pin_hash FROM users WHERE phone = ?", (l_phone,))
                    user_data = cursor.fetchone()
                    if user_data:
                        stored_hash = user_data[0]
                        if verify_pin(stored_hash, l_pin):
                            st.session_state["logged_user"] = l_phone
                            st.session_state["failed_attempts"] = 0
                            st.success("सफलतापूर्वक अनलॉक हुआ!")
                            st.rerun()
                        else:
                            st.session_state["failed_attempts"] += 1
                            if st.session_state["failed_attempts"] >= 5:
                                st.session_state["lockout_until"] = time.time() + 60
                                st.error("🚨 5 गलत प्रयास! अकाउंट 60 सेकंड के लिए लॉक हो गया।")
                            else:
                                st.error(f"गलत पिन! केवल {5 - st.session_state['failed_attempts']} प्रयास शेष।")
                    else:
                        st.error("यह नंबर पंजीकृत नहीं है! पहले 'नया सुरक्षित खाता' से रजिस्टर करें।")

    with auth_tab2:
        st.subheader("नया एनक्रिप्टेड खाता रजिस्टर करें")
        with st.form("signup_form"):
            s_phone = st.text_input("अपना 10-अंकों का मोबाइल नंबर:", max_chars=10, value="9983204295")
            s_pin = st.text_input("नया 4-अंकों का सीक्रेट पिन बनाएँ:", type="password", max_chars=4)
            s_pin_confirm = st.text_input("पिन दोबारा दर्ज करें:", type="password", max_chars=4)
            submit_signup = st.form_submit_button("सुरक्षित खाता बनाएँ 🚀")

            if submit_signup:
                if len(s_phone) != 10 or not s_phone.isdigit():
                    st.error("कृपया 10 अंकों का वैध मोबाइल नंबर दर्ज करें!")
                elif len(s_pin) != 4 or not s_pin.isdigit():
                    st.error("पिन ठीक 4 अंकों का होना चाहिए!")
                elif s_pin != s_pin_confirm:
                    st.error("दोनों पिन मेल नहीं खा रहे हैं!")
                else:
                    secure_pin_hash = hash_pin(s_pin)
                    cursor.execute("SELECT phone FROM users WHERE phone = ?", (s_phone,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE users SET pin_hash = ? WHERE phone = ?", (secure_pin_hash, s_phone))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("पिन अपडेट हुआ!")
                        st.rerun()
                    else:
                        cursor.execute("INSERT INTO users (phone, pin_hash, created_at) VALUES (?, ?, ?)",
                                       (s_phone, secure_pin_hash, str(date.today())))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("खाता तैयार हो गया!")
                        st.rerun()
    st.stop()

# ==================== यहाँ से आगे केवल लॉगिन यूज़र ====================
ACTIVE_USER = st.session_state["logged_user"]

# Styling
bg_color = "#0a0c10"
text_color = "#ffffff"
accent = "#f59e0b"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    label, p, h1, h2, h3, span, div {{ color: {text_color} !important; }}
    .leaderboard-row {{
        background: linear-gradient(135deg, #161a23 0%, #0d0f14 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .leaderboard-top1 {{
        background: linear-gradient(135deg, #2a1f0a 0%, #151005 100%);
        border: 2px solid #f59e0b !important;
    }}
    .reel-container {{
        background: linear-gradient(180deg, #161a23 0%, #0d0f14 100%);
        border: 2px solid #e5a93c;
        border-radius: 20px;
        padding: 24px;
        min-height: 440px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 15px 35px rgba(0,0,0,0.7);
        margin: 10px 0;
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000

# Top Title
st.title("👑 100 Crore Wealth Hub")
st.caption(f"सुरक्षित सत्र: **{ACTIVE_USER[:5]}***** | अनुशासन, रील्स व 100 Cr मिशन")

# Tabs (नया लीडरबोर्ड टैब जोड़ा गया)
tab_lead, tab_reels, tab_dash, tab_tracker = st.tabs([
    "🏆 एलीट लीडरबोर्ड", 
    "📱 वेल्थ रील्स (Feed)", 
    "📊 मुख्य डैशबोर्ड",
    "💵 कमाई व लेजर"
])

# ----------------- TAB: ALL-INDIA LEADERBOARD (NEW) -----------------
with tab_lead:
    st.subheader("🏆 ऑल-इंडिया वेल्थ अनुशासन लीडरबोर्ड")
    st.caption("यह रैंक आपकी दैनिक नियमितता (Streak) और बचत अनुशासन के आधार पर तय होती है:")

    # सभी यूज़र्स का स्कोर व स्ट्रीक निकालना
    all_users = pd.read_sql_query("SELECT phone FROM users", conn)["phone"].tolist()
    leaderboard_data = []

    for u in all_users:
        u_inc = pd.read_sql_query("SELECT entry_date, daily_amount FROM income_history WHERE user_phone = ?", conn, params=(u,))
        u_exp = pd.read_sql_query("SELECT amount FROM expense_history WHERE user_phone = ?", conn, params=(u,))
        
        tot_inc = u_inc["daily_amount"].sum() if not u_inc.empty else 0.0
        tot_exp = u_exp["amount"].sum() if not u_exp.empty else 0.0
        
        # स्ट्रीक की गणना
        u_dates = sorted(u_inc["entry_date"].unique().tolist(), reverse=True) if not u_inc.empty else []
        u_streak = 0
        chk = date.today()
        if str(chk) not in u_dates:
            chk = date.today() - timedelta(days=1)
        while str(chk) in u_dates:
            u_streak += 1
            chk = chk - timedelta(days=1)
            
        # अनुशासन स्कोर (स्ट्रीक * 50 + बचत दर)
        sav_rate = ((tot_inc - tot_exp) / tot_inc * 100) if tot_inc > 0 else 0.0
        discipline_score = int(u_streak * 50 + sav_rate)
        
        masked_phone = f"{u[:5]}*****"
        leaderboard_data.append({
            "phone": u,
            "masked_phone": masked_phone,
            "streak": u_streak,
            "score": discipline_score
        })

    lead_df = pd.DataFrame(leaderboard_data).sort_values(by="score", ascending=False).reset_index(drop=True)

    # टॉप 10 लीडरबोर्ड कार्ड्स
    for rank, row in lead_df.iterrows():
        r_num = rank + 1
        is_current_user = (row["phone"] == ACTIVE_USER)
        
        if r_num == 1:
            badge = "👑 रैंक 1 (Grand Titan)"
            card_class = "leaderboard-row leaderboard-top1"
        elif r_num == 2:
            badge = "🥈 रैंक 2 (Master Architect)"
            card_class = "leaderboard-row"
        elif r_num == 3:
            badge = "🥉 रैंक 3 (Elite Hustler)"
            card_class = "leaderboard-row"
        else:
            badge = f"रैंक {r_num}"
            card_class = "leaderboard-row"

        highlight = " (आप ⭐)" if is_current_user else ""
        
        st.markdown(f"""
        <div class="{card_class}">
            <div>
                <b style="color: #e5a93c; font-size: 1.05rem;">{badge}</b><br>
                <span style="color: #f1f5f9; font-size: 1.1rem; font-weight: bold;">{row['masked_phone']}{highlight}</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #f59e0b; font-weight: bold; font-size: 1.1rem;">🔥 {row['streak']} दिन स्ट्रीक</span><br>
                <small style="color: #94a3b8;">अनुशासन स्कोर: <b>{row['score']} XP</b></small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **रैंक बढ़ाने का सीक्रेट:** रोज़ अपनी कमाई और बचत दर्ज करें। हर दिन स्ट्रीक बढ़ने से आपका स्कोर 50 XP बढ़ जाता है!")

# ----------------- TAB: REELS FEED -----------------
with tab_reels:
    reels_list = pd.read_sql_query("SELECT id, user_phone, post_date, hook_title, gyan_content, video_filename, likes_count FROM reels_feed ORDER BY id DESC", conn)

    if not reels_list.empty:
        total_reels = len(reels_list)
        idx = st.session_state["current_reel_index"] % total_reels
        current_reel = reels_list.iloc[idx]
        reel_id = int(current_reel['id'])

        col_nav1, col_nav2, col_nav3 = st.columns([1.5, 2, 1.5])
        with col_nav1:
            if st.button("⬆️ पिछली रील", use_container_width=True, key="prev_reel"):
                st.session_state["current_reel_index"] = (idx - 1) % total_reels
                st.rerun()
        with col_nav2:
            st.markdown(f"<p style='text-align: center; margin-top: 8px; font-weight: bold; color: #94a3b8;'>रील {idx + 1} / {total_reels}</p>", unsafe_allow_html=True)
        with col_nav3:
            if st.button("⬇️ अगली रील", use_container_width=True, key="next_reel", type="primary"):
                st.session_state["current_reel_index"] = (idx + 1) % total_reels
                st.rerun()

        st.markdown(f"""
        <div class="reel-container">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #e5a93c; font-weight: bold;">👤 @{current_reel['user_phone'][:6]}***</span>
                    <span style="color: #64748b; font-size: 0.85rem;">📅 {current_reel['post_date']}</span>
                </div>
                <h3 style="color: #e5a93c; margin-bottom: 8px;">{current_reel['hook_title']}</h3>
                <p style="font-size: 1.1rem; line-height: 1.6; color: #f1f5f9;">{current_reel['gyan_content']}</p>
            </div>
            <div style="border-top: 1px solid rgba(229, 169, 60, 0.2); padding-top: 10px;">
                <small style="color: #f59e0b;">💡 100 Crore Mindset Hack • स्वाइप करके सीखें</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2, col_act3 = st.columns([1.5, 1.5, 3])
        with col_act1:
            if st.button(f"❤️ {current_reel['likes_count']}", key=f"reel_like_{reel_id}", use_container_width=True):
                cursor.execute("UPDATE reels_feed SET likes_count = likes_count + 1 WHERE id = ?", (reel_id,))
                conn.commit()
                st.rerun()
        with col_act2:
            cursor.execute("SELECT id FROM user_saved_reels WHERE user_phone = ? AND reel_id = ?", (ACTIVE_USER, reel_id))
            is_saved = cursor.fetchone()
            if is_saved:
                if st.button("🔖 Saved", key=f"unsave_reel_{reel_id}", use_container_width=True):
                    cursor.execute("DELETE FROM user_saved_reels WHERE user_phone = ? AND reel_id = ?", (ACTIVE_USER, reel_id))
                    conn.commit()
                    st.rerun()
            else:
                if st.button("🔖 Save", key=f"save_reel_{reel_id}", use_container_width=True):
                    cursor.execute("INSERT OR IGNORE INTO user_saved_reels (user_phone, reel_id, saved_date) VALUES (?, ?, ?)",
                                   (ACTIVE_USER, reel_id, str(date.today())))
                    conn.commit()
                    st.rerun()
        with col_act3:
            if st.button("🪙 ज्ञान सीखा ➔ ₹10 गोल्ड", key=f"gold_learn_{reel_id}", use_container_width=True):
                g_bought = 10.0 / 7650.0
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                               (ACTIVE_USER, str(date.today()), "Gold (24K Gyan Reward)", g_bought, 10.0, f"Learnt from Reel #{reel_id}"))
                conn.commit()
                st.balloons()
                st.success("₹10 का सोना वॉल्ट में जुड़ गया!")

# ----------------- TAB: DASHBOARD -----------------
with tab_dash:
    st.subheader("📊 आपका 100 करोड़ वेल्थ डैशबोर्ड")
    cash_df = pd.read_sql_query("SELECT daily_amount as 'amt' FROM income_history WHERE user_phone = ?", conn, params=(ACTIVE_USER,))
    exp_df = pd.read_sql_query("SELECT amount as 'amt' FROM expense_history WHERE user_phone = ?", conn, params=(ACTIVE_USER,))
    asset_df = pd.read_sql_query("SELECT current_value as 'amt' FROM assets_history WHERE user_phone = ?", conn, params=(ACTIVE_USER,))

    t_inc = cash_df['amt'].sum() if not cash_df.empty else 0.0
    t_exp = exp_df['amt'].sum() if not exp_df.empty else 0.0
    t_net_cash = max(t_inc - t_exp, 0.0)
    t_assets = asset_df['amt'].sum() if not asset_df.empty else 0.0
    networth = t_net_cash + t_assets

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1: st.metric("नकद बचत", f"₹{t_net_cash:,.0f}")
    with col_m2: st.metric("गोल्ड व एसेट्स", f"₹{t_assets:,.0f}")
    with col_m3: st.metric("शुद्ध नेटवर्थ 👑", f"₹{networth:,.0f}")

    st.write(f"### 🎯 100 करोड़ प्रोग्रेस: `{(networth/TARGET)*100:.6f}%`")
    st.progress(min(networth/TARGET, 1.0))

    st.divider()
    if st.button("लॉगआउट करें 🔒"):
        st.session_state["logged_user"] = None
        st.rerun()

# ----------------- TAB: TRACKER -----------------
with tab_tracker:
    st.subheader("💵 दैनिक कमाई व ख़र्च दर्ज करें")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        with st.form("quick_income_form", clear_on_submit=True):
            inc_val = st.number_input("कमाई (₹):", min_value=0.0, step=500.0)
            inc_note = st.text_input("स्रोत / नोट:", value="Business")
            if st.form_submit_button("💾 कमाई सेव करें") and inc_val > 0:
                cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                               (ACTIVE_USER, str(date.today()), inc_val, inc_note))
                conn.commit()
                st.success("कमाई जुड़ गई!")
                st.rerun()

    with col_t2:
        with st.form("quick_expense_form", clear_on_submit=True):
            exp_val = st.number_input("ख़र्च (₹):", min_value=0.0, step=100.0)
            exp_note = st.text_input("श्रेणी:", value="Daily")
            if st.form_submit_button("💸 ख़र्च दर्ज करें") and exp_val > 0:
                cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)",
                               (ACTIVE_USER, str(date.today()), exp_val, exp_note, exp_note))
                conn.commit()
                st.warning("ख़र्च दर्ज हुआ!")
                st.rerun()
