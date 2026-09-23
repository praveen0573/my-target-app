import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import io
import requests
import math
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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

with st.sidebar:
    st.title("👤 यूज़र प्रोफ़ाइल")
    st.success(f"खाता: **{ACTIVE_USER}**")
    
    theme_choice = st.selectbox(
        "थीम चुनें:",
        ["🌟 रॉयल गोल्ड डार्क", "☀️ क्लासिक ब्राइट लाइट", "🌌 डीप नेवी ब्लू", "🌿 लग्ज़री ग्रीन"]
    )
    
    st.divider()
    st.subheader("🔐 पिन बदलें")
    with st.expander("पिन अपडेट करें"):
        with st.form("user_change_pin"):
            u_old = st.text_input("पुराना पिन:", type="password", max_chars=4)
            u_new = st.text_input("नया पिन:", type="password", max_chars=4)
            if st.form_submit_button("💾 नया पिन सेव करें"):
                cursor.execute("SELECT pin FROM users WHERE phone = ?", (ACTIVE_USER,))
                cur_p = cursor.fetchone()
                if cur_p and u_old != cur_p[0]:
                    st.error("पुराना पिन गलत है!")
                elif len(u_new) != 4 or not u_new.isdigit():
                    st.error("नया पिन 4 अंकों का होना चाहिए!")
                else:
                    cursor.execute("UPDATE users SET pin = ? WHERE phone = ?", (u_new, ACTIVE_USER))
                    conn.commit()
                    st.success("पिन बदल गया!")

    st.divider()
    st.subheader("💾 बैकअप डाउनलोड")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp:
            st.download_button(
                label="📥 बैकअप डाउनलोड करें",
                data=fp,
                file_name=f"wealth_backup_{ACTIVE_USER}_{date.today()}.db",
                mime="application/octet-stream"
            )

    st.divider()
    if st.button("लॉगआउट करें 🔒", type="primary"):
        st.session_state["logged_user"] = None
        st.rerun()

# Theme CSS
if theme_choice == "☀️ क्लासिक ब्राइट लाइट":
    bg_color = "#ffffff"
    text_color = "#111827"
    accent = "#b45309"
    tab_bg = "#f3f4f6"
    btn_bg = "#1d4ed8"
    btn_text = "#ffffff"
elif theme_choice == "🌌 डीप नेवी ब्लू":
    bg_color = "#0a192f"
    text_color = "#f8fafc"
    accent = "#38bdf8"
    tab_bg = "#1e293b"
    btn_bg = "#38bdf8"
    btn_text = "#0f172a"
elif theme_choice == "🌿 लग्ज़री ग्रीन":
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
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000  # 100 Crore

st.title("👑 100 Crore Wealth Hub")
st.caption(f"खाता: **{ACTIVE_USER}** | रिवर्स-इंजीनियरिंग, स्पीड बूस्टर व 100 Cr मिशन")

