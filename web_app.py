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

# --- Online Ludo Game Tables ---
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
if "active_ludo_room" not in st.session_state:
    st.session_state["active_ludo_room"] = None

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

bg_color = "#0a0c10"
text_color = "#ffffff"
accent = "#f59e0b"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    label, p, h1, h2, h3, span, div {{ color: {text_color} !important; }}
    .ludo-board {{
        background: linear-gradient(135deg, #131722 0%, #080a0f 100%);
        border: 2px solid #eab308;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(234, 179, 8, 0.2);
    }}
    .player-card {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 12px;
        margin-top: 8px;
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000

st.title("👑 100 Crore Wealth Hub")
st.caption(f"यूज़र: **{ACTIVE_USER[:5]}***** | ऑनलाइन मल्टीप्लेयर लूडो, स्क्वाड व 100 Cr मिशन")

# Tabs (नया लूडो गेम टैब सबसे पहले जोड़ा गया)
tab_ludo, tab_spin, tab_squad, tab_lead, tab_reels, tab_dash, tab_tracker = st.tabs([
    "🎲 ऑनलाइन लूडो (Game)",
    "🎯 डेली वेल्थ स्पिन",
    "👥 वेल्थ स्क्वाड",
    "🏆 एलीट लीडरबोर्ड", 
    "📱 वेल्थ रील्स (Feed)", 
    "📊 मुख्य डैशबोर्ड",
    "💵 कमाई व लेजर"
])

# ----------------- TAB: ONLINE MULTIPLAYER LUDO -----------------
with tab_ludo:
    st.subheader("🎲 100 करोड़ ऑनलाइन लूडो एरीना")
    st.caption("दोस्तों के साथ ग्रुप बनाकर खेलें या ऑनलाइन रूम कोड से मुकाबला करें:")

    # रूम चेक
    cursor.execute("""
        SELECT r.room_code, r.room_name, r.status, r.current_turn, r.last_dice, r.winner
        FROM ludo_rooms r
        INNER JOIN ludo_players p ON r.room_code = p.room_code
        WHERE p.user_phone = ? AND r.status != 'FINISHED'
    """, (ACTIVE_USER,))
    joined_room = cursor.fetchone()

    if not joined_room:
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.markdown("#### 🛡️ नया लूडो रूम बनाएँ")
            with st.form("create_ludo_form", clear_on_submit=True):
                r_name = st.text_input("मैच का नाम:", placeholder="उदा. चैंपियंस बैटल")
                r_code = st.text_input("4-अंकों का रूम कोड रखें:", max_chars=4, placeholder="उदा. 4455")
                submit_create = st.form_submit_button("रूम बनाएँ 🎲", type="primary")

                if submit_create:
                    if not r_name or len(r_code) != 4:
                        st.error("कृपया नाम और 4-अंकों का कोड डालें!")
                    else:
                        try:
                            cursor.execute("""
                                INSERT INTO ludo_rooms (room_code, room_name, host_phone, status, current_turn)
                                VALUES (?, ?, ?, 'WAITING', ?)
                            """, (r_code, r_name, ACTIVE_USER, ACTIVE_USER))
                            cursor.execute("""
                                INSERT INTO ludo_players (room_code, user_phone, color, token_pos, joined_at)
                                VALUES (?, ?, '🔴 लाल (Red)', 0, ?)
                            """, (r_code, ACTIVE_USER, str(date.today())))
                            conn.commit()
                            st.balloons()
                            st.success(f"रूम '{r_name}' बन गया!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("यह कोड पहले से उपयोग में है, दूसरा कोड चुनें!")

        with col_l2:
            st.markdown("#### 🤝 दोस्त का रूम जॉइन करें")
            with st.form("join_ludo_form", clear_on_submit=True):
                join_c = st.text_input("4-अंकों का रूम कोड डालें:", max_chars=4)
                submit_join = st.form_submit_button("मैच जॉइन करें ⚡")

                if submit_join:
                    cursor.execute("SELECT room_code, room_name FROM ludo_rooms WHERE room_code = ? AND status != 'FINISHED'", (join_c,))
                    r_found = cursor.fetchone()
                    if r_found:
                        cursor.execute("SELECT COUNT(*) FROM ludo_players WHERE room_code = ?", (join_c,))
                        p_count = cursor.fetchone()[0]
                        colors = ['🔴 लाल', '🟢 हरा', '🟡 पीला', '🔵 नीला']
                        chosen_color = colors[p_count % 4]
                        try:
                            cursor.execute("""
                                INSERT INTO ludo_players (room_code, user_phone, color, token_pos, joined_at)
                                VALUES (?, ?, ?, 0, ?)
                            """, (join_c, ACTIVE_USER, chosen_color, str(date.today())))
                            conn.commit()
                            st.success(f"आप '{r_found[1]}' रूम में जुड़ गए!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.warning("आप पहले से इस मैच में हैं!")
                    else:
                        st.error("यह रूम कोड सक्रिय नहीं है!")

    else:
        r_code, r_name, r_status, r_turn, r_dice, r_winner = joined_room

        # सभी खिलाड़ी
        players_df = pd.read_sql_query("""
            SELECT user_phone, color, token_pos FROM ludo_players WHERE room_code = ? ORDER BY id ASC
        """, conn, params=(r_code,))

        st.markdown(f"""
        <div class="ludo-board">
            <h2 style="color: #eab308; margin-bottom: 4px;">🎲 {r_name} (रूम: {r_code})</h2>
            <p style="color: #cbd5e1; margin-bottom: 8px;">लक्ष्य: 50 कदम पूरा करके 100 करोड़ होम पहुँचना!</p>
            <div style="font-size: 2.2rem; font-weight: bold; color: #ffffff; margin: 12px 0;">
                डाइस: 🎲 {r_dice if r_dice > 0 else '-'}
            </div>
            <p style="color: #38bdf8; font-weight: bold;">वर्तमान बारी: @{r_turn[:5]}*****</p>
        </div>
        """, unsafe_allow_html=True)

        # गेम कंट्रोल्स
        col_gc1, col_gc2 = st.columns(2)
        with col_gc1:
            is_my_turn = (r_turn == ACTIVE_USER)
            if is_my_turn:
                if st.button("🎲 डाइस रोल करें (Roll Dice)", type="primary", use_container_width=True):
                    dice_val = random.randint(1, 6)
                    # खिलाड़ी की स्थिति अपडेट करना
                    cursor.execute("SELECT token_pos FROM ludo_players WHERE room_code = ? AND user_phone = ?", (r_code, ACTIVE_USER))
                    current_pos = cursor.fetchone()[0]
                    new_pos = current_pos + dice_val

                    # क्या कोई जीता? (50 पर होम)
                    if new_pos >= 50:
                        new_pos = 50
                        cursor.execute("UPDATE ludo_rooms SET status = 'FINISHED', winner = ?, last_dice = ? WHERE room_code = ?",
                                       (ACTIVE_USER, dice_val, r_code))
                        # विनर को गोल्ड बोनस
                        cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                                       (ACTIVE_USER, str(date.today()), "Gold (Ludo Winner Reward)", 0.005, 38.0, f"Won Ludo Match #{r_code}"))
                    else:
                        # अगली बारी दूसरे खिलाड़ी को
                        player_list = players_df['user_phone'].tolist()
                        cur_idx = player_list.index(ACTIVE_USER)
                        next_turn = player_list[(cur_idx + 1) % len(player_list)]
                        cursor.execute("UPDATE ludo_rooms SET current_turn = ?, last_dice = ? WHERE room_code = ?",
                                       (next_turn, dice_val, r_code))

                    cursor.execute("UPDATE ludo_players SET token_pos = ? WHERE room_code = ? AND user_phone = ?",
                                   (new_pos, r_code, ACTIVE_USER))
                    conn.commit()
                    st.rerun()
            else:
                st.info("⏳ दूसरे खिलाड़ी की बारी की प्रतीक्षा करें...")
                if st.button("🔄 बोर्ड रीफ़्रेश करें", use_container_width=True):
                    st.rerun()

        with col_gc2:
            if st.button("🚪 मैच छोड़ें (Leave Match)", use_container_width=True):
                cursor.execute("DELETE FROM ludo_players WHERE room_code = ? AND user_phone = ?", (r_code, ACTIVE_USER))
                conn.commit()
                st.rerun()

        # लाइव ट्रैक प्रोग्रेस
        st.write("---")
        st.markdown("### 🏆 खिलाड़ियों की लाइव स्थिति (Race to 100 Cr):")
        for _, p_row in players_df.iterrows():
            pos = p_row['token_pos']
            pct = min(pos / 50.0, 1.0)
            me_tag = " (आप ⭐)" if p_row['user_phone'] == ACTIVE_USER else ""
            st.write(f"**{p_row['color']}** • `@{p_row['user_phone'][:5]}*****`{me_tag} — **{pos} / 50 कदम**")
            st.progress(pct)

        if r_winner:
            st.balloons()
            st.success(f"👑 **विजेता घोषित:** @{r_winner[:5]}***** ने मैच जीत लिया और ₹38 का डिजिटल गोल्ड जैकपॉट हासिल किया!")

# ----------------- TAB: DAILY WEALTH SPIN -----------------
with tab_spin:
    st.subheader("🎯 डेली वेल्थ रूले व सीक्रेट चैलेंज")
    today_str = str(date.today())
    cursor.execute("SELECT id, task_text, reward_type, reward_val, is_completed FROM daily_challenges WHERE user_phone = ? AND challenge_date = ?", (ACTIVE_USER, today_str))
    today_challenge = cursor.fetchone()

    available_tasks = [
        ("☕ ज़ीरो-वेस्ट चाय/नाश्ता मिशन: आज बाहर कोई फ़ालतू ख़र्च नहीं करना!", "GOLD", 20.0),
        ("📚 60 मिनट डीप वर्क: आज 1 घंटा बिना सोशल मीडिया के काम करें!", "XP", 150.0),
        ("🪙 चिल्लर बचत: आज अपने वॉलेट से ₹30 बचाकर सीधे डिजिटल गोल्ड में लॉक करें!", "GOLD", 30.0)
    ]

    if not today_challenge:
        if st.button("🎡 आज का चैलेंज स्पिन करें", type="primary", use_container_width=True):
            chosen = random.choice(available_tasks)
            cursor.execute("""
                INSERT INTO daily_challenges (user_phone, challenge_date, task_text, reward_type, reward_val, is_completed)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (ACTIVE_USER, today_str, chosen[0], chosen[1], chosen[2]))
            conn.commit()
            st.rerun()
    else:
        c_id, t_text, r_type, r_val, is_done = today_challenge
        if is_done:
            st.success("✅ आज का चैलेंज पूरा हो चुका है!")
        else:
            st.info(f"📌 **आज का मिशन:** {t_text}")
            if st.button("🏆 चैलेंज पूरा किया (Claim)", type="primary"):
                cursor.execute("UPDATE daily_challenges SET is_completed = 1 WHERE id = ?", (c_id,))
                conn.commit()
                st.balloons()
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
        with st.form("create_sq_form"):
            s_n = st.text_input("स्क्वाड का नाम:")
            s_c = st.text_input("4-अंकों का कोड:", max_chars=4)
            if st.form_submit_button("ग्रुप बनाएँ 🚀") and s_n and len(s_c) == 4:
                try:
                    cursor.execute("INSERT INTO wealth_squads (squad_name, squad_code, creator_phone) VALUES (?, ?, ?)", (s_n, s_c, ACTIVE_USER))
                    cursor.execute("INSERT INTO squad_members (squad_code, user_phone, joined_date) VALUES (?, ?, ?)", (s_c, ACTIVE_USER, str(date.today())))
                    conn.commit()
                    st.rerun()
                except Exception:
                    st.error("यह कोड पहले से उपयोग में है!")
    else:
        st.success(f"🛡️ वर्तमान स्क्वाड: **{user_squad[1]}** | इनवाइट कोड: `{user_squad[2]}`")

# ----------------- TAB: LEADERBOARD -----------------
with tab_lead:
    st.subheader("🏆 ऑल-इंडिया वेल्थ अनुशासन लीडरबोर्ड")
    lead_rows = pd.read_sql_query("SELECT phone FROM users LIMIT 10", conn)
    for idx, r in lead_rows.iterrows():
        me = " (आप ⭐)" if r['phone'] == ACTIVE_USER else ""
        st.write(f"**रैंक {idx+1}** • `@{r['phone'][:5]}*****`{me} — **🔥 10 दिन स्ट्रीक**")

# ----------------- TAB: REELS FEED -----------------
with tab_reels:
    reels_list = pd.read_sql_query("SELECT hook_title, gyan_content FROM reels_feed ORDER BY id DESC LIMIT 5", conn)
    if not reels_list.empty:
        for _, r in reels_list.iterrows():
            st.markdown(f"### {r['hook_title']}")
            st.write(r['gyan_content'])
            st.write("---")

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
