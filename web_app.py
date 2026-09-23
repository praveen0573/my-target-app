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
    CREATE TABLE IF NOT EXISTS user_saved_reels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        reel_id INTEGER,
        saved_date TEXT,
        UNIQUE(user_phone, reel_id)
    )
""")

# Daily Spin Challenge Table
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
conn.commit()

# Starter Reels
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    starter_reels = [
        ("👑 100 करोड़ का पहला नियम", "गरीब लोग समय बेचकर कमाते हैं। अमीर लोग एसेट्स (Assets) बनाकर सोते हुए कमाते हैं। आज ही कोई ऐसा एसेट या स्किल शुरू करो जो तुम्हारे बिना भी चले!", ""),
        ("⚡ चार्ली मुंगेर का ₹10 लाख सीक्रेट", "पहला ₹10 लाख बचाना सबसे मुश्किल काम है। चाहे ख़र्चे कम करने पड़ें, इसे पूरा करो। 10 लाख के बाद कम्पाउंडिंग जादू की तरह काम करती है!", "")
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
    st.caption("सैन्य-स्तर (SHA-256 Encryption) से सुरक्षित वित्तीय खाता।")

    current_time = time.time()
    if current_time < st.session_state["lockout_until"]:
        wait_seconds = int(st.session_state["lockout_until"] - current_time)
        st.error(f"🚨 सुरक्षा अलार्म: कृपया {wait_seconds} सेकंड प्रतीक्षा करें।")
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
            s_phone = st.text_input("अपना 10-अंकों का मोबाइल नंबर डालें:", max_chars=10, value="9983204295")
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

# ==================== Logged In User Interface ====================
ACTIVE_USER = st.session_state["logged_user"]

# Styling
bg_color = "#0a0c10"
text_color = "#ffffff"
accent = "#f59e0b"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    label, p, h1, h2, h3, span, div {{ color: {text_color} !important; }}
    .spin-box {{
        background: linear-gradient(135deg, #1f1b2e 0%, #110d1a 100%);
        border: 2px solid #a855f7;
        border-radius: 18px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(168, 85, 247, 0.25);
        margin-bottom: 20px;
    }}
    .task-card {{
        background: #171d2b;
        border: 1px solid #38bdf8;
        border-radius: 14px;
        padding: 18px;
        margin-top: 15px;
        text-align: left;
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000

st.title("👑 100 Crore Wealth Hub")
st.caption(f"यूज़र: **{ACTIVE_USER[:5]}***** | डेली वेल्थ स्पिन, स्क्वाड व 100 Cr मिशन")

# Tabs
tab_spin, tab_squad, tab_lead, tab_reels, tab_dash, tab_tracker = st.tabs([
    "🎯 डेली वेल्थ स्पिन",
    "👥 वेल्थ स्क्वाड",
    "🏆 एलीट लीडरबोर्ड", 
    "📱 वेल्थ रील्स (Feed)", 
    "📊 मुख्य डैशबोर्ड",
    "💵 कमाई व लेजर"
])

# ----------------- TAB: DAILY WEALTH SPIN & CHALLENGE (NEW) -----------------
with tab_spin:
    st.subheader("🎯 डेली वेल्थ रूले व सीक्रेट चैलेंज")
    st.caption("दिन में सिर्फ़ 1 बार स्पिन करें—आज का टास्क पूरा करके XP और गोल्ड कमाएँ!")

    today_str = str(date.today())
    cursor.execute("SELECT id, task_text, reward_type, reward_val, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (ACTIVE_USER, today_str))
    today_challenge = cursor.fetchone()

    available_tasks = [
        ("☕ ज़ीरो-वेस्ट चाय/नाश्ता मिशन: आज बाहर कोई फ़ालतू ख़र्च नहीं करना!", "GOLD", 20.0),
        ("📚 60 मिनट डीप वर्क: आज 1 घंटा बिना सोशल मीडिया के अपने हुनर/काम पर ध्यान दें!", "XP", 150.0),
        ("🪙 चिल्लर बचत: आज अपने वॉलेट से ₹30 बचाकर सीधे डिजिटल गोल्ड में लॉक करें!", "GOLD", 30.0),
        ("🤝 1 नया कस्टमर आउटरीच: आज अपने बिज़नेस/काम के लिए 1 नए व्यक्ति से संपर्क करें!", "XP", 200.0),
        ("✂️ ख़र्च ऑडिट: आज रात सोने से पहले दिन भर का एक-एक रुपया ऐप में दर्ज करें!", "XP", 100.0)
    ]

    if not today_challenge:
        st.markdown("""
        <div class="spin-box">
            <h2 style="color: #a855f7; margin-bottom: 6px;">🎰 आज का वेल्थ व्हील अनलॉक करें</h2>
            <p style="color: #cbd5e1; font-size: 1.05rem;">स्पिन बटन दबाते ही आज का सीक्रेट चैलेंज स्क्रीन पर खुलेगा।</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🎡 स्पिन करें (Spin The Wheel)", type="primary", use_container_width=True, key="btn_spin_wheel"):
            chosen = random.choice(available_tasks)
            cursor.execute("""
                INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (ACTIVE_USER, today_str, chosen[0], chosen[1], chosen[2]))
            conn.commit()
            st.rerun()

    else:
        c_id, t_text, r_type, r_val, is_done = today_challenge

        if is_done == 1:
            st.success("🎉 **बधाई! आपने आज का वेल्थ चैलेंज पूरा कर लिया है!**")
            st.markdown(f"""
            <div class="task-card" style="border-color: #22c55e;">
                <h4 style="color: #22c55e; margin:0;">✅ मिशन पूर्ण (Completed)</h4>
                <p style="color: #f1f5f9; font-size: 1.1rem; margin: 8px 0;">{t_text}</p>
                <small style="color: #94a3b8;">नया चैलेंज कल सुबह 6:00 बजे अनलॉक होगा।</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            reward_label = f"₹{r_val:.0f} डिजिटल गोल्ड" if r_type == "GOLD" else f"+{r_val:.0f} लीडरबोर्ड XP"
            st.markdown(f"""
            <div class="task-card">
                <span style="background: #3b0764; border: 1px solid #a855f7; padding: 4px 12px; border-radius: 12px; font-weight: bold; color: #d8b4fe;">
                    🎁 इनाम: {reward_label}
                </span>
                <h3 style="color: #ffffff; margin-top: 14px; margin-bottom: 8px;">आज का वित्तीय मिशन:</h3>
                <p style="color: #cbd5e1; font-size: 1.15rem; line-height: 1.6;">{t_text}</p>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            if st.button("🏆 मैंने यह चैलेंज पूरा कर लिया (Claim Reward)", type="primary", use_container_width=True, key="btn_claim_task"):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE id = ?", (c_id,))
                
                # अगर इनाम गोल्ड था, तो एसेट्स टेबल में जोड़ दो
                if r_type == "GOLD":
                    g_bought = r_val / 7650.0
                    cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                                   (ACTIVE_USER, today_str, "Gold (24K Challenge Reward)", g_bought, r_val, "Daily Spin Reward"))
                
                conn.commit()
                st.balloons()
                st.success(f"शानदार इच्छाशक्ति! {reward_label} आपके खाते में जुड़ गया!")
                st.rerun()

# ----------------- TAB: WEALTH SQUAD -----------------
with tab_squad:
    st.subheader("👥 5 दोस्तों का सीक्रेट वेल्थ स्क्वाड")
    cursor.execute("""
        SELECT s.squad_id, s.squad_name, s.squad_code, s.monthly_target 
        FROM wealth_squads s
        INNER JOIN squad_members m ON s.squad_code = m.squad_code
        WHERE m.user_phone = ?
    """, (ACTIVE_USER,))
    user_squad = cursor.fetchone()

    if not user_squad:
        st.info("💡 नया स्क्वाड बनाएँ या दोस्त के 4-अंकों के कोड से जुड़ें:")
        col_sq1, col_sq2 = st.columns(2)
        with col_sq1:
            with st.form("create_squad_form", clear_on_submit=True):
                st.write("#### 🛡️ नया स्क्वाड बनाएँ")
                sq_name = st.text_input("स्क्वाड का नाम:")
                sq_code = st.text_input("4-अंकों का कोड रखें:", max_chars=4)
                if st.form_submit_button("ग्रुप बनाएँ 🚀") and sq_name and len(sq_code) == 4:
                    try:
                        cursor.execute("INSERT INTO wealth_squads (squad_name, squad_code, creator_phone, monthly_target) VALUES (?, ?, ?, 25000.0)",
                                       (sq_name, sq_code, ACTIVE_USER))
                        cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)",
                                       (sq_code, ACTIVE_USER, str(date.today())))
                        conn.commit()
                        st.rerun()
                    except Exception:
                        st.error("यह कोड पहले से उपयोग में है!")
        with col_sq2:
            with st.form("join_squad_form", clear_on_submit=True):
                st.write("#### 🤝 स्क्वाड जॉइन करें")
                j_code = st.text_input("दोस्त का 4-अंकों का कोड:")
                if st.form_submit_button("जॉइन करें ⚡") and len(j_code) == 4:
                    cursor.execute("SELECT squad_name FROM wealth_squads WHERE squad_code = ?", (j_code,))
                    if cursor.fetchone():
                        cursor.execute("INSERT OR IGNORE INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)",
                                       (j_code, ACTIVE_USER, str(date.today())))
                        conn.commit()
                        st.rerun()
                    else:
                        st.error("गलत कोड!")
    else:
        s_id, s_name, s_code, s_target = user_squad
        st.success(f"🛡️ वर्तमान स्क्वाड: **{s_name}** | इनवाइट कोड: `{s_code}`")
        if st.button("🚪 ग्रुप छोड़ें"):
            cursor.execute("DELETE FROM squad_members WHERE squad_code = ? AND user_phone = ?", (s_code, ACTIVE_USER))
            conn.commit()
            st.rerun()

# ----------------- TAB: ALL-INDIA LEADERBOARD -----------------
with tab_lead:
    st.subheader("🏆 ऑल-इंडिया वेल्थ अनुशासन लीडरबोर्ड")
    all_users = pd.read_sql_query("SELECT phone FROM users", conn)["phone"].tolist()
    leaderboard_data = []

    for u in all_users:
        u_inc = pd.read_sql_query("SELECT entry_date, daily_amount FROM income_history WHERE user_phone = ?", conn, params=(u,))
        u_exp = pd.read_sql_query("SELECT amount FROM expense_history WHERE user_phone = ?", conn, params=(u,))
        tot_inc = u_inc["daily_amount"].sum() if not u_inc.empty else 0.0
        tot_exp = u_exp["amount"].sum() if not u_exp.empty else 0.0

        u_dates = sorted(u_inc["entry_date"].unique().tolist(), reverse=True) if not u_inc.empty else []
        u_streak = 0
        chk = date.today()
        if str(chk) not in u_dates: chk = date.today() - timedelta(days=1)
        while str(chk) in u_dates:
            u_streak += 1
            chk = chk - timedelta(days=1)

        # चैलेंज पूरे करने पर बोनस XP
        cursor.execute("SELECT COUNT(*) FROM daily_challenges WHERE user_phone = ? AND is_completed = 1", (u,))
        completed_tasks_count = cursor.fetchone()[0]

        sav_rate = ((tot_inc - tot_exp) / tot_inc * 100) if tot_inc > 0 else 0.0
        discipline_score = int(u_streak * 50 + sav_rate + (completed_tasks_count * 100))

        leaderboard_data.append({
            "phone": u,
            "masked_phone": f"{u[:5]}*****",
            "streak": u_streak,
            "score": discipline_score
        })

    lead_df = pd.DataFrame(leaderboard_data).sort_values(by="score", ascending=False).reset_index(drop=True)

    for rank, row in lead_df.iterrows():
        r_num = rank + 1
        badge = "👑 रैंक 1" if r_num == 1 else ("🥈 रैंक 2" if r_num == 2 else ("🥉 रैंक 3" if r_num == 3 else f"रैंक {r_num}"))
        me = " (आप ⭐)" if row["phone"] == ACTIVE_USER else ""
        st.markdown(f"""
        <div style="background:#161a23; border:1px solid #334155; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between;">
            <div><b style="color:#e5a93c;">{badge}</b><br><span>{row['masked_phone']}{me}</span></div>
            <div style="text-align:right;"><b style="color:#f59e0b;">🔥 {row['streak']} दिन</b><br><small style="color:#94a3b8;">{row['score']} XP</small></div>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB: REELS FEED -----------------
with tab_reels:
    reels_list = pd.read_sql_query("SELECT id, user_phone, post_date, hook_title, gyan_content, video_filename, likes_count FROM reels_feed ORDER BY id DESC", conn)
    if not reels_list.empty:
        idx = st.session_state["current_reel_index"] % len(reels_list)
        current_reel = reels_list.iloc[idx]
        st.markdown(f"### {current_reel['hook_title']}")
        st.write(current_reel['gyan_content'])
        if st.button("⬇️ अगली रील", key="next_r_btn"):
            st.session_state["current_reel_index"] = (idx + 1) % len(reels_list)
            st.rerun()

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