# Tabs
tab1, tab_reverse, tab_booster, tab_elite, tab_cal, tab_fire, tab_roundup, tab_tax, tab_ai, tab_wishlist, tab_game, tab2, tab_exp, tab_debt, tab_health, tab_analytics, tab3, tab4, tab5 = st.tabs([
    "📊 डैशबोर्ड", 
    "🎯 रिवर्स लक्ष्य इंजन",
    "⚡ स्पीड बूस्टर",
    "👑 टॉप 1% क्लब",
    "📅 कैलेंडर",
    "🌴 पैसिव आज़ादी",
    "🪙 UPI राउंड-अप",
    "⚖️ टैक्स व इन-हैंड",
    "🧠 AI मेंटॉर",
    "🏎️ लग्ज़री सिमुलेटर",
    "🎮 गेम ज़ोन",
    "💵 कमाई", 
    "💸 ख़र्च",
    "⚖️ कर्ज़ / उधारी",
    "🩺 वेल्थ स्कोर",
    "📈 बचत दर", 
    "🥇 गोल्ड व एसेट्स", 
    "🚀 100 Cr रोडमैप",
    "🔥 दैनिक अनुशासन"
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

# ----------------- TAB: TARGET REVERSE-ENGINE (NEW & POWERFUL) -----------------
with tab_reverse:
    st.subheader("🎯 ₹100 करोड़ का रिवर्स-गणित व दैनिक एक्शन प्लान")
    st.caption("100 करोड़ के लक्ष्य को छोटे, साफ़ और आसान दैनिक नंबरों में तोड़ें:")

    st.write("**आप 100 करोड़ कितने साल में हासिल करना चाहते हैं? बटन दबाएँ:**")
    col_hz1, col_hz2, col_hz3, col_hz4 = st.columns(4)
    with col_hz1:
        if st.button("⏱️ 10 साल में", use_container_width=True, key="rev_10"):
            st.session_state["reverse_horizon_yrs"] = 10
    with col_hz2:
        if st.button("⏱️ 15 साल में", use_container_width=True, key="rev_15"):
            st.session_state["reverse_horizon_yrs"] = 15
    with col_hz3:
        if st.button("⏱️ 20 साल में", use_container_width=True, key="rev_20"):
            st.session_state["reverse_horizon_yrs"] = 20
    with col_hz4:
        if st.button("⏱️ 25 साल में", use_container_width=True, key="rev_25"):
            st.session_state["reverse_horizon_yrs"] = 25

    selected_yrs = st.session_state["reverse_horizon_yrs"]
    remaining_goal = max(TARGET - total_networth, 0.0)

    # 15% सालाना रिटर्न पर कम्पाउंडिंग रिवर्स गणना
    r_mo = 0.15 / 12
    n_mo = selected_yrs * 12
    # FV = P*(1+r)^n + PMT * [((1+r)^n - 1)/r]
    # PMT = (FV - P*(1+r)^n) * r / ((1+r)^n - 1)
    fv_from_current = total_networth * ((1 + 0.15)**selected_yrs)
    needed_from_sip = max(TARGET - fv_from_current, 0.0)
    
    denom = ((1 + r_mo)**n_mo - 1)
    if denom > 0:
        required_monthly = (needed_from_sip * r_mo) / denom
    else:
        required_monthly = remaining_goal / n_mo

    required_daily = required_monthly / 30
    required_yearly = required_monthly * 12

    st.write(f"### 📍 **{selected_yrs} वर्षों** में 100 करोड़ तक पहुँचने का प्लान:")
    
    col_rv1, col_rv2, col_rv3 = st.columns(3)
    with col_rv1:
        st.metric("सालाना बचत / निवेश", f"₹{required_yearly:,.0f} / वर्ष")
    with col_rv2:
        st.metric("मासिक बचत लक्ष्य", f"₹{required_monthly:,.0f} / माह")
    with col_rv3:
        st.metric("दैनिक आवश्यक कमाई 🎯", f"₹{required_daily:,.0f} / दिन")

    if st.button(f"📌 आज का दैनिक लक्ष्य ₹{required_daily:,.0f} सेट करें", key="btn_sync_goal", type="primary"):
        st.session_state["custom_daily_target"] = round(required_daily)
        st.success(f"शानदार! आपका दैनिक अनुशासन लक्ष्य ₹{required_daily:,.0f} पर सेट हो गया!")

    st.divider()
    st.markdown("#### 🏢 इस दैनिक लक्ष्य को पूरा करने के 3 बिज़नेस रास्ते:")
    st.caption("100 करोड़ कभी केवल एक तनख्वाह से नहीं बनता, यह वॉल्यूम और वैल्यू से बनता है:")

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        units_500 = math.ceil(required_monthly / 500)
        st.markdown(f"""
        <div class="metric-box">
            <b>📦 ₹500 का प्रॉडक्ट</b><br>
            माह में चाहिए: <b>{units_500:,} ग्राहक</b><br>
            <small>(ई-कॉमर्स / डिजिटल टूल्स)</small>
        </div>
        """, unsafe_allow_html=True)
    with b_col2:
        units_5000 = math.ceil(required_monthly / 5000)
        st.markdown(f"""
        <div class="metric-box">
            <b>💼 ₹5,000 की सर्विस</b><br>
            माह में चाहिए: <b>{units_5000:,} क्लाइंट्स</b><br>
            <small>(लोकल SEO / डिजिटल एजेंसी)</small>
        </div>
        """, unsafe_allow_html=True)
    with b_col3:
        units_50000 = math.ceil(required_monthly / 50000)
        st.markdown(f"""
        <div class="metric-box">
            <b>🤝 ₹50,000 की हाई-टिकट डील</b><br>
            माह में चाहिए: <b>{units_50000:,} क्लाइंट्स</b><br>
            <small>(कॉन्ट्रैक्ट्स / B2B कंसल्टिंग)</small>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB: SPEED BOOSTER -----------------
with tab_booster:
    st.subheader("⚡ 100 करोड़ स्पीड एक्सीलरेटर (Wealth Multiplier)")
    st.caption("हज़ारों साल का इंतज़ार खत्म: 2 छोटे फ़ाइनेंशियल फ़ैसले जो 100 करोड़ को आपकी ज़िंदगी में खींच लाएँगे!")

    base_daily = cash_df["Raqam (₹)"].mean() if not cash_df.empty else 500.0
    if base_daily <= 0:
        base_daily = 500.0

    raw_years = ((TARGET - total_networth) / base_daily) / 365
    st.markdown(f"#### 🐢 वर्तमान धीमी गति: **₹{base_daily:,.0f} / दिन** (समय लगेगा: ~{raw_years:.0f} वर्ष)")

    st.write("---")
    st.write("### 🚀 नीचे दिए गए बूस्टर्स को चालू (ON) करके जादू देखें:")

    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.session_state["boost_hustle"] = st.checkbox("🔥 बूस्टर 1: डिजिटल साइड-वर्क (+₹1,000/दिन)", value=st.session_state["boost_hustle"])
        st.caption("फ़्रीलांसिंग, डिजिटल स्किल या साइड बिज़नेस से रोज़ का अतिरिक्त कैश।")
    with c_b2:
        st.session_state["boost_cut"] = st.checkbox("✂️ बूस्टर 2: ज़ीरो-वेस्ट ख़र्च कटिंग (+₹300/दिन)", value=st.session_state["boost_cut"])
        st.caption("चाय, पेट्रोल व गैर-ज़रूरी छोटे ख़र्चों से बचाकर सोने में जमा करना।")

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
    with col_acc1:
        st.metric("नई बूस्टेड दैनिक कमाई", f"₹{new_daily:,.0f} / दिन", delta=f"+₹{added_daily:,.0f}")
    with col_acc2:
        st.metric("100 करोड़ पहुँचने का नया समय 👑", f"केवल {accelerated_years:.1f} वर्ष!")

    years_saved = max(raw_years - accelerated_years, 0.0)
    st.success(f"🎉 **अविश्वसनीय छलांग:** इन 2 छोटे बूस्टर्स ने आपकी ज़िंदगी के लगभग **{years_saved:,.0f} वर्ष बचा लिए**!")

# ----------------- TAB: ELITE 1% CLUB & CARD DOWNLOAD -----------------
with tab_elite:
    st.subheader("👑 The Top 1% Wealth Club & Future Time-Machine")
    st.caption("जानिए आप देश और दुनिया में किस स्तर पर खड़े हैं:")

    if total_networth >= 100000000:
        percentile = "Top 0.01% Titan"
        badge_name = "🔱 SHADOW TITAN"
    elif total_networth >= 10000000:
        percentile = "Top 0.5% Crorepati"
        badge_name = "👑 CENTURION MOGUL"
    elif total_networth >= 2500000:
        percentile = "Top 3% Wealth Builder"
        badge_name = "🦅 EMPIRE ARCHITECT"
    elif total_networth >= 500000:
        percentile = "Top 10% Capitalist"
        badge_name = "🛡️ GOLD GUARDIAN"
    elif total_networth >= 50000:
        percentile = "Top 30% Rising Player"
        badge_name = "⚡ RISING SPARK"
    else:
        percentile = "Ground Zero Builder"
        badge_name = "🐺 LONE HUSTLER"

    st.markdown(f"""
    <div class="vip-card">
        <h4 style="color: #e5a93c !important; letter-spacing: 2px; margin: 0;">VERIFIED WEALTH STATUS</h4>
        <h1 style="color: #ffffff !important; font-size: 2.1rem; margin: 10px 0;">{percentile}</h1>
        <p style="color: #cbd5e0 !important; font-size: 1rem; margin-bottom: 0;">
            रैंक: <b>{badge_name}</b> | स्ट्रीक: <b>🔥 {streak} दिन</b>
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
        label="📸 अपना HD स्टेटस कार्ड डाउनलोड करें (PNG)",
        data=flex_img_data,
        file_name=f"Elite_Card_{ACTIVE_USER}.png",
        mime="image/png",
        key="btn_dl_flex_png"
    )

    st.divider()
    st.subheader("⏳ Future Time-Machine (1-Click Future Prediction)")
    st.write("**कितने साल आगे का भविष्य देखना है? नीचे बटन दबाएँ:**")

    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    with c_btn1:
        if st.button("🚀 3 साल बाद", use_container_width=True, key="btn_yr_3"):
            st.session_state["selected_future_yrs"] = 3
    with c_btn2:
        if st.button("🚀 5 साल बाद", use_container_width=True, key="btn_yr_5"):
            st.session_state["selected_future_yrs"] = 5
    with c_btn3:
        if st.button("🚀 10 साल बाद", use_container_width=True, key="btn_yr_10"):
            st.session_state["selected_future_yrs"] = 10
    with c_btn4:
        if st.button("👑 15 साल बाद", use_container_width=True, key="btn_yr_15"):
            st.session_state["selected_future_yrs"] = 15

    chosen_yrs = st.session_state["selected_future_yrs"]
    current_year = date.today().year
    future_year = current_year + chosen_yrs
    
    monthly_runrate = max(month_net_savings, 5000.0)
    r_mo_tm = 0.15 / 12
    n_mo_tm = chosen_yrs * 12
    future_val = (total_networth * ((1 + 0.15)**chosen_yrs)) + (monthly_runrate * (((1 + r_mo_tm)**n_mo_tm - 1) / r_mo_tm))
    future_passive_mo = (future_val * 0.05) / 12

    st.write(f"### 🔮 वर्ष **{future_year}** ({chosen_yrs} साल बाद) का प्रेडिक्शन:")
    col_tm1, col_tm2 = st.columns(2)
    with col_tm1:
        st.metric(f"वर्ष {future_year} में नेटवर्थ 💰", f"₹{future_val:,.0f}")
    with col_tm2:
        st.metric(f"पैसिव सैलरी 🌴", f"₹{future_passive_mo:,.0f} / माह")

# ----------------- TAB: CALENDAR -----------------
with tab_cal:
    st.subheader("📅 दैनिक वित्तीय कैलेंडर व डायरी")
    sel_cal_date = st.date_input("तारीख चुनें:", value=date.today(), key="wealth_cal_picker")
    sel_date_str = str(sel_cal_date)

    day_inc = 0.0
    day_exp = 0.0
    day_inc_df = pd.DataFrame()
    day_exp_df = pd.DataFrame()
    day_asset_df = pd.DataFrame()

    if not cash_df.empty:
        day_inc_df = cash_df[cash_df["Tariqh"] == sel_date_str]
        day_inc = day_inc_df["Raqam (₹)"].sum()

    if not exp_df.empty:
        day_exp_df = exp_df[exp_df["Tariqh"] == sel_date_str]
        day_exp = day_exp_df["Raqam (₹)"].sum()

    if not asset_df.empty:
        day_asset_df = asset_df[asset_df["Tariqh"] == sel_date_str]

    day_net = day_inc - day_exp

    col_cd1, col_cd2, col_cd3 = st.columns(3)
    with col_cd1: st.metric("उस दिन की कमाई", f"₹{day_inc:,.0f}")
    with col_cd2: st.metric("उस दिन का ख़र्च", f"₹{day_exp:,.0f}")
    with col_cd3: st.metric("शुद्ध दैनिक बचत", f"₹{day_net:,.0f}", delta=f"{day_net:+,.0f}")

    st.divider()
    c_tab1, c_tab2, c_tab3 = st.tabs(["💵 कमाई एंट्रियां", "💸 ख़र्च एंट्रियां", "🥇 संपत्तियां/सोना"])
    with c_tab1:
        if not day_inc_df.empty: st.dataframe(day_inc_df.drop(columns=["id"]), use_container_width=True)
        else: st.info("इस तारीख को कोई कमाई दर्ज नहीं हुई थी।")
    with c_tab2:
        if not day_exp_df.empty: st.dataframe(day_exp_df.drop(columns=["id"]), use_container_width=True)
        else: st.info("इस तारीख को कोई ख़र्च दर्ज नहीं हुआ था।")
    with c_tab3:
        if not day_asset_df.empty: st.dataframe(day_asset_df.drop(columns=["id"]), use_container_width=True)
        else: st.info("इस तारीख को कोई नई संपत्ति नहीं जोड़ी गई थी।")

# ----------------- TAB: PASSIVE FIRE FREEDOM ENGINE -----------------
with tab_fire:
    st.subheader("🌴 पैसिव कैशफ़्लो व वित्तीय आज़ादी इंजन")
    withdrawal_rate = 4.0
    annual_passive = total_networth * (withdrawal_rate / 100)
    monthly_passive = annual_passive / 12
    daily_passive = annual_passive / 365
    st.metric("वर्तमान शुद्ध पैसिव इनकम", f"₹{monthly_passive:,.0f} / महीना")
    st.caption(f"रोज़ाना बिना काम किए: **₹{daily_passive:,.0f} / दिन**")

    st.divider()
    t_annual_passive = TARGET * (withdrawal_rate / 100)
    t_monthly_passive = t_annual_passive / 12
    t_daily_passive = t_annual_passive / 365
    col_tw1, col_tw2, col_tw3 = st.columns(3)
    with col_tw1: st.metric("सालाना पैसिव कैश", f"₹{t_annual_passive/10000000:.1f} करोड़/वर्ष")
    with col_tw2: st.metric("मासिक पैसिव सैलरी", f"₹{t_monthly_passive/100000:.1f} लाख/माह")
    with col_tw3: st.metric("प्रतिदिन पैसिव आवक", f"₹{t_daily_passive:,.0f}/दिन")

# ----------------- TAB: TAX & CLEAN IN-HAND -----------------
with tab_tax:
    st.subheader("⚖️ स्मार्ट टैक्स बफ़र व असली इन-हैंड वेल्थ")
    tax_bracket = 15
    tax_reserve = total_gross_income * (tax_bracket / 100)
    clean_in_hand_cash = max(total_net_cash - tax_reserve, 0.0)
    clean_networth = max(clean_in_hand_cash + total_assets + total_receivables - total_liabilities, 0.0)

    col_res1, col_res2 = st.columns(2)
    with col_res1: st.metric("कुल ग्रॉस नेटवर्थ", f"₹{total_networth:,.0f}")
    with col_res2: st.metric("टैक्स-कटी इन-हैंड नेटवर्थ 🛡️", f"₹{clean_networth:,.0f}")

# ----------------- TAB: UPI ROUND-UP -----------------
with tab_roundup:
    st.subheader("🪙 UPI स्पेयर-चेंज राउंड-अप और ₹10 डेली गोल्ड SIP")
    col_ru1, col_ru2 = st.columns(2)
    with col_ru1:
        spend_amt = st.number_input("आज आपने कितने का UPI ख़र्च किया (₹)?", min_value=1.0, value=73.0, step=5.0)
        round_to = 50
        rounded_val = math.ceil(spend_amt / round_to) * round_to
        spare_change = rounded_val - spend_amt if rounded_val > spend_amt else round_to
        st.info(f"💡 ख़र्च: ₹{spend_amt:.0f} ➔ राउंड-अप: ₹{rounded_val:.0f} ➔ **बची चिल्लर: ₹{spare_change:.0f}**")
        
        if st.button("🟡 यह चिल्लर सीधे 24K गोल्ड में जोड़ें!", key="btn_roundup_save"):
            gold_price_gram = 7650.0
            grams_bought = spare_change / gold_price_gram
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, today_str, "Gold (24K Round-up)", grams_bought, spare_change, f"UPI Round-up on ₹{spend_amt} spend"))
            conn.commit()
            st.balloons()
            st.success(f"शानदार! ₹{spare_change:.0f} का सोना ({grams_bought:.4f} ग्राम) जुड़ गया!")
            st.rerun()

    with col_ru2:
        st.markdown("#### ⚡ 1-क्लिक डेली गोल्ड SIP")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🟡 ₹10 सोना खरीदें", key="btn_sip_10"):
                g_bought = 10.0 / 7650.0
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                               (ACTIVE_USER, today_str, "Gold (24K Daily SIP)", g_bought, 10.0, "Daily ₹10 Micro SIP"))
                conn.commit()
                st.success("₹10 का सोना जुड़ गया!")
                st.rerun()
        with col_btn2:
            if st.button("🟡 ₹50 सोना खरीदें", key="btn_sip_50"):
                g_bought = 50.0 / 7650.0
                cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                               (ACTIVE_USER, today_str, "Gold (24K Daily SIP)", g_bought, 50.0, "Daily ₹50 Micro SIP"))
                conn.commit()
                st.success("₹50 का सोना जुड़ गया!")
                st.rerun()

