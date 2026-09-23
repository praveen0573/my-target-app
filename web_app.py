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

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_loot_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        loot_date TEXT,
        nugget TEXT
    )
""")

# Community Daily Feed Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS community_feed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        post_date TEXT,
        post_title TEXT,
        routine_text TEXT,
        video_filename TEXT,
        likes_count INTEGER DEFAULT 0
    )
""")

# Comments Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_phone TEXT,
        comment_text TEXT,
        created_date TEXT
    )
""")

# Bookmarks / Saved Posts Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_saved_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        post_id INTEGER,
        saved_date TEXT,
        UNIQUE(user_phone, post_id)
    )
""")
conn.commit()

def add_column_if_missing(table_name, column_name, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

add_column_if_missing("income_history", "user_phone", "TEXT")
add_column_if_missing("expense_history", "user_phone", "TEXT")
add_column_if_missing("assets_history", "user_phone", "TEXT")
add_column_if_missing("debt_history", "user_phone", "TEXT")

cursor.execute("UPDATE income_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE expense_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE assets_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE debt_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
conn.commit()

# --- Session State ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None
if "selected_future_yrs" not in st.session_state:
    st.session_state["selected_future_yrs"] = 5
if "boost_hustle" not in st.session_state:
    st.session_state["boost_hustle"] = False
if "boost_cut" not in st.session_state:
    st.session_state["boost_cut"] = False
if "reverse_horizon_yrs" not in st.session_state:
    st.session_state["reverse_horizon_yrs"] = 15
if "custom_daily_target" not in st.session_state:
    st.session_state["custom_daily_target"] = 2000.0
if "selected_ig_mins" not in st.session_state:
    st.session_state["selected_ig_mins"] = 30
if "feed_view_mode" not in st.session_state:
    st.session_state["feed_view_mode"] = "all"  # 'all' ya 'saved'

# --- Login Screen ---
if not st.session_state["logged_user"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("Har vyakti ka apna surakshit, vyaktigat financial khata.")

    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Naya Khata Banayein"])

    with auth_tab1:
        st.subheader("Apne number se login karein")
        with st.form("login_form"):
            l_phone = st.text_input("Mobile Number (10 digit):", max_chars=10, value="9983204295")
            l_pin = st.text_input("4-digit Secret PIN:", type="password", max_chars=4)
            submit_login = st.form_submit_button("Login Karein 🔓", type="primary")

            if submit_login:
                if len(l_phone) != 10 or not l_phone.isdigit():
                    st.error("Kripya 10 ank ka sahi mobile number dalein!")
                else:
                    cursor.execute("SELECT pin FROM users WHERE phone = ?", (l_phone,))
                    user_data = cursor.fetchone()
                    if user_data:
                        if user_data[0] == l_pin:
                            st.session_state["logged_user"] = l_phone
                            st.success("Safaltapoorvak login ho gaya!")
                            st.rerun()
                        else:
                            st.error("Galat PIN! Sahi PIN dalein.")
                    else:
                        st.error("Yeh number registered nahi hai! Pehle 'Naya Khata Banayein' se PIN set karein.")

    with auth_tab2:
        st.subheader("Naya 100 Cr Khata Banayein")
        with st.form("signup_form"):
            s_phone = st.text_input("Apna 10-digit mobile number:", max_chars=10, value="9983204295")
            s_pin = st.text_input("Naya 4-digit PIN chunein:", type="password", max_chars=4)
            s_pin_confirm = st.text_input("PIN dobara dalein:", type="password", max_chars=4)
            submit_signup = st.form_submit_button("Khata Banayein aur Login Karein 🚀")

            if submit_signup:
                if len(s_phone) != 10 or not s_phone.isdigit():
                    st.error("Kripya 10 ank ka valid number dalein!")
                elif len(s_pin) != 4 or not s_pin.isdigit():
                    st.error("PIN 4 ank ka hona chahiye!")
                elif s_pin != s_pin_confirm:
                    st.error("Dono PIN match nahi kar rahe hain!")
                else:
                    cursor.execute("SELECT phone FROM users WHERE phone = ?", (s_phone,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE users SET pin = ? WHERE phone = ?", (s_pin, s_phone))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("PIN update hua aur login ho gaya!")
                        st.rerun()
                    else:
                        cursor.execute("INSERT INTO users (phone, pin, created_at) VALUES (?, ?, ?)",
                                       (s_phone, s_pin, str(date.today())))
                        conn.commit()
                        st.session_state["logged_user"] = s_phone
                        st.success("Badhai ho! Aapka naya khata tayyar ho gaya.")
                        st.rerun()
    st.stop()

# ==================== Logged In User Interface ====================
ACTIVE_USER = st.session_state["logged_user"]

with st.sidebar:
    st.title("👤 User Profile")
    st.success(f"Khata: **{ACTIVE_USER}**")
    
    theme_choice = st.selectbox(
        "Theme Chunein:",
        ["🌟 Royal Gold Dark", "☀️ Classic Bright Light", "🌌 Deep Navy Blue", "🌿 Luxury Green"]
    )
    
    st.divider()
    st.subheader("🔐 PIN Badlein")
    with st.expander("PIN update karein"):
        with st.form("user_change_pin"):
            u_old = st.text_input("Purana PIN:", type="password", max_chars=4)
            u_new = st.text_input("Naya PIN:", type="password", max_chars=4)
            if st.form_submit_button("💾 Naya PIN Save Karein"):
                cursor.execute("SELECT pin FROM users WHERE phone = ?", (ACTIVE_USER,))
                cur_p = cursor.fetchone()
                if cur_p and u_old != cur_p[0]:
                    st.error("Purana PIN galat hai!")
                elif len(u_new) != 4 or not u_new.isdigit():
                    st.error("Naya PIN 4 ank ka hona chahiye!")
                else:
                    cursor.execute("UPDATE users SET pin = ? WHERE phone = ?", (u_new, ACTIVE_USER))
                    conn.commit()
                    st.success("PIN badal gaya!")

    st.divider()
    st.subheader("💾 Backup Download")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp:
            st.download_button(
                label="📥 Backup Download Karein",
                data=fp,
                file_name=f"wealth_backup_{ACTIVE_USER}_{date.today()}.db",
                mime="application/octet-stream"
            )

    st.divider()
    if st.button("Logout Karein 🔒", type="primary"):
        st.session_state["logged_user"] = None
        st.rerun()

# Theme CSS
if theme_choice == "☀️ Classic Bright Light":
    bg_color = "#ffffff"
    text_color = "#111827"
    accent = "#b45309"
    tab_bg = "#f3f4f6"
    btn_bg = "#1d4ed8"
    btn_text = "#ffffff"
elif theme_choice == "🌌 Deep Navy Blue":
    bg_color = "#0a192f"
    text_color = "#f8fafc"
    accent = "#38bdf8"
    tab_bg = "#1e293b"
    btn_bg = "#38bdf8"
    btn_text = "#0f172a"
elif theme_choice == "🌿 Luxury Green":
    bg_color = "#06231a"
    text_color = "#f0fdf4"
    accent = "#4ade80"
    tab_bg = "#14532d"
    btn_bg = "#4ade80"
    btn_text = "#052e16"
else:
    bg_color = "#111318"
    text_color = "#ffffff"
    accent = "#f59e0b"
    tab_bg = "#1f2430"
    btn_bg = "#f59e0b"
    btn_text = "#111827"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    label, p, h1, h2, h3, span, div {{ color: {text_color} !important; }}
    div[data-testid="stMetricValue"] {{ color: {accent} !important; font-weight: 800 !important; font-size: 1.85rem; }}
    div[data-testid="stMetricLabel"] {{ color: {text_color} !important; font-weight: 600 !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{ background-color: {tab_bg} !important; border-radius: 8px; color: {text_color} !important; padding: 6px 12px; font-size: 0.9rem; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 3px solid {accent} !important; font-weight: 700 !important; }}
    .stDownloadButton button {{ background-color: {btn_bg} !important; color: {btn_text} !important; font-weight: bold !important; border: none !important; padding: 10px 22px !important; border-radius: 8px !important; }}
    .vip-card {{
        background: linear-gradient(135deg, #1e1b18 0%, #0d0c0a 100%);
        border: 2px solid #e5a93c;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(229, 169, 60, 0.2);
    }}
    .post-card {{
        background-color: {tab_bg};
        border-radius: 14px;
        padding: 18px;
        border: 1px solid rgba(229, 169, 60, 0.3);
        margin-bottom: 20px;
    }}
    .comment-bubble {{
        background: rgba(0, 0, 0, 0.25);
        padding: 8px 14px;
        border-radius: 10px;
        margin-top: 6px;
        border-left: 3px solid {accent};
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000  # 100 Crore

st.title("👑 100 Crore Wealth Hub")
st.caption(f"Khata: **{ACTIVE_USER}** | Social Feed, Likes, Comments & Saved Posts")

# Tabs
tab1, tab_feed, tab_detox, tab_audio, tab_reverse, tab_booster, tab_elite, tab_cal, tab_fire, tab_roundup, tab_tax, tab_ai, tab_wishlist, tab_game, tab2, tab_exp, tab_debt, tab_health, tab_analytics, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "🌟 Community Feed",
    "🔥 Reels Detox",
    "🎙️ AI Coach",
    "🎯 Reverse Goal",
    "⚡ Speed Booster",
    "👑 Top 1% Club",
    "📅 Calendar",
    "🌴 Passive Freedom",
    "🪙 UPI Round-up",
    "⚖️ Tax & In-Hand",
    "🧠 AI Mentor",
    "🏎️ Luxury Simulator",
    "🎮 Game Zone",
    "💵 Income", 
    "💸 Expenses",
    "⚖️ Karz / Debt",
    "🩺 Health Score",
    "📈 Savings Rate", 
    "🥇 Gold & Assets", 
    "🚀 100 Cr Roadmap",
    "🔥 Daily Goals"
])

# ----------------- Safe Data Query -----------------
try:
    cash_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', daily_amount as 'Raqam (₹)', note as 'Vivran' FROM income_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    cash_df = pd.DataFrame(columns=["id", "Tariqh", "Raqam (₹)", "Vivran"])

try:
    exp_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', amount as 'Raqam (₹)', category as 'Category', note as 'Vivran' FROM expense_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    exp_df = pd.DataFrame(columns=["id", "Tariqh", "Raqam (₹)", "Category", "Vivran"])

try:
    asset_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', asset_type as 'Type', quantity as 'Qty', current_value as 'Value (₹)', note as 'Vivran' FROM assets_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    asset_df = pd.DataFrame(columns=["id", "Tariqh", "Type", "Qty", "Value (₹)", "Vivran"])

try:
    debt_df = pd.read_sql_query("SELECT id, entry_date as 'Tariqh', debt_type as 'Type', person_name as 'Naam', amount as 'Raqam (₹)', note as 'Vivran' FROM debt_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    debt_df = pd.DataFrame(columns=["id", "Tariqh", "Type", "Naam", "Raqam (₹)", "Vivran"])

total_gross_income = cash_df["Raqam (₹)"].sum() if not cash_df.empty else 0.0
total_expenses = exp_df["Raqam (₹)"].sum() if not exp_df.empty else 0.0
total_net_cash = max(total_gross_income - total_expenses, 0.0)
total_assets = asset_df["Value (₹)"].sum() if not asset_df.empty else 0.0

total_liabilities = 0.0
total_receivables = 0.0
if not debt_df.empty:
    liab_rows = debt_df[debt_df["Type"].str.contains("लायबिलिटी|Liability", case=False, na=False)]
    rec_rows = debt_df[debt_df["Type"].str.contains("एसेट|Asset", case=False, na=False)]
    total_liabilities = liab_rows["Raqam (₹)"].sum()
    total_receivables = rec_rows["Raqam (₹)"].sum()

total_networth = max(total_net_cash + total_assets + total_receivables - total_liabilities, 0.0)
savings_rate = ((total_gross_income - total_expenses) / total_gross_income * 100) if total_gross_income > 0 else 0.0

today_str = str(date.today())
current_month_prefix = today_str[:7]

month_inc = 0.0
month_exp = 0.0
if not cash_df.empty:
    m_inc_rows = cash_df[cash_df["Tariqh"].str.startswith(current_month_prefix)]
    month_inc = m_inc_rows["Raqam (₹)"].sum()

if not exp_df.empty:
    m_exp_rows = exp_df[exp_df["Tariqh"].str.startswith(current_month_prefix)]
    month_exp = m_exp_rows["Raqam (₹)"].sum()

month_net_savings = max(month_inc - month_exp, 0.0)

unique_dates = sorted(cash_df["Tariqh"].unique().tolist(), reverse=True) if not cash_df.empty else []
streak = 0
check_day = date.today()
if today_str not in unique_dates:
    check_day = date.today() - timedelta(days=1)
while str(check_day) in unique_dates:
    streak += 1
    check_day = check_day - timedelta(days=1)

# ----------------- TAB: COMMUNITY FEED (LIKES, COMMENTS & SAVE POSTS) -----------------
with tab_feed:
    st.subheader("🌟 Community Din-charya & Video Feed")
    st.caption("Likes karein, Comments karein aur achhi routines ko Save (Bookmark) karein!")

    # Post Creation Expander
    with st.expander("➕ Apni Aaj Ki Din-charya / Video Post Karein", expanded=False):
        with st.form("hustle_post_form", clear_on_submit=True):
            p_title = st.text_input("Post Heading:", placeholder="Jaise: 8 Ghante Work + ₹1500 Saving + 1 Hr Skill")
            p_desc = st.text_area("Din-charya Ka Vivran:", placeholder="Aaj subah se shaam tak kya kiya aur kitni pragati hui...")
            p_video = st.file_uploader("Video Upload (MP4 / MOV):", type=["mp4", "mov", "avi"])
            submit_post = st.form_submit_button("🚀 Post Share Karein", type="primary")

            if submit_post:
                if not p_title:
                    st.error("Kripya heading zaroor dalein!")
                else:
                    saved_filename = ""
                    if p_video is not None:
                        saved_filename = f"{ACTIVE_USER}_{int(random.random()*100000)}_{p_video.name}"
                        file_path = os.path.join(UPLOADS_DIR, saved_filename)
                        with open(file_path, "wb") as f:
                            f.write(p_video.getbuffer())

                    cursor.execute("""
                        INSERT INTO community_feed (user_phone, post_date, post_title, routine_text, video_filename)
                        VALUES (?, ?, ?, ?, ?)
                    """, (ACTIVE_USER, today_str, p_title, p_desc, saved_filename))
                    conn.commit()
                    st.balloons()
                    st.success("Aapki din-charya aur video post ho gayi!")
                    st.rerun()

    # Filter: Sabhi Posts vs Meri Saved Posts
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("🌐 Sabhi Community Posts Dekhein", use_container_width=True):
            st.session_state["feed_view_mode"] = "all"
    with col_f2:
        if st.button("🔖 Meri Saved (Bookmarked) Posts", use_container_width=True):
            st.session_state["feed_view_mode"] = "saved"

    st.write("---")

    if st.session_state["feed_view_mode"] == "saved":
        st.markdown("### 🔖 Aapki Saved Posts:")
        posts_df = pd.read_sql_query("""
            SELECT f.id, f.user_phone, f.post_date, f.post_title, f.routine_text, f.video_filename, f.likes_count 
            FROM community_feed f
            INNER JOIN user_saved_posts s ON f.id = s.post_id
            WHERE s.user_phone = ?
            ORDER BY s.id DESC
        """, conn, params=(ACTIVE_USER,))
    else:
        st.markdown("### 📱 Latest Hustle Feed:")
        posts_df = pd.read_sql_query("""
            SELECT id, user_phone, post_date, post_title, routine_text, video_filename, likes_count 
            FROM community_feed ORDER BY id DESC LIMIT 25
        """, conn)

    if posts_df.empty:
        st.info("Koi post nahi mili. Apni pehli din-charya post karein!")
    else:
        for idx, row in posts_df.iterrows():
            post_id = row['id']
            st.markdown(f"""
            <div class="post-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #e5a93c;">👤 {row['user_phone'][:5]}*****</span>
                    <span style="font-size: 0.82rem; color: #94a3b8;">📅 {row['post_date']}</span>
                </div>
                <h3 style="margin: 4px 0 8px 0; color: #ffffff;">{row['post_title']}</h3>
                <p style="color: #cbd5e1; white-space: pre-wrap; font-size: 0.95rem;">{row['routine_text']}</p>
            </div>
            """, unsafe_allow_html=True)

            if row['video_filename']:
                v_path = os.path.join(UPLOADS_DIR, row['video_filename'])
                if os.path.exists(v_path):
                    st.video(v_path)

            # Action Buttons: Like & Save
            c_act1, c_act2, c_act3 = st.columns([1.5, 1.5, 3])
            with c_act1:
                if st.button(f"❤️ Like ({row['likes_count']})", key=f"like_btn_{post_id}"):
                    cursor.execute("UPDATE community_feed SET likes_count = likes_count + 1 WHERE id = ?", (post_id,))
                    conn.commit()
                    st.rerun()

            with c_act2:
                # Check if already saved
                cursor.execute("SELECT id FROM user_saved_posts WHERE user_phone = ? AND post_id = ?", (ACTIVE_USER, post_id))
                is_saved = cursor.fetchone()
                if is_saved:
                    if st.button("❌ Unsave", key=f"unsave_btn_{post_id}"):
                        cursor.execute("DELETE FROM user_saved_posts WHERE user_phone = ? AND post_id = ?", (ACTIVE_USER, post_id))
                        conn.commit()
                        st.rerun()
                else:
                    if st.button("🔖 Save", key=f"save_btn_{post_id}"):
                        cursor.execute("INSERT OR IGNORE INTO user_saved_posts (user_phone, post_id, saved_date) VALUES (?, ?, ?)",
                                       (ACTIVE_USER, post_id, today_str))
                        conn.commit()
                        st.success("Post save ho gayi!")
                        st.rerun()

            # Comment Section Expander
            with st.expander(f"💬 Comments dekhein aur likhein"):
                comments_df = pd.read_sql_query(
                    "SELECT user_phone, comment_text, created_date FROM post_comments WHERE post_id = ? ORDER BY id ASC", 
                    conn, params=(post_id,)
                )
                if not comments_df.empty:
                    for _, c_row in comments_df.iterrows():
                        st.markdown(f"""
                        <div class="comment-bubble">
                            <small style="color: #94a3b8;"><b>{c_row['user_phone'][:5]}*****</b> • {c_row['created_date']}</small><br>
                            <span style="color: #f1f5f9;">{c_row['comment_text']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("Abhi tak koi comment nahi hai. Pehla comment aap karein!")

                # Add new comment form
                with st.form(f"comment_form_{post_id}", clear_on_submit=True):
                    c_input = st.text_input("Apna comment likhein:", placeholder="Zabardast routine bhai...")
                    if st.form_submit_button("Bhejein 💬"):
                        if c_input.strip():
                            cursor.execute("""
                                INSERT INTO post_comments (post_id, user_phone, comment_text, created_date)
                                VALUES (?, ?, ?, ?)
                            """, (post_id, ACTIVE_USER, c_input.strip(), today_str))
                            conn.commit()
                            st.rerun()

            st.write("---")

# ----------------- TAB: ANTI-INSTAGRAM REELS DETOX -----------------
with tab_detox:
    st.subheader("🔥 Anti-Instagram Reels Detox & Daily Wealth Chest")
    st.caption("Instagram par doosron ko ameer banane ke bajaye, yahan har second apna 100 Cr banayein!")

    st.markdown("### ⏱️ Aaj kitne der Reels dekhi? Button dabayein:")
    col_ig1, col_ig2, col_ig3, col_ig4 = st.columns(4)
    with col_ig1:
        if st.button("📱 15 Minute", use_container_width=True, key="btn_ig_15"):
            st.session_state["selected_ig_mins"] = 15
    with col_ig2:
        if st.button("📱 30 Minute", use_container_width=True, key="btn_ig_30"):
            st.session_state["selected_ig_mins"] = 30
    with col_ig3:
        if st.button("📱 60 Minute (1 Hr)", use_container_width=True, key="btn_ig_60"):
            st.session_state["selected_ig_mins"] = 60
    with col_ig4:
        if st.button("🚨 120 Min (2 Hr)", use_container_width=True, key="btn_ig_120"):
            st.session_state["selected_ig_mins"] = 120

    chosen_ig_mins = st.session_state["selected_ig_mins"]
    hourly_opp_cost = 300.0
    lost_money = (chosen_ig_mins / 60.0) * hourly_opp_cost
    compounded_lost_10yr = lost_money * ((1 + 0.15)**10)
    delay_days = (chosen_ig_mins / 15.0)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2a0808 0%, #170404 100%); border: 1px solid #ef4444; border-radius: 12px; padding: 18px; margin-bottom: 12px;">
        <h4 style="color: #ef4444; margin:0;">⚠️ {chosen_ig_mins} MINUTE REELS KA NUKSAAN:</h4>
        <h2 style="color: #ffffff; margin: 8px 0;">₹{lost_money:,.0f} Aaj Barbaad Kiye</h2>
        <p style="color: #fca5a5; margin:0;">
            10 saal ki compounding me yeh nuksaan <b>₹{compounded_lost_10yr:,.0f}</b> ke barabar hai!<br>
            Aapka 100 Crore ka lakshya lagbhag <b>{delay_days:.1f} Din peeche</b> khisak gaya.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_sw1, col_sw2 = st.columns(2)
    with col_sw1:
        if st.button("🟡 Maine Reels chhodi ➔ ₹20 Gold me bachaye!", use_container_width=True, key="btn_swap_gold"):
            g_bought = 20.0 / 7650.0
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, today_str, "Gold (24K Detox Reward)", g_bought, 20.0, "Saved from IG Doomscrolling"))
            conn.commit()
            st.balloons()
            st.success("Zabardast! ₹20 ka 24K Sona jud gaya!")
            st.rerun()
    with col_sw2:
        st.info("💡 Jab bhi Instagram kholne ka man kare, ye button dabayein.")

    st.divider()
    st.markdown("### 🎁 Aaj Ka Secret Wealth Chest (Daily Mystery Loot)")
    cursor.execute("SELECT loot_date, nugget FROM user_loot_log WHERE user_phone = ? AND loot_date = ?", (ACTIVE_USER, today_str))
    today_loot = cursor.fetchone()

    secret_nuggets = [
        "👑 **Naval Ravikant:** 'Kiraye par apna waqt mat becho. Aisi equity ya code banao jo sote waqt bhi kamaye!'",
        "⚡ **Charlie Munger:** 'Pehla ₹10 Lakh bachana sabse mushkil hai, uske baad compounding ka pahiya khud ghoomta hai!'",
        "🛡️ **Warren Buffett:** 'Rule No. 1: Capital kabhi mat gavao. Rule No. 2: Rule No. 1 ko kabhi mat bhoolo!'"
    ]

    if today_loot:
        st.success("✅ **Aaj Ka Chest Unlock Ho Chuka Hai:**")
        st.markdown(f"""
        <div class="vip-card" style="text-align: left; border-color: #38bdf8;">
            {today_loot[1]}
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button("🔓 Aaj Ka Golden Chest Unlock Karein (Open Chest)", type="primary", use_container_width=True, key="btn_open_chest"):
            chosen_nugget = random.choice(secret_nuggets)
            cursor.execute("INSERT INTO user_loot_log (user_phone, loot_date, nugget) VALUES (?, ?, ?)",
                           (ACTIVE_USER, today_str, chosen_nugget))
            conn.commit()
            st.balloons()
            st.rerun()

# ----------------- TAB: AI VOICE COACH -----------------
with tab_audio:
    st.subheader("🎙️ AI Wealth Voice Coach")
    coach_mode = st.radio("Mode:", ["⚡ Hustle & Focus", "👑 Billionaire Mindset"], horizontal=True)
    speech_text = f"Namaskar! 100 Crore ki yatra me aapki networth ₹{total_networth:,.0f} hai. Daily discipline hi amiri ki seedhi hai."
    st.info(f"📜 {speech_text}")
    safe_speech_js = speech_text.replace('"', '\\"').replace('\n', ' ')
    audio_html = f"""
    <div style="text-align: center; margin-top: 10px;">
        <button onclick="speakAudio()" style="background: linear-gradient(135deg, #e5a93c 0%, #b45309 100%); color: #111; font-weight: bold; border: none; padding: 10px 24px; border-radius: 20px; cursor: pointer;">
            🔊 Audio Coach Suney (Play)
        </button>
    </div>
    <script>
    function speakAudio() {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{safe_speech_js}");
        msg.lang = 'hi-IN';
        msg.rate = 0.95;
        window.speechSynthesis.speak(msg);
    }}
    </script>
    """
    st.components.v1.html(audio_html, height=70)

# ----------------- TAB: TARGET REVERSE-ENGINE -----------------
with tab_reverse:
    st.subheader("🎯 100 Crore Reverse-Engine Plan")
    col_hz1, col_hz2, col_hz3 = st.columns(3)
    with col_hz1:
        if st.button("⏱️ 10 Saal", use_container_width=True, key="rev_10"): st.session_state["reverse_horizon_yrs"] = 10
    with col_hz2:
        if st.button("⏱️ 15 Saal", use_container_width=True, key="rev_15"): st.session_state["reverse_horizon_yrs"] = 15
    with col_hz3:
        if st.button("⏱️ 20 Saal", use_container_width=True, key="rev_20"): st.session_state["reverse_horizon_yrs"] = 20

    selected_yrs = st.session_state["reverse_horizon_yrs"]
    remaining_goal = max(TARGET - total_networth, 0.0)
    r_mo = 0.15 / 12
    n_mo = selected_yrs * 12
    fv_from_current = total_networth * ((1 + 0.15)**selected_yrs)
    needed_from_sip = max(TARGET - fv_from_current, 0.0)
    denom = ((1 + r_mo)**n_mo - 1)
    required_monthly = (needed_from_sip * r_mo) / denom if denom > 0 else (remaining_goal / n_mo)
    required_daily = required_monthly / 30

    col_rv1, col_rv2 = st.columns(2)
    with col_rv1: st.metric("Monthly Target", f"₹{required_monthly:,.0f} / mo")
    with col_rv2: st.metric("Daily Run-rate 🎯", f"₹{required_daily:,.0f} / day")

# ----------------- TAB: SPEED BOOSTER -----------------
with tab_booster:
    st.subheader("⚡ 100 Crore Speed Booster")
    base_daily = cash_df["Raqam (₹)"].mean() if not cash_df.empty else 500.0
    if base_daily <= 0: base_daily = 500.0
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.session_state["boost_hustle"] = st.checkbox("🔥 Side-Work (+₹1,000/day)", value=st.session_state["boost_hustle"])
    with c_b2:
        st.session_state["boost_cut"] = st.checkbox("✂️ Zero-Waste Cut (+₹300/day)", value=st.session_state["boost_cut"])
    added_daily = (1000.0 if st.session_state["boost_hustle"] else 0.0) + (300.0 if st.session_state["boost_cut"] else 0.0)
    new_daily = base_daily + added_daily
    st.metric("New Daily Pace", f"₹{new_daily:,.0f} / day", delta=f"+₹{added_daily:,.0f}")

# ----------------- TAB: ELITE 1% CLUB & CARD DOWNLOAD -----------------
with tab_elite:
    st.subheader("👑 The Top 1% Wealth Club")
    badge_name = "👑 CENTURION MOGUL" if total_networth >= 10000000 else "🐺 LONE HUSTLER"
    st.markdown(f"""
    <div class="vip-card">
        <h4 style="color: #e5a93c !important; letter-spacing: 2px; margin: 0;">VERIFIED WEALTH STATUS</h4>
        <h1 style="color: #ffffff !important; font-size: 2.1rem; margin: 10px 0;">{badge_name}</h1>
        <p style="color: #cbd5e0 !important; margin-bottom: 0;">Networth: <b>₹{total_networth:,.0f}</b> | Streak: <b>🔥 {streak} Days</b></p>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TAB: CALENDAR -----------------
with tab_cal:
    st.subheader("📅 Financial Calendar")
    sel_cal_date = st.date_input("Date:", value=date.today(), key="wealth_cal_picker")
    sel_date_str = str(sel_cal_date)
    day_inc = cash_df[cash_df["Tariqh"] == sel_date_str]["Raqam (₹)"].sum() if not cash_df.empty else 0.0
    day_exp = exp_df[exp_df["Tariqh"] == sel_date_str]["Raqam (₹)"].sum() if not exp_df.empty else 0.0
    st.metric("Day Net Savings", f"₹{day_inc - day_exp:,.0f}")

# ----------------- TAB: PASSIVE FIRE FREEDOM ENGINE -----------------
with tab_fire:
    st.subheader("🌴 Passive Freedom Engine")
    st.metric("Net Monthly Passive Income", f"₹{(total_networth * 0.04) / 12:,.0f} / mo")

# ----------------- TAB: TAX & CLEAN IN-HAND -----------------
with tab_tax:
    st.subheader("⚖️ Tax Buffer & Clean In-Hand")
    clean_cash = max(total_net_cash - (total_gross_income * 0.15), 0.0)
    st.metric("Clean In-Hand Networth 🛡️", f"₹{clean_cash + total_assets - total_liabilities:,.0f}")

# ----------------- TAB: UPI ROUND-UP -----------------
with tab_roundup:
    st.subheader("🪙 UPI Spare-Change Round-up")
    if st.button("🟡 ₹10 Micro Gold SIP", key="btn_sip_10"):
        g_bought = 10.0 / 7650.0
        cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                       (ACTIVE_USER, today_str, "Gold (24K Daily SIP)", g_bought, 10.0, "Daily ₹10 Micro SIP"))
        conn.commit()
        st.success("₹10 gold added!")
        st.rerun()

# ----------------- TAB: AI MENTOR -----------------
with tab_ai:
    st.subheader("🧠 AI Wealth Mentor")
    st.success("🎯 Portfolio balanced aur surakshit hai.")

# ----------------- TAB: LUXURY SIMULATOR -----------------
with tab_wishlist:
    st.subheader("🏎️ Luxury Wishlist Simulator")
    st.progress(min((total_networth / 8500000), 1.0))
    st.caption("Sports Car Goal Progress")

# ----------------- TAB: GAME ZONE -----------------
with tab_game:
    st.subheader("🎮 100 Crore Elite Game Zone")
    st.write(f"Player Level: **Active Builder** | Streak: **🔥 {streak} Days**")

# ----------------- TAB 2: INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 Record Income")
        entry_date = st.date_input("Date", value=date.today(), key="cash_date")
        daily_income = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
        custom_note = st.text_input("Source / Note", value="Business")
        if st.form_submit_button("💾 Save Income") and daily_income > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                           (ACTIVE_USER, str(entry_date), daily_income, custom_note))
            conn.commit()
            st.success("Income saved!")
            st.rerun()
    if not cash_df.empty: st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)

# ----------------- TAB: EXPENSES -----------------
with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("💸 Record Expense")
        exp_date = st.date_input("Date", value=date.today(), key="exp_date")
        exp_amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        exp_note = st.text_input("Category / Note", value="Essentials")
        if st.form_submit_button("💾 Save Expense") and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(exp_date), exp_amt, exp_note, exp_note))
            conn.commit()
            st.warning("Expense saved!")
            st.rerun()
    if not exp_df.empty: st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)

# ----------------- TAB: DEBT / LOAN -----------------
with tab_debt:
    st.subheader("⚖️ Debt / Karz Manager")
    if not debt_df.empty: st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 Gold & Physical Assets")
    if not asset_df.empty: st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)

# ----------------- TAB: HEALTH SCORE -----------------
with tab_health:
    st.subheader("🩺 Wealth Health Score")
    st.metric("Health Score", "80 / 100")

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 Savings Rate Analysis")
    st.metric("Savings Rate", f"{savings_rate:.1f}%")

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("Cash In Hand", f"₹{total_net_cash:,.0f}")
    with col_m2: st.metric("Gold & Assets", f"₹{total_assets:,.0f}")
    with col_m3: st.metric("Liabilities (Karz)", f"₹{total_liabilities:,.0f}")
    with col_m4: st.metric("Clean Networth 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 Crore Goal Progress: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 Wealth Milestones Ladder")
    st.write("Step 1: 10 Lakh | Step 2: 1 Crore | Final Goal: 100 Crore 👑")

# ----------------- TAB 5: DAILY DISCIPLINE -----------------
with tab5:
    st.subheader("🔥 Daily Goals & Streak")
    st.metric("Streak", f"{streak} Days Active 🔥")
