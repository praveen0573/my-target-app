import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import io
import requests
import math
import os
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Page Config ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- Video Storage Folder ---
UPLOADS_DIR = "uploaded_videos"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Database Setup & Auto-Migration ---
DB_PATH = "wealth_data.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        phone TEXT PRIMARY KEY,
        pin TEXT,
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

# Community Reels Table
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

# Reels Comments Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS reels_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reel_id INTEGER,
        user_phone TEXT,
        comment_text TEXT,
        created_date TEXT
    )
""")

# Saved Reels
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_saved_reels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        reel_id INTEGER,
        saved_date TEXT,
        UNIQUE(user_phone, reel_id)
    )
""")

# इनिशियल ज्ञान रील्स अगर टेबल खाली हो
cursor.execute("SELECT COUNT(*) FROM reels_feed")
if cursor.fetchone()[0] == 0:
    starter_reels = [
        ("👑 100 करोड़ का पहला नियम", "गरीब लोग समय बेचकर पैसे कमाते हैं। अमीर लोग संपत्ति (Assets) बनाकर सोते हुए कमाते हैं। आज ही कोई ऐसा एसेट या स्किल शुरू करो जो तुम्हारे बिना भी चले!", ""),
        ("⚡ चार्ली मुंगेर का ₹10 लाख सीक्रेट", "पहला ₹10 लाख बचाना सबसे मुश्किल काम है। चाहे बस से चलना पड़े या बाहर का खाना बंद करना पड़े, इसे पूरा करो। 10 लाख के बाद कम्पाउंडिंग जादू की तरह काम करती है!", ""),
        ("🛡️ वारेन बफ़ेट का 50% रूल", "अगर तुम ऐसी चीज़ें खरीदते हो जिनकी तुम्हें ज़रूरत नहीं है, तो जल्द ही तुम्हें वो चीज़ें बेचनी पड़ेंगी जिनकी तुम्हें सख्त ज़रूरत है। हर ख़र्च पर 24 घंटे सोचो!", ""),
        ("🔥 नेवल रविकांत: कोड और मीडिया", "अगर आपके पास पूँजी नहीं है, तो कोड लिखो या हाई-वैल्यू वीडियो बनाओ। इंटरनेट पर बनाया गया कंटेंट बिना सोए 24 घंटे दुनिया भर में आपके लिए काम करता है!", ""),
        ("🪙 स्पेयर-चेंज का गणित", "रोज़ ₹50 का सोना खरीदना मज़ाक लगता है। लेकिन 15% सालाना रिटर्न के साथ 20 साल में यह छोटी चिल्लर ₹75 लाख+ की दौलत बन जाती है!", "")
    ]
    for r_title, r_gyan, r_vid in starter_reels:
        cursor.execute("INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename, likes_count) VALUES (?, ?, ?, ?, ?, ?)",
                       ("OFFICIAL", str(date.today()), r_title, r_gyan, r_vid, random.randint(15, 60)))
    conn.commit()

# --- Session State ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None
if "current_reel_index" not in st.session_state:
    st.session_state["current_reel_index"] = 0

