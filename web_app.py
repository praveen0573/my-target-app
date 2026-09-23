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

# Squad Groups Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS wealth_squads (
        squad_id INTEGER PRIMARY KEY AUTOINCREMENT,
        squad_name TEXT,
        squad_code TEXT UNIQUE,
        creator_phone TEXT,
        monthly_target REAL DEFAULT 25000.0
    )
""")

# Squad Members Table
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
    .squad-card {{
        background: linear-gradient(135deg, #182234 0%, #0e1626 100%);
        border: 2px solid #38bdf8;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }}
    .member-row {{
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px 15px;
        margin-top: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000

st.title("👑 100 Crore Wealth Hub")
st.caption(f"यूज़र: **{ACTIVE_USER[:5]}***** | वेल्थ स्क्वाड व 100 Cr मिशन")

# Tabs
tab_squad, tab_lead, tab_reels, tab_dash, tab_tracker = st.tabs([
    "👥 वेल्थ स्क्वाड",
    "🏆 एलीट लीडरबोर्ड", 
    "📱 वेल्थ रील्स (Feed)", 
    "📊 मुख्य डैशबोर्ड",
    "💵 कमाई व लेजर"
])

# ----------------- TAB: WEALTH SQUAD (5 DOSTON KA GROUP) -----------------
with tab_squad:
    st.subheader("👥 5 दोस्तों का सीक्रेट वेल्थ स्क्वाड")
    st.caption("अकेले बचत करना मुश्किल है, लेकिन जब दोस्त साथ हों तो 100 करोड़ का सफ़र आसान हो जाता है!")

    # यूज़र किस ग्रुप में है?
    cursor.execute("""
        SELECT s.squad_id, s.squad_name, s.squad_code, s.monthly_target 
        FROM wealth_squads s
        INNER JOIN squad_members m ON s.squad_code = m.squad_code
        WHERE m.user_phone = ?
    """, (ACTIVE_USER,))
    user_squad = cursor.fetchone()

    if not user_squad:
        st.info("💡 आप अभी किसी वेल्थ स्क्वाड में शामिल नहीं हैं। नया स्क्वाड बनाएँ या दोस्तों के स्क्वाड कोड से जुड़ें:")
        col_sq1, col_sq2 = st.columns(2)
        with col_sq1:
            with st.form("create_squad_form", clear_on_submit=True):
                st.write("#### 🛡️ नया स्क्वाड बनाएँ")
                sq_name = st.text_input("स्क्वाड का नाम:", placeholder="उदा. रॉयल टाइटन्स")
                sq_code = st.text_input("4-अंकों का गुप्त कोड रखें:", max_chars=4, placeholder="उदा. 7788")
                sq_target = st.number_input("ग्रुप का मासिक बचत लक्ष्य (₹):", min_value=5000.0, value=25000.0, step=5000.0)
                submit_create = st.form_submit_button("ग्रुप बनाएँ 🚀", type="primary")

                if submit_create:
                    if not sq_name or len(sq_code) != 4:
                        st.error("कृपया सही नाम और 4-अंकों का कोड डालें!")
                    else:
                        try:
                            cursor.execute("INSERT INTO wealth_squads (squad_name, squad_code, creator_phone, monthly_target) VALUES (?, ?, ?, ?)",
                                           (sq_name, sq_code, ACTIVE_USER, sq_target))
                            cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)",
                                           (sq_code, ACTIVE_USER, str(date.today())))
                            conn.commit()
                            st.balloons()
                            st.success(f"बधाई! '{sq_name}' स्क्वाड बन गया!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("यह कोड पहले से किसी ग्रुप का है, कृपया दूसरा कोड चुनें!")

        with col_sq2:
            with st.form("join_squad_form", clear_on_submit=True):
                st.write("#### 🤝 दोस्त के स्क्वाड में जुड़ें")
                j_code = st.text_input("दोस्त का 4-अंकों का कोड डालें:", max_chars=4)
                submit_join = st.form_submit_button("स्क्वाड जॉइन करें ⚡")

                if submit_join:
                    cursor.execute("SELECT squad_name FROM wealth_squads WHERE squad_code = ?", (j_code,))
                    sq_found = cursor.fetchone()
                    if sq_found:
                        try:
                            cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)",
                                           (j_code, ACTIVE_USER, str(date.today())))
                            conn.commit()
                            st.success(f"आप '{sq_found[0]}' स्क्वाड में शामिल हो गए!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.warning("आप पहले से इस ग्रुप में हैं!")
                    else:
                        st.error("गलत कोड! ऐसा कोई स्क्वाड नहीं मिला।")

    else:
        s_id, s_name, s_code, s_target = user_squad

        # ग्रुप मेंबर्स और उनके इस महीने के आंकड़े
        current_m_prefix = str(date.today())[:7]
        members = pd.read_sql_query("SELECT user_phone FROM squad_members WHERE squad_code = ?", conn, params=(s_code,))["user_phone"].tolist()

        squad_total_saved = 0.0
        member_stats = []

        for m_phone in members:
            m_inc = pd.read_sql_query("SELECT daily_amount, entry_date FROM income_history WHERE user_phone = ? AND entry_date LIKE ?", conn, params=(m_phone, f"{current_m_prefix}%"))
            m_exp = pd.read_sql_query("SELECT amount FROM expense_history WHERE user_phone = ? AND entry_date LIKE ?", conn, params=(m_phone, f"{current_m_prefix}%"))
            
            tot_i = m_inc["daily_amount"].sum() if not m_inc.empty else 0.0
            tot_e = m_exp["amount"].sum() if not m_exp.empty else 0.0
            net_s = max(tot_i - tot_e, 0.0)
            squad_total_saved += net_s

            # आखिरी एंट्री तारीख
            last_entry = m_inc["entry_date"].max() if not m_inc.empty else "कोई एंट्री नहीं"
            is_active = (last_entry == str(date.today()))

            member_stats.append({
                "phone": m_phone,
                "saved": net_s,
                "is_active": is_active,
                "last_entry": last_entry
            })

        member_stats = sorted(member_stats, key=lambda x: x["saved"], reverse=True)

        # स्क्वाड कार्ड
        st.markdown(f"""
        <div class="squad-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="color: #38bdf8; margin:0;">🛡️ {s_name}</h2>
                <span style="background:#0f172a; border:1px solid #38bdf8; padding:4px 12px; border-radius:12px; font-weight:bold; color:#e5a93c;">
                    कोड: {s_code}
                </span>
            </div>
            <p style="color:#94a3b8; margin: 6px 0 16px 0;">इस कोड को दोस्तों को भेजें ताकि वे सीधे आपके ग्रुप में जुड़ सकें।</p>
            <div style="margin-top:10px;">
                <b style="color:#ffffff;">स्क्वाड मिशन: ₹{squad_total_saved:,.0f} / ₹{s_target:,.0f} पूरा</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        prog_squad = min(squad_total_saved / s_target, 1.0) if s_target > 0 else 0.0
        st.progress(prog_squad)

        st.write("---")
        st.markdown("### 🏆 स्क्वाड मेंबर्स का योगदान (Leaderboard):")

        for idx, m in enumerate(member_stats):
            m_tag = "👑 स्क्वाड कैप्टन" if idx == 0 else f"मेंबर {idx + 1}"
            status_text = "🔥 आज एक्टिव" if m["is_active"] else "😴 कल से सुस्त"
            status_color = "#22c55e" if m["is_active"] else "#ef4444"
            masked = f"{m['phone'][:5]}*****"
            me_highlight = " (आप ⭐)" if m["phone"] == ACTIVE_USER else ""

            st.markdown(f"""
            <div class="member-row">
                <div>
                    <span style="color:#e5a93c; font-weight:bold;">{m_tag}</span><br>
                    <b style="color:#ffffff; font-size:1.05rem;">{masked}{me_highlight}</b>
                </div>
                <div style="text-align:right;">
                    <b style="color:#38bdf8; font-size:1.1rem;">₹{m['saved']:,.0f} बचाया</b><br>
                    <small style="color:{status_color}; font-weight:bold;">{status_text}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        if st.button("🚪 स्क्वाड से बाहर निकलें (Leave Group)"):
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
        if str(chk) not in u_dates:
            chk = date.today() - timedelta(days=1)
        while str(chk) in u_dates:
            u_streak += 1
            chk = chk - timedelta(days=1)

        sav_rate = ((tot_inc - tot_exp) / tot_inc * 100) if tot_inc > 0 else 0.0
        discipline_score = int(u_streak * 50 + sav_rate)

        leaderboard_data.append({
            "phone": u,
            "masked_phone": f"{u[:5]}*****",
            "streak": u_streak,
            "score": discipline_score
        })

    lead_df = pd.DataFrame(leaderboard_data).sort_values(by="score", ascending=False).reset_index(drop=True)

    for rank, row in lead_df.iterrows():
        r_num = rank + 1
        badge = f"रैंक {r_num}"
        if r_num == 1: badge = "👑 रैंक 1 (Grand Titan)"
        elif r_num == 2: badge = "🥈 रैंक 2 (Master)"
        elif r_num == 3: badge = "🥉 रैंक 3 (Hustler)"

        st.markdown(f"""
        <div style="background:#161a23; border:1px solid #334155; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between;">
            <div>
                <b style="color:#e5a93c;">{badge}</b><br>
                <span>{row['masked_phone']}</span>
            </div>
            <div style="text-align:right;">
                <b style="color:#f59e0b;">🔥 {row['streak']} दिन</b><br>
                <small style="color:#94a3b8;">{row['score']} XP</small>
            </div>
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
