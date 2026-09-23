import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import io
import requests
import math
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- पेज कॉन्फ़िगरेशन ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- डेटाबेस सेटअप व ऑटो-माइग्रेशन ---
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

# --- सेशन स्टेट ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None

# --- लॉगिन स्क्रीन ---
if not st.session_state["logged_user"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("हर व्यक्ति का अपना सुरक्षित, व्यक्तिगत वित्तीय खाता।")

    auth_tab1, auth_tab2 = st.tabs(["🔑 मौजूदा यूज़र लॉगिन", "📝 नया खाता बनाएँ (Sign Up)"])

    with auth_tab1:
        st.subheader("अपने नंबर से प्रवेश करें")
        with st.form("login_form"):
            l_phone = st.text_input("मोबाइल नंबर (10 अंक):", max_chars=10, value="9983204295")
            l_pin = st.text_input("अपना 4-अंकों का गुप्त पिन दर्ज करें:", type="password", max_chars=4)
            submit_login = st.form_submit_button("लॉगिन करें 🔓", type="primary")

            if submit_login:
                if len(l_phone) != 10 or not l_phone.isdigit():
                    st.error("कृपया 10 अंकों का मान्य मोबाइल नंबर डालें!")
                else:
                    cursor.execute("SELECT pin FROM users WHERE phone = ?", (l_phone,))
                    user_data = cursor.fetchone()
                    if user_data:
                        if user_data[0] == l_pin:
                            st.session_state["logged_user"] = l_phone
                            st.success("सफलतापूर्वक लॉगिन हो गया!")
                            st.rerun()
                        else:
                            st.error("गलत पिन! कृपया सही पिन डालें।")
                    else:
                        st.error("यह नंबर पंजीकृत नहीं है! कृपया 'नया खाता बनाएँ' टैब से पिन सेट करें।")

    with auth_tab2:
        st.subheader("नया 100 Cr खाता रजिस्टर करें")
        with st.form("signup_form"):
            s_phone = st.text_input("अपना 10-अंकों का मोबाइल नंबर डालें:", max_chars=10, value="9983204295")
            s_pin = st.text_input("अपना नया 4-अंकों का पिन सेट करें:", type="password", max_chars=4)
            s_pin_confirm = st.text_input("पिन दोबारा दर्ज करें:", type="password", max_chars=4)
            submit_signup = st.form_submit_button("खाता बनाएँ व लॉगिन करें 🚀")

            if submit_signup:
                if len(s_phone) != 10 or not s_phone.isdigit():
                    st.error("कृपया 10 अंकों का मान्य मोबाइल नंबर दर्ज करें!")
                elif len(s_pin) != 4 or not s_pin.isdigit():
                    st.error("पिन ठीक 4 अंकों का होना चाहिए!")
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

# ==================== लॉगिन यूज़र इंटरफ़ेस ====================
ACTIVE_USER = st.session_state["logged_user"]

with st.sidebar:
    st.title("👤 यूज़र प्रोफ़ाइल")
    st.success(f"खाता: **{ACTIVE_USER}**")
    
    theme_choice = st.selectbox(
        "पसंदीदा थीम चुनें:",
        ["🌟 रॉयल गोल्ड डार्क", "☀️ क्लासिक ब्राइट लाइट", "🌌 डीप नेवी ब्लू", "🌿 लग्ज़री ग्रीन"]
    )
    
    st.divider()
    st.subheader("🔐 अपना पिन बदलें")
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

# थीम CSS
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
    </style>
""", unsafe_allow_html=True)

TARGET = 1000000000  # 100 करोड़

st.title("👑 100 Crore Wealth Hub")
st.caption(f"व्यक्तिगत खाता: **{ACTIVE_USER}** | टॉप 1% वेल्थ क्लब व 100 Cr का सफ़र")

# 16 टैब्स (नया वायरल टैब जोड़ा गया)
tab1, tab_elite, tab_cal, tab_fire, tab_roundup, tab_tax, tab_ai, tab_wishlist, tab_game, tab2, tab_exp, tab_debt, tab_health, tab_analytics, tab3, tab4 = st.tabs([
    "📊 डैशबोर्ड", 
    "👑 टॉप 1% एलीट क्लब",
    "📅 वित्तीय कैलेंडर",
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
    "🥇 गोल्ड व संपत्तियां", 
    "🚀 100 Cr रोडमैप"
])

# ----------------- सुरक्षित डेटा क्वेरी -----------------
try:
    cash_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', daily_amount as 'रकम (₹)', note as 'विवरण' FROM income_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    cash_df = pd.DataFrame(columns=["id", "तारीख", "रकम (₹)", "विवरण"])

try:
    exp_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', amount as 'रकम (₹)', category as 'श्रेणी', note as 'विवरण' FROM expense_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    exp_df = pd.DataFrame(columns=["id", "तारीख", "रकम (₹)", "श्रेणी", "विवरण"])

try:
    asset_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', asset_type as 'प्रकार', quantity as 'मात्रा', current_value as 'मूल्य (₹)', note as 'विवरण' FROM assets_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    asset_df = pd.DataFrame(columns=["id", "तारीख", "प्रकार", "मात्रा", "मूल्य (₹)", "विवरण"])

try:
    debt_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', debt_type as 'प्रकार', person_name as 'नाम', amount as 'रकम (₹)', note as 'विवरण' FROM debt_history WHERE user_phone = ? ORDER BY id DESC", conn, params=(ACTIVE_USER,))
except Exception:
    debt_df = pd.DataFrame(columns=["id", "तारीख", "प्रकार", "नाम", "रकम (₹)", "विवरण"])

total_gross_income = cash_df["रकम (₹)"].sum() if not cash_df.empty else 0.0
total_expenses = exp_df["रकम (₹)"].sum() if not exp_df.empty else 0.0
total_net_cash = max(total_gross_income - total_expenses, 0.0)
total_assets = asset_df["मूल्य (₹)"].sum() if not asset_df.empty else 0.0

total_liabilities = 0.0
total_receivables = 0.0
if not debt_df.empty:
    liab_rows = debt_df[debt_df["प्रकार"].str.contains("लायबिलिटी")]
    rec_rows = debt_df[debt_df["प्रकार"].str.contains("एसेट")]
    total_liabilities = liab_rows["रकम (₹)"].sum()
    total_receivables = rec_rows["रकम (₹)"].sum()

total_networth = max(total_net_cash + total_assets + total_receivables - total_liabilities, 0.0)
savings_rate = ((total_gross_income - total_expenses) / total_gross_income * 100) if total_gross_income > 0 else 0.0

today_str = str(date.today())
current_month_prefix = today_str[:7]

month_inc = 0.0
month_exp = 0.0
if not cash_df.empty:
    m_inc_rows = cash_df[cash_df["तारीख"].str.startswith(current_month_prefix)]
    month_inc = m_inc_rows["रकम (₹)"].sum()

if not exp_df.empty:
    m_exp_rows = exp_df[exp_df["तारीख"].str.startswith(current_month_prefix)]
    month_exp = m_exp_rows["रकम (₹)"].sum()

month_net_savings = max(month_inc - month_exp, 0.0)

unique_dates = sorted(cash_df["तारीख"].unique().tolist(), reverse=True) if not cash_df.empty else []
streak = 0
check_day = date.today()
if today_str not in unique_dates:
    check_day = date.today() - timedelta(days=1)
while str(check_day) in unique_dates:
    streak += 1
    check_day = check_day - timedelta(days=1)

# ----------------- TAB: ELITE 1% CLUB & TIME MACHINE (VIRAL & ATTRACTIVE) -----------------
with tab_elite:
    st.subheader("👑 द 1% एलीट वेल्थ क्लब व 2035 टाइम-मशीन")
    st.caption("जानिए आप भारत व दुनिया की आबादी में कहाँ खड़े हैं:")

    # पर्सेंटाइल गणना
    if total_networth >= 100000000:
        percentile = "टॉप 0.01% (अल्ट्रा-एलीट टाइटन)"
        next_bracket = "ग्लोबल फ़ोर्ब्स लिस्ट 🏆"
    elif total_networth >= 10000000:
        percentile = "टॉप 0.5% (करोड़पति क्लब)"
        next_bracket = "टॉप 0.1% (5 करोड़ क्लब)"
    elif total_networth >= 2500000:
        percentile = "टॉप 3% (संपन्न वेल्थ क्रिएटर)"
        next_bracket = "टॉप 1% (1 करोड़ क्लब)"
    elif total_networth >= 500000:
        percentile = "टॉप 10% (मज़बूत पूँजीपति)"
        next_bracket = "टॉप 5% (25 लाख क्लब)"
    elif total_networth >= 50000:
        percentile = "टॉप 30% (तेज़ी से आगे बढ़ता खिलाड़ी)"
        next_bracket = "टॉप 10% (5 लाख क्लब)"
    else:
        percentile = "आरम्भिक क्लब (Ground Zero Builder)"
        next_bracket = "टॉप 30% (50 हज़ार क्लब)"

    # VIP Flex Card
    st.markdown(f"""
    <div class="vip-card">
        <h4 style="color: #e5a93c !important; letter-spacing: 2px; margin: 0;">VERIFIED WEALTH STATUS</h4>
        <h1 style="color: #ffffff !important; font-size: 2.1rem; margin: 10px 0;">{percentile}</h1>
        <p style="color: #cbd5e0 !important; font-size: 1rem; margin-bottom: 0;">
            अकाउंट: <b>{ACTIVE_USER}</b> | शुद्ध नेटवर्थ: <b>₹{total_networth:,.0f}</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.success(f"🎯 **अगला पड़ाव:** {next_bracket} में प्रवेश करना!")

    # 2035 टाइम-मशीन (Future Predictor)
    st.divider()
    st.subheader("⏳ 2035 फ्यूचर टाइम-मशीन (Your Wealth in Future)")
    st.caption("यदि आप अपनी वर्तमान दैनिक आदत और बचत को जारी रखते हैं, तो आपका भविष्य कैसा होगा:")

    time_travel_yrs = st.slider("भविष्य में कितने साल आगे देखना है?", min_value=3, max_value=15, value=10, step=1)
    future_year = 2026 + time_travel_yrs
    
    # 15% कम्पाउंडिंग पर भविष्य की संपत्ति
    monthly_runrate = max(month_net_savings, 5000.0)
    r_mo = 0.15 / 12
    n_mo = time_travel_yrs * 12
    future_val = (total_networth * ((1 + 0.15)**time_travel_yrs)) + (monthly_runrate * (((1 + r_mo)**n_mo - 1) / r_mo))
    future_passive_mo = (future_val * 0.05) / 12

    col_tm1, col_tm2 = st.columns(2)
    with col_tm1:
        st.metric(f"वर्ष {future_year} में आपकी अनुमानित नेटवर्थ 🚀", f"₹{future_val:,.0f}")
    with col_tm2:
        st.metric(f"उस समय हर महीने बिना काम किए पैसिव सैलरी 🌴", f"₹{future_passive_mo:,.0f} / माह")

    st.info(f"✨ **टाइम-मशीन इनसाइट:** वर्ष {future_year} में आप रोज़ाना लगभग **₹{future_passive_mo/30:,.0f}** सिर्फ़ पैसिव आय से कमा रहे होंगे!")

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
        day_inc_df = cash_df[cash_df["तारीख"] == sel_date_str]
        day_inc = day_inc_df["रकम (₹)"].sum()

    if not exp_df.empty:
        day_exp_df = exp_df[exp_df["तारीख"] == sel_date_str]
        day_exp = day_exp_df["रकम (₹)"].sum()

    if not asset_df.empty:
        day_asset_df = asset_df[asset_df["तारीख"] == sel_date_str]

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
    col_fi1, col_fi2 = st.columns(2)
    with col_fi1:
        withdrawal_rate = st.slider("पैसिव विथड्रॉल दर (% वार्षिक):", min_value=3.0, max_value=8.0, value=4.0, step=0.5)
    with col_fi2:
        annual_passive = total_networth * (withdrawal_rate / 100)
        monthly_passive = annual_passive / 12
        daily_passive = annual_passive / 365
        st.metric("वर्तमान शुद्ध पैसिव इनकम", f"₹{monthly_passive:,.0f} / महीना")
        st.caption(f"रोज़ाना बिना काम किए: **₹{daily_passive:,.0f} / दिन**")

    st.divider()
    st.markdown("#### 👑 100 करोड़ पर आपकी पैसिव आज़ादी:")
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
    col_tx1, col_tx2 = st.columns(2)
    with col_tx1:
        tax_bracket = st.slider("अनुमानित टैक्स बफ़र रेट (%):", min_value=0, max_value=35, value=15, step=5)
    with col_tx2:
        tax_reserve = total_gross_income * (tax_bracket / 100)
        clean_in_hand_cash = max(total_net_cash - tax_reserve, 0.0)
        clean_networth = max(clean_in_hand_cash + total_assets + total_receivables - total_liabilities, 0.0)
        st.metric("टैक्स रिज़र्व फंड", f"₹{tax_reserve:,.0f}")

    col_res1, col_res2 = st.columns(2)
    with col_res1: st.metric("कुल ग्रॉस नेटवर्थ", f"₹{total_networth:,.0f}")
    with col_res2: st.metric("टैक्स-कटी इन-हैंड नेटवर्थ 🛡️", f"₹{clean_networth:,.0f}")

# ----------------- TAB: UPI ROUND-UP -----------------
with tab_roundup:
    st.subheader("🪙 UPI स्पेयर-चेंज राउंड-अप और ₹10 डेली गोल्ड SIP")
    col_ru1, col_ru2 = st.columns(2)
    with col_ru1:
        spend_amt = st.number_input("आज आपने कितने का UPI ख़र्च किया (₹)?", min_value=1.0, value=73.0, step=5.0)
        round_to = st.selectbox("राउंड-अप का नियम चुनें:", [10, 50, 100])
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
    st.subheader("🧠 AI वेल्थ मेंटॉर व स्ट्रेस-टेस्ट")
    if total_networth == 0:
        st.info("💡 **AI डायग्नोसिस:** अभी आपके खाते में कोई एंट्री दर्ज नहीं है। कमाई व बचत जोड़कर शुरुआत करें।")
    else:
        cash_ratio = (total_net_cash / total_networth) * 100 if total_networth > 0 else 0
        asset_ratio = (total_assets / total_networth) * 100 if total_networth > 0 else 0
        if cash_ratio > 70:
            st.warning(f"⚠️ **AI चेतावनी:** आपकी {cash_ratio:.1f}% पूँजी नकद में है। इसे सोने या एसेट्स में बदलें!")
        elif asset_ratio > 70:
            st.success(f"🎯 **AI इनसाइट:** आपका 70%+ पोर्टफोलियो वास्तविक एसेट्स में सुरक्षित है।")
        else:
            st.info("💡 **संतुलित रणनीति:** नकद और एसेट्स का संतुलन अच्छा है।")

# ----------------- TAB: LUXURY SIMULATOR -----------------
with tab_wishlist:
    st.subheader("🏎️ लग्ज़री शॉपिंग व विशलिस्ट सिमुलेटर")
    luxury_items = [
        {"icon": "⌚", "name": "रोलेक्स / लक्ज़री घड़ी", "cost": 1500000},
        {"icon": "🏎️", "name": "लक्ज़री स्पोर्ट्स कार", "cost": 8500000},
        {"icon": "👑", "name": "रोल्स-रॉयस फैंटम", "cost": 95000000},
        {"icon": "🏰", "name": "अल्ट्रा-लक्ज़री पेंटहाउस", "cost": 250000000},
        {"icon": "✈️", "name": "प्राइवेट जेट", "cost": 450000000},
        {"icon": "🏝️", "name": "प्राइवेट आइलैंड", "cost": 850000000}
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
        <h1 style="color: #ffffff !important; font-size: 2.2rem; margin: 10px 0;">{percentile}</h1>
        <p style="color: #a0aec0 !important; font-size: 1rem;">DISCIPLINE STREAK: <b>🔥 {streak} DAYS</b></p>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TAB 2: INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 नई नकद कमाई दर्ज करें")
        col_a, col_b = st.columns(2)
        with col_a: entry_date = st.date_input("तारीख", value=date.today(), key="cash_date")
        with col_b: daily_income = st.number_input("रकम (₹ में)", min_value=0.0, step=500.0)
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("आय का स्रोत", [
                "व्यापार / बिज़नेस (Business)", "दैनिक बचत (Daily Savings)", "ट्रेडिंग व निवेश (Trading)", "साइड वर्क (Side Hustle)", "अन्य स्रोत"
            ])
        with col_cat2: custom_note = st.text_input("अतिरिक्त नोट", value="")
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 कमाई सेव करें")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (user_phone, entry_date, daily_amount, note) VALUES (?, ?, ?, ?)",
                           (ACTIVE_USER, str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} आपके खाते में जुड़ गए!")
            st.rerun()

    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        csv_cash = cash_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 कमाई CSV डाउनलोड करें", data=csv_cash, file_name=f"income_{ACTIVE_USER}.csv", mime="text/csv", key="dl_income_csv")
        with st.expander("🗑️ कमाई एंट्री हटाएँ"):
            del_id = st.selectbox("एंट्री चुनें:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'रकम (₹)'].values[0]:,.0f}",
                                  key="sel_del_income")
            if st.button("❌ मिटाएँ", key="btn_del_income"):
                cursor.execute("DELETE FROM income_history WHERE id = ? AND user_phone = ?", (del_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: EXPENSES -----------------
with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("💸 दैनिक ख़र्च दर्ज करें")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            exp_date = st.date_input("तारीख", value=date.today(), key="exp_date")
            exp_cat = st.selectbox("श्रेणी", ["ज़रूरी ख़र्च", "सफ़र / पेट्रोल", "खाना / राशन", "बिज़नेस ख़र्च", "अन्य"])
        with col_e2:
            exp_amt = st.number_input("रकम (₹ में)", min_value=0.0, step=100.0)
            exp_note = st.text_input("विवरण", value="")
        submit_exp = st.form_submit_button("💾 ख़र्च दर्ज करें")

        if submit_exp and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (user_phone, entry_date, amount, category, note) VALUES (?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} ख़र्च दर्ज हुए!")
            st.rerun()

    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ ख़र्च हटाएँ"):
            del_exp_id = st.selectbox("ख़र्च चुनें:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'रकम (₹)'].values[0]:,.0f}",
                                      key="sel_del_exp")
            if st.button("❌ मिटाएँ", key="btn_del_exp"):
                cursor.execute("DELETE FROM expense_history WHERE id = ? AND user_phone = ?", (del_exp_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: DEBT / LOAN -----------------
with tab_debt:
    st.subheader("⚖️ कर्ज़ व उधारी ट्रैकर (Liabilities)")
    with st.form("debt_form", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_date = st.date_input("तारीख", value=date.today(), key="debt_date")
            debt_type = st.radio("प्रकार", ["मेरा कर्ज़ (मुझे देना है - लायबिलिटी)", "मेरा पैसा बाहर है (मुझे लेना है - एसेट)"])
        with col_d2:
            d_person = st.text_input("व्यक्ति / बैंक का नाम", value="")
            d_amount = st.number_input("रकम (₹ में)", min_value=0.0, step=500.0)
        d_note = st.text_input("कारण / अंतिम तारीख", value="")
        submit_debt = st.form_submit_button("💾 कर्ज़ रिकॉर्ड सेव करें")

        if submit_debt and d_amount > 0:
            cursor.execute("INSERT INTO debt_history (user_phone, entry_date, debt_type, person_name, amount, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(d_date), debt_type, d_person, d_amount, d_note))
            conn.commit()
            st.success("कर्ज़ रिकॉर्ड जुड़ गया!")
            st.rerun()

    if not debt_df.empty:
        st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ कर्ज़ हटाएँ"):
            del_debt_id = st.selectbox("रिकॉर्ड चुनें:", options=debt_df["id"].tolist(),
                                       format_func=lambda x: f"ID {x} - ₹{debt_df.loc[debt_df['id']==x, 'रकम (₹)'].values[0]:,.0f}",
                                       key="sel_del_debt")
            if st.button("❌ मिटाएँ", key="btn_del_debt"):
                cursor.execute("DELETE FROM debt_history WHERE id = ? AND user_phone = ?", (del_debt_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 गोल्ड व वास्तविक संपत्तियां")
    col_gr1, col_gr2, col_gr3 = st.columns(3)
    with col_gr1: st.info("🟡 24K गोल्ड: **₹7,650 / ग्राम**")
    with col_gr2: st.info("🟠 22K गोल्ड: **₹7,050 / ग्राम**")
    with col_gr3: st.info("⚪ शुद्ध चाँदी: **₹92 / ग्राम**")

    asset_mode = st.radio("जोड़ने का तरीक़ा:", ["गोल्ड कैलकुलेटर (ग्राम अनुसार)", "अन्य अचल संपत्ति"], horizontal=True)

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: asset_date = st.date_input("तारीख", value=date.today(), key="asset_date")
        
        if asset_mode == "गोल्ड कैलकुलेटर (ग्राम अनुसार)":
            with col2: gold_purity = st.selectbox("शुद्धता", ["24K (99.9% शुद्ध सोना)", "22K (गहने/ज्वेलरी)", "चाँदी (Silver)"])
            default_rate = 7650.0 if "24" in gold_purity else (7050.0 if "22" in gold_purity else 92.0)
            c_g1, c_g2 = st.columns(2)
            with c_g1: grams = st.number_input("मात्रा (ग्राम में):", min_value=0.1, value=10.0, step=0.5)
            with c_g2: rate_per_gram = st.number_input("भाव प्रति ग्राम (₹):", min_value=50.0, value=default_rate, step=50.0)
            calc_val = grams * rate_per_gram
            st.write(f"💡 कुल मूल्य: **₹{calc_val:,.0f}**")
            asset_type = f"Gold ({gold_purity})" if "2" in gold_purity else "Silver"
            final_val = calc_val
            final_qty = grams
            asset_note = st.text_input("नोट:", value=f"{grams}g @ ₹{rate_per_gram}/g")
        else:
            with col2: asset_type = st.selectbox("प्रकार", ["ज़मीन / प्लॉट", "मकान / दुकान", "शेयर / म्यूचुअल फंड", "अन्य संपत्ति"])
            c_m1, c_m2 = st.columns(2)
            with c_m1: final_val = st.number_input("कुल मौजूदा मूल्यांकन (₹):", min_value=1000.0, step=5000.0)
            with c_m2: final_qty = st.number_input("मात्रा / यूनिट्स:", min_value=1.0, value=1.0, step=1.0)
            asset_note = st.text_input("विवरण:", value="दीर्घकालिक संपत्ति")

        submit_asset = st.form_submit_button("💾 एसेट सेव करें")
        if submit_asset and final_val > 0:
            cursor.execute("INSERT INTO assets_history (user_phone, entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                           (ACTIVE_USER, str(asset_date), asset_type, final_qty, final_val, asset_note))
            conn.commit()
            st.success("एसेट जुड़ गया!")
            st.rerun()

    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ एसेट हटाएँ"):
            del_asset_id = st.selectbox("एसेट चुनें:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'प्रकार'].values[0]}",
                                        key="sel_del_asset")
            if st.button("❌ मिटाएँ", key="btn_del_asset"):
                cursor.execute("DELETE FROM assets_history WHERE id = ? AND user_phone = ?", (del_asset_id, ACTIVE_USER))
                conn.commit()
                st.rerun()

# ----------------- TAB: HEALTH SCORE -----------------
with tab_health:
    st.subheader("🩺 फाइनेंशियल हेल्थ ऑडिट")
    score = 0
    if savings_rate >= 60: score += 35
    elif savings_rate >= 40: score += 25
    elif savings_rate > 0: score += 15

    if total_liabilities == 0 and total_networth > 0: score += 30
    elif total_liabilities < (total_networth * 0.2): score += 20
    else: score += 5

    if total_assets > 0 and total_net_cash > 0: score += 20
    elif total_assets > 0 or total_net_cash > 0: score += 10

    if len(cash_df) >= 5: score += 15
    elif len(cash_df) > 0: score += 8

    col_sc1, col_sc2 = st.columns([1, 2])
    with col_sc1: st.metric("वेल्थ स्कोर", f"{score} / 100")
    with col_sc2: st.progress(score / 100)

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 बचत दर विश्लेषण")
    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1: st.metric("कुल कमाई", f"₹{total_gross_income:,.0f}")
    with col_an2: st.metric("कुल ख़र्च", f"₹{total_expenses:,.0f}")
    with col_an3: st.metric("बचत दर", f"{savings_rate:.1f}%")
    comp_df = pd.DataFrame({"रकम (₹)": [total_gross_income, total_expenses, max(total_gross_income - total_expenses, 0.0)]}, index=["कमाई", "ख़र्च", "शुद्ध बचत"])
    st.bar_chart(comp_df)

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("शुद्ध नकद बचत", f"₹{total_net_cash:,.0f}")
    with col_m2: st.metric("गोल्ड व एसेट्स", f"₹{total_assets:,.0f}")
    with col_m3: st.metric("कर्ज़ (देना है)", f"₹{total_liabilities:,.0f}")
    with col_m4: st.metric("शुद्ध नेटवर्थ 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ लक्ष्य प्रोग्रेस: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 करोड़ के लक्ष्य में अभी ₹{TARGET - total_networth:,.0f} शेष हैं।")

    st.divider()
    st.subheader("📅 इस महीने का वित्तीय स्नैपशॉट (Current Month)")
    col_mo1, col_mo2, col_mo3 = st.columns(3)
    with col_mo1: st.metric("इस माह की कमाई", f"₹{month_inc:,.0f}")
    with col_mo2: st.metric("इस माह का ख़र्च", f"₹{month_exp:,.0f}")
    with col_mo3: st.metric("इस माह की शुद्ध बचत", f"₹{month_net_savings:,.0f}")

    st.divider()
    def generate_wealth_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("100 CRORE TARGET - OFFICIAL WEALTH AUDIT", styles['Heading1']))
        elements.append(Paragraph(f"Account: {ACTIVE_USER} | Date: {date.today().strftime('%d %B %Y')}", styles['Normal']))
        elements.append(Spacer(1, 15))
        summary_data = [
            ["Financial Metric", "Amount (INR)", "Status"],
            ["Total Networth", f"Rs. {total_networth:,.0f}", f"{(total_networth/TARGET)*100:.6f}%"],
            ["Net Liquid Cash", f"Rs. {total_net_cash:,.0f}", "In Hand"],
            ["Total Assets & Gold", f"Rs. {total_assets:,.0f}", "Valuation"],
            ["Total Liabilities", f"Rs. {total_liabilities:,.0f}", "Debt"]
        ]
        t = Table(summary_data, colWidths=[200, 170, 170])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ('FONTSIZE', (0, 0), (-1, -1), 10)
        ]))
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    st.download_button(
        label="📥 आधिकारिक वेल्थ ऑडिट PDF डाउनलोड करें",
        data=generate_wealth_pdf(),
        file_name=f"Wealth_Report_{ACTIVE_USER}_{date.today()}.pdf",
        mime="application/pdf",
        key="dl_wealth_pdf_btn"
    )

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 माइलस्टोन लेडर")
    milestones = [
        ("पहला पड़ाव: 10 लाख", 1000000),
        ("दूसरा पड़ाव: 50 लाख", 5000000),
        ("तीसरा पड़ाव: 1 करोड़", 10000000),
        ("चौथा पड़ाव: 5 करोड़", 50000000),
        ("पाँचवाँ पड़ाव: 10 करोड़", 100000000),
        ("छठा पड़ाव: 50 करोड़", 500000000),
        ("अंतिम लक्ष्य: 100 करोड़ 👑", 1000000000),
    ]
    for name, target_amt in milestones:
        if total_networth >= target_amt:
            st.success(f"✅ **{name}** — पूर्ण! (₹{target_amt:,.0f})")
        else:
            diff = target_amt - total_networth
            pct = min((total_networth / target_amt) * 100, 100.0)
            st.warning(f"⏳ **{name}** — `{pct:.2f}%` पूरा (अभी ₹{diff:,.0f} बाकी)")