# --- Login Screen ---
if not st.session_state["logged_user"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("हर व्यक्ति का अपना सुरक्षित, व्यक्तिगत वित्तीय खाता।")

    auth_tab1, auth_tab2 = st.tabs(["🔑 लॉगिन", "📝 नया खाता बनाएँ"])

    with auth_tab1:
        st.subheader("अपने नंबर से लॉगिन करें")
        with st.form("login_form"):
            l_phone = st.text_input("मोबाइल नंबर (10 अंक):", max_chars=10, value="9983204295")
            l_pin = st.text_input("4-अंकों का गुप्त पिन:", type="password", max_chars=4)
            submit_login = st.form_submit_button("लॉगिन करें 🔓", type="primary")

            if submit_login:
                if len(l_phone) != 10 or not l_phone.isdigit():
                    st.error("कृपया 10 अंकों का सही मोबाइल नंबर डालें!")
                else:
                    cursor.execute("SELECT pin FROM users WHERE phone = ?", (l_phone,))
                    user_data = cursor.fetchone()
                    if user_data:
                        if user_data[0] == l_pin:
                            st.session_state["logged_user"] = l_phone
                            st.success("सफलतापूर्वक लॉगिन हो गया!")
                            st.rerun()
                        else:
                            st.error("गलत पिन! सही पिन डालें।")
                    else:
                        st.error("यह नंबर पंजीकृत नहीं है! पहले 'नया खाता बनाएँ' से पिन सेट करें।")

    with auth_tab2:
        st.subheader("नया 100 Cr खाता बनाएँ")
        with st.form("signup_form"):
            s_phone = st.text_input("अपना 10-अंकों का मोबाइल नंबर:", max_chars=10, value="9983204295")
            s_pin = st.text_input("नया 4-अंकों का पिन चुनें:", type="password", max_chars=4)
            s_pin_confirm = st.text_input("पिन दोबारा डालें:", type="password", max_chars=4)
            submit_signup = st.form_submit_button("खाता बनाएँ और लॉगिन करें 🚀")

            if submit_signup:
                if len(s_phone) != 10 or not s_phone.isdigit():
                    st.error("कृपया 10 अंकों का मान्य नंबर डालें!")
                elif len(s_pin) != 4 or not s_pin.isdigit():
                    st.error("पिन 4 अंकों का होना चाहिए!")
                elif s_pin != s_pin_confirm:
                    st.error("दोनों पिन मेल नहीं खा रहे हैं!")
                else:
                    cursor.execute("SELECT phone FROM users WHERE phone = ?", (s_phone,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE users SET pin = ? WHERE phone = ?", (s_pin, s_phone))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("पिन अपडेट हुआ और लॉगिन हो गया!")
                        st.rerun()
                    else:
                        cursor.execute("INSERT INTO users (phone, pin, created_at) VALUES (?, ?, ?)",
                                       (s_phone, s_pin, str(date.today())))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("बधाई हो! आपका नया खाता तैयार हो गया है।")
                        st.rerun()
    st.stop()

# ==================== Logged In User Interface ====================
ACTIVE_USER = st.session_state["logged_user"]

# Theme Styling
bg_color = "#0a0c10"
text_color = "#ffffff"
accent = "#f59e0b"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    label, p, h1, h2, h3, span, div {{ color: {text_color} !important; }}
    .reel-container {{
        background: linear-gradient(180deg, #161a23 0%, #0d0f14 100%);
        border: 2px solid #e5a93c;
        border-radius: 20px;
        padding: 24px;
        min-height: 480px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 15px 35px rgba(0,0,0,0.7);
        margin: 10px 0;
    }}
    .reel-hook {{
        color: #e5a93c !important;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .reel-text {{
        color: #f1f5f9 !important;
        font-size: 1.15rem;
        line-height: 1.6;
        font-weight: 500;
        margin: 15px 0;
    }}
    .action-btn-pill {{
        background: #1e2430;
        border: 1px solid #475569;
        border-radius: 25px;
        padding: 8px 16px;
        color: white;
        font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000

# Top Bar
st.title("👑 100 Crore Wealth Reels")
st.caption(f"यूज़र: **{ACTIVE_USER}** | इंस्टाग्राम रील्स छोड़ो, यहाँ 100 करोड़ का ज्ञान लो!")

# Core Tabs
tab_reels, tab_upload_reel, tab_dash, tab_tracker = st.tabs([
    "📱 वेल्थ रील्स (Feed)", 
    "➕ नई रील / ज्ञान पोस्ट करें",
    "📊 मुख्य डैशबोर्ड",
    "💵 कमाई व लेजर"
])

# ----------------- TAB: INSTAGRAM STYLE REELS SCROLLER -----------------
with tab_reels:
    reels_list = pd.read_sql_query("SELECT id, user_phone, post_date, hook_title, gyan_content, video_filename, likes_count FROM reels_feed ORDER BY id DESC", conn)

    if reels_list.empty:
        st.info("अभी कोई रील उपलब्ध नहीं है। पहली रील पोस्ट करें!")
    else:
        total_reels = len(reels_list)
        idx = st.session_state["current_reel_index"] % total_reels
        current_reel = reels_list.iloc[idx]
        reel_id = int(current_reel['id'])

        # Reels Header Controls (Next / Prev)
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

        # Instagram Reel Card
        st.markdown(f"""
        <div class="reel-container">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="color: #e5a93c; font-weight: bold;">👤 @{current_reel['user_phone'][:6]}***</span>
                    <span style="color: #64748b; font-size: 0.85rem;">📅 {current_reel['post_date']}</span>
                </div>
                <div class="reel-hook">{current_reel['hook_title']}</div>
                <div class="reel-text">{current_reel['gyan_content']}</div>
            </div>
            <div style="border-top: 1px solid rgba(229, 169, 60, 0.2); padding-top: 12px; margin-top: 15px;">
                <small style="color: #f59e0b;">💡 100 Crore Mindset Hack • स्वाइप करके सीखते रहें</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Video if attached
        if current_reel['video_filename']:
            v_path = os.path.join(UPLOADS_DIR, current_reel['video_filename'])
            if os.path.exists(v_path):
                st.video(v_path)

        # Bottom Instagram-Style Action Bar
        col_act1, col_act2, col_act3, col_act4 = st.columns([1.2, 1.2, 1.2, 2.4])
        
        # 1. Like
        with col_act1:
            if st.button(f"❤️ {current_reel['likes_count']}", key=f"reel_like_{reel_id}", use_container_width=True):
                cursor.execute("UPDATE reels_feed SET likes_count = likes_count + 1 WHERE id = ?", (reel_id,))
                conn.commit()
                st.rerun()

        # 2. Save
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

        # 3. Share / WhatsApp
        with col_act3:
            share_text = f"100 Crore Gyan Reel: {current_reel['hook_title']}"
            st.button("↗️ शेयर", key=f"share_reel_{reel_id}", use_container_width=True)

        # 4. Instant Action Button (रील से ज्ञान लिया ➔ सोना जोड़ा)
        with col_act4:
            if st.button("🪙 ज्ञान सीखा ➔ ₹10 गोल्ड", key=f"gold_learn_{reel_id}", use_container_width=True):
                g_bought = 10.0 / 7650.0
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                               (ACTIVE_USER, str(date.today()), "Gold (24K Gyan Reward)", g_bought, 10.0, f"Learnt from Reel #{reel_id}"))
                conn.commit()
                st.balloons()
                st.success("शानदार! ज्ञान लेने के साथ ₹10 का 24K सोना भी जुड़ गया!")

        # Comments Section
        with st.expander("💬 इस रील पर विचार व कमेंट्स"):
            comments_df = pd.read_sql_query(
                "SELECT user_phone, comment_text, created_date FROM reels_comments WHERE reel_id = ? ORDER BY id DESC", 
                conn, params=(reel_id,)
            )
            if not comments_df.empty:
                for _, c_row in comments_df.iterrows():
                    st.write(f"**@{c_row['user_phone'][:6]}***: {c_row['comment_text']}")
            else:
                st.caption("अभी कोई कमेंट नहीं है। पहला विचार आप लिखें!")

            with st.form(f"reel_comment_form_{reel_id}", clear_on_submit=True):
                c_text = st.text_input("अपना कमेंट दर्ज करें:")
                if st.form_submit_button("पोस्ट करें 💬") and c_text.strip():
                    cursor.execute("INSERT INTO reels_comments (reel_id, user_phone, comment_text, created_date) VALUES (?, ?, ?, ?)",
                                   (reel_id, ACTIVE_USER, c_text.strip(), str(date.today())))
                    conn.commit()
                    st.rerun()

# ----------------- TAB: UPLOAD NEW REEL -----------------
with tab_upload_reel:
    st.subheader("➕ अपनी 100 Cr ज्ञान रील या वीडियो पोस्ट करें")
    st.caption("जो आपने आज सीखा, अपनी कम्युनिटी के साथ साझा करें:")
    
    with st.form("new_reel_form", clear_on_submit=True):
        r_hook = st.text_input("रील का मुख्य शीर्षक (Hook Title):", placeholder="उदा. 90% लोग यह गलती करते हैं...")
        r_gyan = st.text_area("ज्ञान / सीख (Gyan Text):", placeholder="कम शब्दों में दमदार बात लिखें जो लोगों की आँखें खोल दे...")
        r_video = st.file_uploader("शॉर्ट वीडियो अपलोड करें (वैकल्पिक - MP4):", type=["mp4", "mov"])
        submit_reel = st.form_submit_button("🚀 रील पब्लिश करें", type="primary")

        if submit_reel:
            if not r_hook or not r_gyan:
                st.error("कृपया शीर्षक और ज्ञान विवरण दोनों भरें!")
            else:
                v_filename = ""
                if r_video is not None:
                    v_filename = f"{ACTIVE_USER}_{int(random.random()*100000)}_{r_video.name}"
                    v_path = os.path.join(UPLOADS_DIR, v_filename)
                    with open(v_path, "wb") as f:
                        f.write(r_video.getbuffer())

                cursor.execute("""
                    INSERT INTO reels_feed (user_phone, post_date, hook_title, gyan_content, video_filename)
                    VALUES (?, ?, ?, ?, ?)
                """, (ACTIVE_USER, str(date.today()), r_hook, r_gyan, v_filename))
                conn.commit()
                st.balloons()
                st.success("आपकी रील पब्लिश हो गई और अब फीड में लाइव है!")
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

# ----------------- TAB: TRACKER -----------------
with tab_tracker:
    st.subheader("💵 कमाई व ख़र्च दर्ज करें")
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
