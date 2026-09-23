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
    CREATE TABLE IF NOT EXISTS custom_wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        item_name TEXT,
        cost REAL
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
add_column_if_missing("custom_wishlist", "user_phone", "TEXT")

cursor.execute("UPDATE income_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE expense_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE assets_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE debt_history SET user_phone = '9983204295' WHERE user_phone IS NULL")
cursor.execute("UPDATE custom_wishlist SET user_phone = '9983204295' WHERE user_phone IS NULL")
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
    st.session_state["selected_ig_mins"] = 30  # Default 30 min

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
    .metric-box {{
        background-color: {tab_bg};
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(245, 158, 11, 0.3);
        text-align: center;
        margin-bottom: 12px;
    }}
    .danger-box {{
        background: linear-gradient(135deg, #2a0808 0%, #170404 100%);
        border: 1px solid #ef4444;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }}
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000  # 100 Crore

st.title("👑 100 Crore Wealth Hub")
st.caption(f"Khata: **{ACTIVE_USER}** | Anti-Instagram Detox, Audio Coach & 100 Cr Mission")

# Tabs
tab1, tab_detox, tab_audio, tab_reverse, tab_booster, tab_elite, tab_cal, tab_fire, tab_roundup, tab_tax, tab_ai, tab_wishlist, tab_game, tab2, tab_exp, tab_debt, tab_health, tab_analytics, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
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

# ----------------- TAB: ANTI-INSTAGRAM REELS DETOX (1-CLICK BUTTON INTERFACE) -----------------
with tab_detox:
    st.subheader("🔥 Anti-Instagram Reels Detox & Daily Wealth Chest")
    st.caption("Instagram par doosron ko ameer banane ke bajaye, yahan har second apna 100 Cr banayein!")

    # 1. BUTTON-BASED REELS BURN CALCULATOR (NO SLIDER)
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
    hourly_opp_cost = 300.0  # ₹300/hr earning capacity
    lost_money = (chosen_ig_mins / 60.0) * hourly_opp_cost
    compounded_lost_10yr = lost_money * ((1 + 0.15)**10)
    delay_days = (chosen_ig_mins / 15.0)

    st.markdown(f"""
    <div class="danger-box">
        <h4 style="color: #ef4444; margin:0;">⚠️ {chosen_ig_mins} MINUTE REELS KA NUKSAAN:</h4>
        <h2 style="color: #ffffff; margin: 8px 0;">₹{lost_money:,.0f} Aaj Barbaad Kiye</h2>
        <p style="color: #fca5a5; margin:0;">
            10 saal ki compounding me yeh nuksaan <b>₹{compounded_lost_10yr:,.0f}</b> ke barabar hai!<br>
            Aapka 100 Crore ka lakshya lagbhag <b>{delay_days:.1f} Din peeche</b> khisak gaya.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. 1-CLICK SWAP BUTTON
    st.write("#### 🛡️ Turant Bharpayi Karein (Quick Wealth Swap):")
    col_sw1, col_sw2 = st.columns(2)
    with col_sw1:
        if st.button("🟡 Maine Reels chhodi ➔ ₹20 Gold me bachaye!", use_container_width=True, key="btn_swap_gold"):
            g_bought = 20.0 / 7650.0
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, today_str, "Gold (24K Detox Reward)", g_bought, 20.0, "Saved from IG Doomscrolling"))
            conn.commit()
            st.balloons()
            st.success("Zabardast! ₹20 ka 24K Sona aapke khate me jud gaya!")
            st.rerun()
    with col_sw2:
        st.info("💡 Jab bhi Instagram kholne ka man kare, ye button dabayein aur apna gold balance badhayein.")

    # 3. 24 HOURS MYSTERY LOOT CHEST BUTTON
    st.divider()
    st.markdown("### 🎁 Aaj Ka Secret Wealth Chest (Daily Mystery Loot)")
    st.caption("Din me sirf ek baar khulega. Daily ek naya secret billionaire mindset rule:")

    cursor.execute("SELECT loot_date, nugget FROM user_loot_log WHERE user_phone = ? AND loot_date = ?", (ACTIVE_USER, today_str))
    today_loot = cursor.fetchone()

    secret_nuggets = [
        "👑 **Naval Ravikant:** 'Kiraye par apna waqt mat becho. Aisi equity, code ya assets banao jo sote waqt bhi kamayein!'",
        "⚡ **Charlie Munger:** 'Pehla ₹10 Lakh bachana sabse mushkil hai, chahe kuch bhi ho jaye, kharch kaat kar ise poora karo. Uske baad compounding ka pahiya khud ghoomta hai!'",
        "🛡️ **Warren Buffett:** 'Rule No. 1: Capital kabhi mat gavao. Rule No. 2: Rule No. 1 ko kabhi mat bhoolo!'",
        "🔥 **Robert Kiyosaki:** 'Ameer log assets khareedte hain, aur middle class aisi liabilities khareedta hai jise wo assets samajhte hain!'",
        "💎 **The Compound Secret:** 'Agar aap daily sirf ₹500 ka naya cashflow jodte hain, toh 100 Crore ka rasta 80% aasan ho jata hai!'"
    ]

    if today_loot:
        st.success("✅ **Aaj Ka Chest Unlock Ho Chuka Hai:**")
        st.markdown(f"""
        <div class="vip-card" style="text-align: left; border-color: #38bdf8;">
            {today_loot[1]}
        </div>
        """, unsafe_allow_html=True)
        st.caption("Agla mystery chest kal subah 6:00 AM unlock hoga.")
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
    coach_mode = st.radio("Mode:", [
        "⚡ Hustle & Focus",
        "👑 Billionaire Mindset",
        "🛡️ Stoic Shield"
    ], horizontal=True)

    if "Hustle" in coach_mode:
        speech_text = f"Namaskar! 100 Crore ki yatra me swagat hai. Aapki networth ₹{total_networth:,.0f} hai. Daulat kisi jackpot se nahi, roz ki nayi kamai aur discipline se banti hai."
    elif "Billionaire" in coach_mode:
        speech_text = f"Top 1 percent log paise ke liye kaam nahi karte, paisa unke liye kaam karta hai. Aapka ₹{total_assets:,.0f} ka asset portfolio 24 ghante badh raha hai."
    else:
        speech_text = f"Financial stability ka sabse bada niyam shant rehna hai. Gold aur hard assets aapka abhedya qila hain. Faltu kharchon se bachein."

    st.markdown(f"""
    <div class="metric-box" style="text-align: left;">
        <b>📜 Voice Message:</b><br><i>"{speech_text}"</i>
    </div>
    """, unsafe_allow_html=True)

    safe_speech_js = speech_text.replace('"', '\\"').replace('\n', ' ')
    audio_html = f"""
    <div style="text-align: center; margin-top: 15px;">
        <button onclick="speakAudio()" style="background: linear-gradient(135deg, #e5a93c 0%, #b45309 100%); color: #111; font-weight: bold; border: none; padding: 12px 28px; border-radius: 25px; font-size: 1.05rem; cursor: pointer;">
            🔊 Audio Coach Suney (Play)
        </button>
        <button onclick="window.speechSynthesis.cancel()" style="background: #334155; color: #fff; font-weight: bold; border: none; padding: 12px 20px; border-radius: 25px; font-size: 1.05rem; cursor: pointer; margin-left: 10px;">
            ⏹️ Stop
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
    st.components.v1.html(audio_html, height=80)

# ----------------- TAB: TARGET REVERSE-ENGINE -----------------
with tab_reverse:
    st.subheader("🎯 100 Crore Reverse-Engine Plan")
    col_hz1, col_hz2, col_hz3, col_hz4 = st.columns(4)
    with col_hz1:
        if st.button("⏱️ 10 Saal", use_container_width=True, key="rev_10"): st.session_state["reverse_horizon_yrs"] = 10
    with col_hz2:
        if st.button("⏱️ 15 Saal", use_container_width=True, key="rev_15"): st.session_state["reverse_horizon_yrs"] = 15
    with col_hz3:
        if st.button("⏱️ 20 Saal", use_container_width=True, key="rev_20"): st.session_state["reverse_horizon_yrs"] = 20
    with col_hz4:
        if st.button("⏱️ 25 Saal", use_container_width=True, key="rev_25"): st.session_state["reverse_horizon_yrs"] = 25

    selected_yrs = st.session_state["reverse_horizon_yrs"]
    remaining_goal = max(TARGET - total_networth, 0.0)
    r_mo = 0.15 / 12
    n_mo = selected_yrs * 12
    fv_from_current = total_networth * ((1 + 0.15)**selected_yrs)
    needed_from_sip = max(TARGET - fv_from_current, 0.0)
    denom = ((1 + r_mo)**n_mo - 1)
    required_monthly = (needed_from_sip * r_mo) / denom if denom > 0 else (remaining_goal / n_mo)
    required_daily = required_monthly / 30
    required_yearly = required_monthly * 12

    col_rv1, col_rv2, col_rv3 = st.columns(3)
    with col_rv1: st.metric("Salana Bachat", f"₹{required_yearly:,.0f} / yr")
    with col_rv2: st.metric("Monthly Target", f"₹{required_monthly:,.0f} / mo")
    with col_rv3: st.metric("Daily Run-rate 🎯", f"₹{required_daily:,.0f} / day")

    if st.button(f"📌 Set Daily Target ₹{required_daily:,.0f}", key="btn_sync_goal", type="primary"):
        st.session_state["custom_daily_target"] = round(required_daily)
        st.success(f"Daily target ₹{required_daily:,.0f} set ho gaya!")

# ----------------- TAB: SPEED BOOSTER -----------------
with tab_booster:
    st.subheader("⚡ 100 Crore Speed Booster")
    base_daily = cash_df["Raqam (₹)"].mean() if not cash_df.empty else 500.0
    if base_daily <= 0: base_daily = 500.0
    raw_years = ((TARGET - total_networth) / base_daily) / 365
    st.markdown(f"#### 🐢 Current Pace: **₹{base_daily:,.0f} / day** (~{raw_years:.0f} yrs)")

    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.session_state["boost_hustle"] = st.checkbox("🔥 Side-Work (+₹1,000/day)", value=st.session_state["boost_hustle"])
    with c_b2:
        st.session_state["boost_cut"] = st.checkbox("✂️ Zero-Waste Cut (+₹300/day)", value=st.session_state["boost_cut"])

    added_daily = 0.0
    if st.session_state["boost_hustle"]: added_daily += 1000.0
    if st.session_state["boost_cut"]: added_daily += 300.0
    new_daily = base_daily + added_daily
    new_monthly_saving = new_daily * 30

    r_mo_b = 0.15 / 12
    try:
        n_months = math.log(((TARGET - total_networth) * r_mo_b / new_monthly_saving) + 1) / math.log(1 + r_mo_b)
        accelerated_years = n_months / 12
    except Exception:
        accelerated_years = 15.0

    col_acc1, col_acc2 = st.columns(2)
    with col_acc1: st.metric("New Daily Pace", f"₹{new_daily:,.0f} / day", delta=f"+₹{added_daily:,.0f}")
    with col_acc2: st.metric("New Time to 100 Cr 👑", f"Keval {accelerated_years:.1f} Yrs!")

# ----------------- TAB: ELITE 1% CLUB & CARD DOWNLOAD -----------------
with tab_elite:
    st.subheader("👑 The Top 1% Wealth Club")
    if total_networth >= 100000000:
        percentile = "Top 0.01% Titan"
        badge_name = "🔱 SHADOW TITAN"
    elif total_networth >= 10000000:
        percentile = "Top 0.5% Crorepati"
        badge_name = "👑 CENTURION MOGUL"
    elif total_networth >= 2500000:
        percentile = "Top 3% Builder"
        badge_name = "🦅 EMPIRE ARCHITECT"
    elif total_networth >= 500000:
        percentile = "Top 10% Capitalist"
        badge_name = "🛡️ GOLD GUARDIAN"
    elif total_networth >= 50000:
        percentile = "Top 30% Rising Star"
        badge_name = "⚡ RISING SPARK"
    else:
        percentile = "Ground Zero Builder"
        badge_name = "🐺 LONE HUSTLER"

    st.markdown(f"""
    <div class="vip-card">
        <h4 style="color: #e5a93c !important; letter-spacing: 2px; margin: 0;">VERIFIED WEALTH STATUS</h4>
        <h1 style="color: #ffffff !important; font-size: 2.1rem; margin: 10px 0;">{percentile}</h1>
        <p style="color: #cbd5e0 !important; font-size: 1rem; margin-bottom: 0;">
            Rank: <b>{badge_name}</b> | Streak: <b>🔥 {streak} Days</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

    def generate_flex_image(badge, streak_days, rank_text):
        img = Image.new('RGB', (800, 450), color=(18, 20, 26))
        draw = ImageDraw.Draw(img)
        draw.rectangle([15, 15, 785, 435], outline=(229, 169, 60), width=4)
        draw.text((400, 70), "100 CRORE WEALTH CLUB", fill=(229, 169, 60), anchor="mm")
        draw.text((400, 160), badge, fill=(255, 255, 255), anchor="mm")
        draw.text((400, 240), f"STATUS: {rank_text}", fill=(160, 174, 192), anchor="mm")
        draw.text((400, 310), f"DISCIPLINE STREAK: {streak_days} DAYS", fill=(245, 158, 11), anchor="mm")
        draw.text((400, 380), "OFFICIAL VERIFIED WEALTH BUILDER", fill=(100, 116, 139), anchor="mm")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    st.write("")
    flex_img_data = generate_flex_image(badge_name, streak, percentile)
    st.download_button(
        label="📸 HD Status Card Download (PNG)",
        data=flex_img_data,
        file_name=f"Elite_Card_{ACTIVE_USER}.png",
        mime="image/png",
        key="btn_dl_flex_png"
    )

# ----------------- TAB: CALENDAR -----------------
with tab_cal:
    st.subheader("📅 Financial Calendar")
    sel_cal_date = st.date_input("Date:", value=date.today(), key="wealth_cal_picker")
    sel_date_str = str(sel_cal_date)

    day_inc = cash_df[cash_df["Tariqh"] == sel_date_str]["Raqam (₹)"].sum() if not cash_df.empty else 0.0
    day_exp = exp_df[exp_df["Tariqh"] == sel_date_str]["Raqam (₹)"].sum() if not exp_df.empty else 0.0
    day_net = day_inc - day_exp

    col_cd1, col_cd2, col_cd3 = st.columns(3)
    with col_cd1: st.metric("Day Income", f"₹{day_inc:,.0f}")
    with col_cd2: st.metric("Day Expense", f"₹{day_exp:,.0f}")
    with col_cd3: st.metric("Net Savings", f"₹{day_net:,.0f}", delta=f"{day_net:+,.0f}")

# ----------------- TAB: PASSIVE FIRE FREEDOM ENGINE -----------------
with tab_fire:
    st.subheader("🌴 Passive Freedom Engine")
    withdrawal_rate = 4.0
    annual_passive = total_networth * (withdrawal_rate / 100)
    monthly_passive = annual_passive / 12
    st.metric("Net Monthly Passive Income", f"₹{monthly_passive:,.0f} / mo")

# ----------------- TAB: TAX & CLEAN IN-HAND -----------------
with tab_tax:
    st.subheader("⚖️ Tax Buffer & Clean In-Hand")
    tax_bracket = 15
    tax_reserve = total_gross_income * (tax_bracket / 100)
    clean_in_hand_cash = max(total_net_cash - tax_reserve, 0.0)
    clean_networth = max(clean_in_hand_cash + total_assets + total_receivables - total_liabilities, 0.0)
    col_res1, col_res2 = st.columns(2)
    with col_res1: st.metric("Gross Networth", f"₹{total_networth:,.0f}")
    with col_res2: st.metric("Clean In-Hand 🛡️", f"₹{clean_networth:,.0f}")

# ----------------- TAB: UPI ROUND-UP -----------------
with tab_roundup:
    st.subheader("🪙 UPI Spare-Change Round-up & Gold SIP")
    col_ru1, col_ru2 = st.columns(2)
    with col_ru1:
        spend_amt = st.number_input("UPI Amount (₹):", min_value=1.0, value=73.0, step=5.0)
        round_to = 50
        rounded_val = math.ceil(spend_amt / round_to) * round_to
        spare_change = rounded_val - spend_amt if rounded_val > spend_amt else round_to
        st.info(f"💡 Spend: ₹{spend_amt:.0f} ➔ Round-up: ₹{rounded_val:.0f} ➔ **Chillar: ₹{spare_change:.0f}**")
        
        if st.button("🟡 Chillar ko Gold me jodein!", key="btn_roundup_save"):
            gold_price_gram = 7650.0
            grams_bought = spare_change / gold_price_gram
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, today_str, "Gold (24K Round-up)", grams_bought, spare_change, f"UPI Round-up on ₹{spend_amt} spend"))
            conn.commit()
            st.balloons()
            st.success("Gold jud gaya!")
            st.rerun()

    with col_ru2:
        st.markdown("#### ⚡ 1-Click Micro Gold SIP")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🟡 ₹10 Gold", key="btn_sip_10"):
                g_bought = 10.0 / 7650.0
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                               (ACTIVE_USER, today_str, "Gold (24K Daily SIP)", g_bought, 10.0, "Daily ₹10 Micro SIP"))
                conn.commit()
                st.success("₹10 gold added!")
                st.rerun()
        with col_btn2:
            if st.button("🟡 ₹50 Gold", key="btn_sip_50"):
                g_bought = 50.0 / 7650.0
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                               (ACTIVE_USER, today_str, "Gold (24K Daily SIP)", g_bought, 50.0, "Daily ₹50 Micro SIP"))
                conn.commit()
                st.success("₹50 gold added!")
                st.rerun()

# ----------------- TAB: AI MENTOR -----------------
with tab_ai:
    st.subheader("🧠 AI Wealth Mentor")
    if total_networth == 0:
        st.info("💡 Khate me kamai darj karein.")
    else:
        cash_ratio = (total_net_cash / total_networth) * 100 if total_networth > 0 else 0
        if cash_ratio > 70:
            st.warning(f"⚠️ {cash_ratio:.1f}% paisa cash me hai, ise gold me badlein!")
        else:
            st.success("🎯 Portfolio balanced aur surakshit hai.")

# ----------------- TAB: LUXURY SIMULATOR -----------------
with tab_wishlist:
    st.subheader("🏎️ Luxury Wishlist Simulator")
    luxury_items = [
        {"icon": "⌚", "name": "Rolex Watch", "cost": 1500000},
        {"icon": "🏎️", "name": "Sports Car (BMW/Merc)", "cost": 8500000},
        {"icon": "👑", "name": "Rolls-Royce Phantom", "cost": 95000000},
        {"icon": "🏰", "name": "Penthouse / Mansion", "cost": 250000000}
    ]
    for item in luxury_items:
        c_cost = item["cost"]
        pct = min((total_networth / c_cost) * 100, 100.0)
        col_w1, col_w2 = st.columns([3, 1])
        with col_w1:
            st.write(f"### {item['icon']} {item['name']} — `₹{c_cost:,.0f}`")
            st.progress(pct / 100)
        with col_w2:
            if total_networth >= c_cost: st.success("✅ UNLOCKED!")
            else: st.warning(f"⏳ `{pct:.2f}%`")
        st.divider()

# ----------------- TAB: GAME ZONE -----------------
with tab_game:
    st.subheader("🎮 100 Crore Elite Game Zone")
    st.markdown(f"""
    <div class="vip-card">
        <h3 style="color: #e5a93c !important; margin: 0;">CURRENT RANK</h3>
        <h1 style="color: #ffffff !important; font-size: 2.2rem; margin: 10px 0;">{badge_name}</h1>
        <p style="color: #a0aec0 !important; font-size: 1rem;">DISCIPLINE STREAK: <b>🔥 {streak} DAYS</b></p>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TAB 2: INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 Record Income")
        col_a, col_b = st.columns(2)
        with col_a: entry_date = st.date_input("Date", value=date.today(), key="cash_date")
        with col_b: daily_income = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("Source", ["Business", "Daily Savings", "Trading", "Side Hustle", "Other"])
        with col_cat2: custom_note = st.text_input("Note", value="")
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 Save Income")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                           (ACTIVE_USER, str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} jud gaye!")
            st.rerun()

    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Income Entry"):
            del_id = st.selectbox("Select entry:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'Raqam (₹)'].values[0]:,.0f}",
                                  key="sel_del_income")
            if st.button("❌ Delete", key="btn_del_income"):
                cursor.execute("DELETE FROM income_history WHERE id = ? AND user_phone = ?", (del_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: EXPENSES -----------------
with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("💸 Record Expense")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            exp_date = st.date_input("Date", value=date.today(), key="exp_date")
            exp_cat = st.selectbox("Category", ["Essentials", "Travel/Fuel", "Food/Groceries", "Business", "Other"])
        with col_e2:
            exp_amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            exp_note = st.text_input("Note", value="")
        submit_exp = st.form_submit_button("💾 Save Expense")

        if submit_exp and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} darj hue!")
            st.rerun()

    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Expense"):
            del_exp_id = st.selectbox("Select expense:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'Raqam (₹)'].values[0]:,.0f}",
                                      key="sel_del_exp")
            if st.button("❌ Delete", key="btn_del_exp"):
                cursor.execute("DELETE FROM expense_history WHERE id = ? AND user_phone = ?", (del_exp_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: DEBT / LOAN -----------------
with tab_debt:
    st.subheader("⚖️ Debt / Karz Manager")
    with st.form("debt_form", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_date = st.date_input("Date", value=date.today(), key="debt_date")
            debt_type = st.radio("Type", ["Mera Karz (Liability - Dena hai)", "Mera Paisa Bahar (Asset - Lena hai)"])
        with col_d2:
            d_person = st.text_input("Name", value="")
            d_amount = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
        d_note = st.text_input("Reason", value="")
        submit_debt = st.form_submit_button("💾 Save Debt Record")

        if submit_debt and d_amount > 0:
            cursor.execute("INSERT INTO debt_history (user_phone, entry_date, debt_type, person_name, amount, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(d_date), debt_type, d_person, d_amount, d_note))
            conn.commit()
            st.success("Record save ho gaya!")
            st.rerun()

    if not debt_df.empty:
        st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Debt"):
            del_debt_id = st.selectbox("Select record:", options=debt_df["id"].tolist(),
                                       format_func=lambda x: f"ID {x} - ₹{debt_df.loc[debt_df['id']==x, 'Raqam (₹)'].values[0]:,.0f}",
                                       key="sel_del_debt")
            if st.button("❌ Delete", key="btn_del_debt"):
                cursor.execute("DELETE FROM debt_history WHERE id = ? AND user_phone = ?", (del_debt_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 Gold & Physical Assets")
    col_gr1, col_gr2, col_gr3 = st.columns(3)
    with col_gr1: st.info("🟡 24K Gold: **₹7,650 / g**")
    with col_gr2: st.info("🟠 22K Gold: **₹7,050 / g**")
    with col_gr3: st.info("⚪ Silver: **₹92 / g**")

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: asset_date = st.date_input("Date", value=date.today(), key="asset_date")
        with col2: gold_purity = st.selectbox("Type", ["24K (99.9% Pure)", "22K (Jewellery)", "Silver", "Plot / Land", "Property", "Other"])
        
        c_g1, c_g2 = st.columns(2)
        with c_g1: grams = st.number_input("Grams / Qty:", min_value=0.1, value=10.0, step=0.5)
        with c_g2: rate_per_gram = st.number_input("Rate / Valuation (₹):", min_value=50.0, value=7650.0, step=50.0)
        calc_val = grams * rate_per_gram if "Gold" in gold_purity or "Silver" in gold_purity else rate_per_gram
        asset_note = st.text_input("Description:", value="Physical Asset")

        submit_asset = st.form_submit_button("💾 Save Asset")
        if submit_asset and calc_val > 0:
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(asset_date), gold_purity, grams, calc_val, asset_note))
            conn.commit()
            st.success("Asset save ho gaya!")
            st.rerun()

    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Asset"):
            del_asset_id = st.selectbox("Select asset:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'Type'].values[0]}",
                                        key="sel_del_asset")
            if st.button("❌ Delete", key="btn_del_asset"):
                cursor.execute("DELETE FROM assets_history WHERE id = ? AND user_phone = ?", (del_asset_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: HEALTH SCORE -----------------
with tab_health:
    st.subheader("🩺 Wealth Health Score")
    score = 75 if total_networth > 0 else 25
    st.metric("Health Score", f"{score} / 100")
    st.progress(score / 100)

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 Savings Rate Analysis")
    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1: st.metric("Total Income", f"₹{total_gross_income:,.0f}")
    with col_an2: st.metric("Total Expenses", f"₹{total_expenses:,.0f}")
    with col_an3: st.metric("Savings Rate", f"{savings_rate:.1f}%")

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("Cash In Hand", f"₹{total_net_cash:,.0f}")
    with col_m2: st.metric("Gold & Assets", f"₹{total_assets:,.0f}")
    with col_m3: st.metric("Karz (Liabilities)", f"₹{total_liabilities:,.0f}")
    with col_m4: st.metric("Clean Networth 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 Crore Goal Progress: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 Crore Target Remaining: ₹{TARGET - total_networth:,.0f}")

    st.divider()
    st.subheader("📅 Current Month Snapshot")
    col_mo1, col_mo2, col_mo3 = st.columns(3)
    with col_mo1: st.metric("This Month Income", f"₹{month_inc:,.0f}")
    with col_mo2: st.metric("This Month Expense", f"₹{month_exp:,.0f}")
    with col_mo3: st.metric("This Month Savings", f"₹{month_net_savings:,.0f}")

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 Wealth Milestones Ladder")
    milestones = [
        ("Step 1: 10 Lakh", 1000000),
        ("Step 2: 50 Lakh", 5000000),
        ("Step 3: 1 Crore", 10000000),
        ("Step 4: 5 Crore", 50000000),
        ("Step 5: 10 Crore", 100000000),
        ("Step 6: 50 Crore", 500000000),
        ("Final Goal: 100 Crore 👑", 1000000000),
    ]
    for name, target_amt in milestones:
        if total_networth >= target_amt:
            st.success(f"✅ **{name}** — Reached! (₹{target_amt:,.0f})")
        else:
            diff = target_amt - total_networth
            pct = min((total_networth / target_amt) * 100, 100.0)
            st.warning(f"⏳ **{name}** — `{pct:.2f}%` done (₹{diff:,.0f} to go)")

# ----------------- TAB 5: DAILY DISCIPLINE -----------------
with tab5:
    st.subheader("🔥 Daily Goals & Streak")
    today_savings = 0.0
    if not cash_df.empty:
        today_rows = cash_df[cash_df["Tariqh"] == today_str]
        today_savings = today_rows["Raqam (₹)"].sum()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        current_target = st.number_input("Daily Income Target (₹):", min_value=100.0, value=float(st.session_state["custom_daily_target"]), step=500.0)
    with col_d2:
        st.metric("Today Earned", f"₹{today_savings:,.0f}")

    daily_prog = min(today_savings / current_target, 1.0) if current_target > 0 else 0.0
    st.write(f"### Daily Progress: `{daily_prog * 100:.1f}%`")
    st.progress(daily_prog)
    if daily_prog >= 1.0:
        st.balloons()
        st.success("🔥 Target Completed!")