# ----------------- TAB: AI MENTOR -----------------
with tab_ai:
    st.subheader("🧠 AI वेल्थ मेंटॉर")
    if total_networth == 0:
        st.info("💡 खाते में कमाई दर्ज करके शुरुआत करें।")
    else:
        cash_ratio = (total_net_cash / total_networth) * 100 if total_networth > 0 else 0
        if cash_ratio > 70:
            st.warning(f"⚠️ {cash_ratio:.1f}% पूँजी नकद में है। इसे सोने या ठोस एसेट्स में बदलें!")
        else:
            st.success("🎯 पोर्टफोलियो संतुलित और सुरक्षित है।")

# ----------------- TAB: LUXURY SIMULATOR -----------------
with tab_wishlist:
    st.subheader("🏎️ लग्ज़री विशलिस्ट सिमुलेटर")
    luxury_items = [
        {"icon": "⌚", "name": "Rolex Watch", "cost": 1500000},
        {"icon": "🏎️", "name": "Sports Car (BMW/Merc)", "cost": 8500000},
        {"icon": "👑", "name": "Rolls-Royce Phantom", "cost": 95000000},
        {"icon": "🏰", "name": "Penthouse / Mansion", "cost": 250000000},
        {"icon": "✈️", "name": "Private Jet", "cost": 450000000}
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
    st.subheader("🎮 100 करोड़ एलीट गेम ज़ोन")
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
        st.subheader("📝 नई कमाई दर्ज करें")
        col_a, col_b = st.columns(2)
        with col_a: entry_date = st.date_input("तारीख", value=date.today(), key="cash_date")
        with col_b: daily_income = st.number_input("रकम (₹ में)", min_value=0.0, step=500.0)
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("स्रोत", [
                "Business", "Daily Savings", "Trading/Investment", "Side Hustle", "Other"
            ])
        with col_cat2: custom_note = st.text_input("नोट", value="")
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 कमाई सेव करें")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                           (ACTIVE_USER, str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} जुड़ गए!")
            st.rerun()

    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ कमाई एंट्री हटाएँ"):
            del_id = st.selectbox("एंट्री चुनें:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'Raqam (₹)'].values[0]:,.0f}",
                                  key="sel_del_income")
            if st.button("❌ मिटाएँ", key="btn_del_income"):
                cursor.execute("DELETE FROM income_history WHERE id = ? AND user_phone = ?", (del_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: EXPENSES -----------------
with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("💸 ख़र्च दर्ज करें")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            exp_date = st.date_input("तारीख", value=date.today(), key="exp_date")
            exp_cat = st.selectbox("श्रेणी", ["Essentials", "Travel/Fuel", "Food/Groceries", "Business", "Other"])
        with col_e2:
            exp_amt = st.number_input("रकम (₹ में)", min_value=0.0, step=100.0)
            exp_note = st.text_input("विवरण", value="")
        submit_exp = st.form_submit_button("💾 ख़र्च सेव करें")

        if submit_exp and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} दर्ज हुए!")
            st.rerun()

    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ ख़र्च हटाएँ"):
            del_exp_id = st.selectbox("ख़र्च चुनें:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'Raqam (₹)'].values[0]:,.0f}",
                                      key="sel_del_exp")
            if st.button("❌ मिटाएँ", key="btn_del_exp"):
                cursor.execute("DELETE FROM expense_history WHERE id = ? AND user_phone = ?", (del_exp_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: DEBT / LOAN -----------------
with tab_debt:
    st.subheader("⚖️ कर्ज़ व उधारी ट्रैकर")
    with st.form("debt_form", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_date = st.date_input("तारीख", value=date.today(), key="debt_date")
            debt_type = st.radio("प्रकार", ["मेरा कर्ज़ (लायबिलिटी - देना है)", "मेरा पैसा बाहर (एसेट - लेना है)"])
        with col_d2:
            d_person = st.text_input("व्यक्ति / बैंक का नाम", value="")
            d_amount = st.number_input("रकम (₹ में)", min_value=0.0, step=500.0)
        d_note = st.text_input("कारण / तारीख", value="")
        submit_debt = st.form_submit_button("💾 कर्ज़ रिकॉर्ड सेव करें")

        if submit_debt and d_amount > 0:
            cursor.execute("INSERT INTO debt_history (user_phone, entry_date, debt_type, person_name, amount, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(d_date), debt_type, d_person, d_amount, d_note))
            conn.commit()
            st.success("रिकॉर्ड सेव हो गया!")
            st.rerun()

    if not debt_df.empty:
        st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ कर्ज़ हटाएँ"):
            del_debt_id = st.selectbox("रिकॉर्ड चुनें:", options=debt_df["id"].tolist(),
                                       format_func=lambda x: f"ID {x} - ₹{debt_df.loc[debt_df['id']==x, 'Raqam (₹)'].values[0]:,.0f}",
                                       key="sel_del_debt")
            if st.button("❌ मिटाएँ", key="btn_del_debt"):
                cursor.execute("DELETE FROM debt_history WHERE id = ? AND user_phone = ?", (del_debt_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 गोल्ड व वास्तविक संपत्तियां")
    col_gr1, col_gr2, col_gr3 = st.columns(3)
    with col_gr1: st.info("🟡 24K Gold: **₹7,650 / g**")
    with col_gr2: st.info("🟠 22K Gold: **₹7,050 / g**")
    with col_gr3: st.info("⚪ Silver: **₹92 / g**")

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: asset_date = st.date_input("तारीख", value=date.today(), key="asset_date")
        with col2: gold_purity = st.selectbox("प्रकार", ["24K (99.9% Pure)", "22K (Jewellery)", "Silver", "Plot / Land", "Property", "Other"])
        
        c_g1, c_g2 = st.columns(2)
        with c_g1: grams = st.number_input("मात्रा (Grams/Units):", min_value=0.1, value=10.0, step=0.5)
        with c_g2: rate_per_gram = st.number_input("भाव प्रति ग्राम / कुल मूल्यांकन (₹):", min_value=50.0, value=7650.0, step=50.0)
        calc_val = grams * rate_per_gram if "Gold" in gold_purity or "Silver" in gold_purity else rate_per_gram
        asset_note = st.text_input("विवरण:", value="Physical Asset")

        submit_asset = st.form_submit_button("💾 एसेट सेव करें")
        if submit_asset and calc_val > 0:
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(asset_date), gold_purity, grams, calc_val, asset_note))
            conn.commit()
            st.success("एसेट जुड़ गया!")
            st.rerun()

    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ एसेट हटाएँ"):
            del_asset_id = st.selectbox("एसेट चुनें:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'Type'].values[0]}",
                                        key="sel_del_asset")
            if st.button("❌ मिटाएँ", key="btn_del_asset"):
                cursor.execute("DELETE FROM assets_history WHERE id = ? AND user_phone = ?", (del_asset_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: HEALTH SCORE -----------------
with tab_health:
    st.subheader("🩺 फाइनेंशियल हेल्थ ऑडिट")
    score = 75 if total_networth > 0 else 25
    st.metric("वेल्थ स्कोर", f"{score} / 100")
    st.progress(score / 100)

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 बचत दर विश्लेषण")
    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1: st.metric("कुल कमाई", f"₹{total_gross_income:,.0f}")
    with col_an2: st.metric("कुल ख़र्च", f"₹{total_expenses:,.0f}")
    with col_an3: st.metric("बचत दर", f"{savings_rate:.1f}%")

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("नकद बचत", f"₹{total_net_cash:,.0f}")
    with col_m2: st.metric("गोल्ड व एसेट्स", f"₹{total_assets:,.0f}")
    with col_m3: st.metric("कर्ज़ (देना है)", f"₹{total_liabilities:,.0f}")
    with col_m4: st.metric("शुद्ध नेटवर्थ 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ लक्ष्य प्रोग्रेस: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 करोड़ के लक्ष्य में अभी ₹{TARGET - total_networth:,.0f} शेष हैं।")

    st.divider()
    st.subheader("📅 इस महीने का वित्तीय स्नैपशॉट")
    col_mo1, col_mo2, col_mo3 = st.columns(3)
    with col_mo1: st.metric("इस माह कमाई", f"₹{month_inc:,.0f}")
    with col_mo2: st.metric("इस माह ख़र्च", f"₹{month_exp:,.0f}")
    with col_mo3: st.metric("इस माह शुद्ध बचत", f"₹{month_net_savings:,.0f}")

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 माइलस्टोन लेडर")
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

# ----------------- TAB 5: DAILY DISCIPLINE (SYNCED) -----------------
with tab5:
    st.subheader("🔥 दैनिक अनुशासन व स्ट्राइक ट्रैकर")
    today_savings = 0.0
    if not cash_df.empty:
        today_rows = cash_df[cash_df["Tariqh"] == today_str]
        today_savings = today_rows["Raqam (₹)"].sum()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        current_target = st.number_input("दैनिक कमाई का लक्ष्य (₹):", min_value=100.0, value=float(st.session_state["custom_daily_target"]), step=500.0)
    with col_d2:
        st.metric("आज की कमाई", f"₹{today_savings:,.0f}")

    daily_prog = min(today_savings / current_target, 1.0) if current_target > 0 else 0.0
    st.write(f"### आज का अनुशासन प्रोग्रेस: `{daily_prog * 100:.1f}%`")
    st.progress(daily_prog)
    if daily_prog >= 1.0:
        st.balloons()
        st.success("🔥 शानदार! आज का दैनिक लक्ष्य पूरा हुआ!")
