import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import io
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- पेज कॉन्फ़िगरेशन ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- सुरक्षा पिन ---
SECRET_PIN = "1234"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("सुरक्षित वित्तीय ऐप में प्रवेश के लिए पिन दर्ज करें।")
    pin_input = st.text_input("4-अंकों का गुप्त पिन डालें:", type="password")
    if st.button("लॉगिन करें 🔓", type="primary"):
        if pin_input == SECRET_PIN:
            st.session_state["authenticated"] = True
            st.success("सफलतापूर्वक अनलॉक हुआ!")
            st.rerun()
        else:
            st.error("गलत पिन! सही पिन दर्ज करें।")
    st.stop()

# --- साइडबार थीम सेलेक्टर ---
with st.sidebar:
    st.title("🎨 थीम व सेटिंग्स")
    theme_choice = st.selectbox(
        "अपनी पसंद का रंग चुनें:",
        ["🌟 रॉयल गोल्ड डार्क", "☀️ क्लासिक ब्राइट लाइट", "🌌 डीप नेवी ब्लू", "🌿 लग्ज़री ग्रीन"]
    )
    if st.button("लॉगआउट 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

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
else:  # रॉयल गोल्ड डार्क
    bg_color = "#111318"
    text_color = "#ffffff"
    accent = "#f59e0b"
    tab_bg = "#1f2430"
    btn_bg = "#f59e0b"
    btn_text = "#111827"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    label, p, h1, h2, h3, span, div {{
        color: {text_color} !important;
    }}
    div[data-testid="stMetricValue"] {{
        color: {accent} !important;
        font-weight: 800 !important;
        font-size: 1.85rem;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {text_color} !important;
        font-weight: 600 !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {tab_bg} !important;
        border-radius: 8px;
        color: {text_color} !important;
        padding: 6px 12px;
        font-size: 0.9rem;
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom: 3px solid {accent} !important;
        font-weight: 700 !important;
    }}
    .stDownloadButton button {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 22px !important;
        border-radius: 8px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- डेटाबेस सेटअप ---
conn = sqlite3.connect("wealth_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS income_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        daily_amount REAL,
        note TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        amount REAL,
        category TEXT,
        note TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        entry_date TEXT,
        debt_type TEXT,
        person_name TEXT,
        amount REAL,
        note TEXT
    )
""")
conn.commit()

TARGET = 1000000000  # 100 करोड़

st.title("👑 100 Crore Wealth Hub")
st.caption("लाइव गोल्ड वैल्यूएशन, वित्तीय स्कोर, संपत्तियां व 100 करोड़ रोडमैप")

# टैब्स
tab1, tab2, tab_exp, tab_debt, tab_health, tab_analytics, tab3, tab4, tab_blueprint, tab5 = st.tabs([
    "📊 डैशबोर्ड", 
    "💵 कमाई", 
    "💸 ख़र्च",
    "⚖️ कर्ज़ / उधारी",
    "🩺 वेल्थ स्कोर",
    "📈 बचत दर", 
    "🥇 गोल्ड व संपत्तियां", 
    "🚀 100 Cr रोडमैप",
    "⚡ ब्लूप्रिंट",
    "🔥 स्ट्राइक"
])

# ----------------- TAB 2: INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 नई नकद कमाई दर्ज करें")
        col_a, col_b = st.columns(2)
        with col_a:
            entry_date = st.date_input("तारीख", value=date.today(), key="cash_date")
        with col_b:
            daily_income = st.number_input("रकम (₹ में)", min_value=0.0, step=500.0)
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("आय का स्रोत", [
                "व्यापार / बिज़नेस (Business)", "दैनिक बचत (Daily Savings)", "ट्रेडिंग व निवेश (Trading)", "साइड वर्क (Side Hustle)", "अन्य स्रोत"
            ])
        with col_cat2:
            custom_note = st.text_input("अतिरिक्त नोट", value="")
        
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 कमाई सेव करें")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
                           (str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} जुड़ गए!")
            st.rerun()

    cash_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', daily_amount as 'रकम (₹)', note as 'विवरण' FROM income_history ORDER BY id DESC", conn)
    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        csv_cash = cash_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 कमाई CSV डाउनलोड करें", data=csv_cash, file_name="income_records.csv", mime="text/csv")
        with st.expander("🗑️ कमाई एंट्री हटाएँ"):
            del_id = st.selectbox("एंट्री चुनें:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'रकम (₹)'].values[0]:,.0f}")
            if st.button("❌ कमाई मिटाएँ"):
                cursor.execute("DELETE FROM income_history WHERE id = ?", (del_id,))
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
            cursor.execute("INSERT INTO expense_history (entry_date, amount, category, note) VALUES (?, ?, ?, ?)",
                           (str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} ख़र्च दर्ज हुए!")
            st.rerun()

    exp_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', amount as 'रकम (₹)', category as 'श्रेणी', note as 'विवरण' FROM expense_history ORDER BY id DESC", conn)
    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ ख़र्च एंट्री हटाएँ"):
            del_exp_id = st.selectbox("ख़र्च चुनें:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'रकम (₹)'].values[0]:,.0f}")
            if st.button("❌ ख़र्च मिटाएँ"):
                cursor.execute("DELETE FROM expense_history WHERE id = ?", (del_exp_id,))
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
            cursor.execute("INSERT INTO debt_history (entry_date, debt_type, person_name, amount, note) VALUES (?, ?, ?, ?, ?)",
                           (str(d_date), debt_type, d_person, d_amount, d_note))
            conn.commit()
            st.success("कर्ज़ रिकॉर्ड जुड़ गया!")
            st.rerun()

    debt_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', debt_type as 'प्रकार', person_name as 'नाम', amount as 'रकम (₹)', note as 'विवरण' FROM debt_history ORDER BY id DESC", conn)
    if not debt_df.empty:
        st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ कर्ज़ एंट्री हटाएँ"):
            del_debt_id = st.selectbox("रिकॉर्ड चुनें:", options=debt_df["id"].tolist(),
                                       format_func=lambda x: f"ID {x} - ₹{debt_df.loc[debt_df['id']==x, 'रकम (₹)'].values[0]:,.0f}")
            if st.button("❌ कर्ज़ मिटाएँ"):
                cursor.execute("DELETE FROM debt_history WHERE id = ?", (del_debt_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 गोल्ड व वास्तविक संपत्तियां")
    
    st.markdown("#### ⚡ लाइव मार्केट गोल्ड रेट्स")
    col_gr1, col_gr2, col_gr3 = st.columns(3)
    with col_gr1:
        st.info("🟡 24K गोल्ड: **₹7,650 / ग्राम**")
    with col_gr2:
        st.info("🟠 22K गोल्ड: **₹7,050 / ग्राम**")
    with col_gr3:
        st.info("⚪ शुद्ध चाँदी: **₹92 / ग्राम**")

    asset_mode = st.radio("जोड़ने का तरीक़ा:", ["गोल्ड कैलकुलेटर (ग्राम अनुसार)", "अन्य अचल संपत्ति"], horizontal=True)

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("तारीख", value=date.today(), key="asset_date")
        
        if asset_mode == "गोल्ड कैलकुलेटर (ग्राम अनुसार)":
            with col2:
                gold_purity = st.selectbox("शुद्धता", ["24K (99.9% शुद्ध सोना)", "22K (गहने/ज्वेलरी)", "चाँदी (Silver)"])
            
            default_rate = 7650.0 if "24" in gold_purity else (7050.0 if "22" in gold_purity else 92.0)
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                grams = st.number_input("मात्रा (ग्राम में):", min_value=0.1, value=10.0, step=0.5)
            with c_g2:
                rate_per_gram = st.number_input("भाव प्रति ग्राम (₹):", min_value=50.0, value=default_rate, step=50.0)
            
            calc_val = grams * rate_per_gram
            st.write(f"💡 कुल मूल्य: **₹{calc_val:,.0f}**")
            asset_type = f"Gold ({gold_purity})" if "2" in gold_purity else "Silver"
            final_val = calc_val
            final_qty = grams
            asset_note = st.text_input("नोट:", value=f"{grams}g @ ₹{rate_per_gram}/g")
        else:
            with col2:
                asset_type = st.selectbox("प्रकार", ["ज़मीन / प्लॉट", "मकान / दुकान", "शेयर / म्यूचुअल फंड", "अन्य संपत्ति"])
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                final_val = st.number_input("कुल मौजूदा मूल्यांकन (₹):", min_value=1000.0, step=5000.0)
            with c_m2:
                final_qty = st.number_input("मात्रा / यूनिट्स:", min_value=1.0, value=1.0, step=1.0)
            asset_note = st.text_input("विवरण:", value="दीर्घकालिक संपत्ति")

        submit_asset = st.form_submit_button("💾 एसेट सेव करें")
        if submit_asset and final_val > 0:
            cursor.execute("INSERT INTO assets_history (entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?)",
                           (str(asset_date), asset_type, final_qty, final_val, asset_note))
            conn.commit()
            st.success("एसेट जुड़ गया!")
            st.rerun()

    asset_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', asset_type as 'प्रकार', quantity as 'मात्रा', current_value as 'मूल्य (₹)', note as 'विवरण' FROM assets_history ORDER BY id DESC", conn)
    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ एसेट एंट्री हटाएँ"):
            del_asset_id = st.selectbox("एसेट चुनें:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'प्रकार'].values[0]} (₹{asset_df.loc[asset_df['id']==x, 'मूल्य (₹)'].values[0]:,.0f})")
            if st.button("❌ एसेट मिटाएँ"):
                cursor.execute("DELETE FROM assets_history WHERE id = ?", (del_asset_id,))
                conn.commit()
                st.rerun()

# मुख्य वित्तीय गणनाएँ
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

# ----------------- TAB: HEALTH SCORE -----------------
with tab_health:
    st.subheader("🩺 फाइनेंशियल हेल्थ स्कोर (Financial Health Audit)")
    
    # स्कोर गणना
    score = 0
    # 1. बचत दर स्कोर (अधिकतम 35)
    if savings_rate >= 60:
        score += 35
    elif savings_rate >= 40:
        score += 25
    elif savings_rate > 0:
        score += 15

    # 2. कर्ज़ नियंत्रण (अधिकतम 30)
    if total_liabilities == 0 and total_networth > 0:
        score += 30
    elif total_liabilities < (total_networth * 0.2):
        score += 20
    else:
        score += 5

    # 3. एसेट विविधता (अधिकतम 20)
    if total_assets > 0 and total_net_cash > 0:
        score += 20
    elif total_assets > 0 or total_net_cash > 0:
        score += 10

    # 4. डेटा निरंतरता (अधिकतम 15)
    if len(cash_df) >= 5:
        score += 15
    elif len(cash_df) > 0:
        score += 8

    col_sc1, col_sc2 = st.columns([1, 2])
    with col_sc1:
        st.metric("वेल्थ स्कोर", f"{score} / 100")
    with col_sc2:
        st.progress(score / 100)
        if score >= 80:
            st.success("🌟 एलीट स्टेटस: आपकी वित्तीय रणनीति 100 करोड़ के लक्ष्य के बिल्कुल सटीक रास्ते पर है!")
        elif score >= 50:
            st.warning("⚡ अच्छा स्तर: बचत दर और एसेट एलोकेशन को थोड़ा और आक्रामक बनाने की आवश्यकता है।")
        else:
            st.error("⚠️ सुधार की आवश्यकता: खर्चों को कम करें और नियमित बचत अनुशासन बनाएँ।")

    st.divider()
    st.markdown("#### 💡 स्मार्ट वेल्थ एडवाइजर सुझाव:")
    if savings_rate < 50:
        st.write("• **बचत दर बढ़ाएँ:** अपनी आय का कम से कम 50% बचाने का प्रयास करें।")
    if total_liabilities > 0:
        st.write("• **कर्ज़ मुक्ति:** सबसे पहले उच्च ब्याज वाले कर्ज़ को समाप्त करें।")
    if total_assets == 0:
        st.write("• **गोल्ड में एलोकेशन:** नकदी को सुरक्षित रखने के लिए नियमित रूप से 24K गोल्ड में बदलें।")
    if total_assets > 0 and savings_rate >= 50 and total_liabilities == 0:
        st.write("• **स्पीड अप:** अब नए बिज़नेस और हाई-कैशफ़्लो प्रोजेक्ट्स पर पूरा ध्यान केंद्रित करें!")

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 बचत दर विश्लेषण (Savings Rate)")
    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1:
        st.metric("कुल कमाई", f"₹{total_gross_income:,.0f}")
    with col_an2:
        st.metric("कुल ख़र्च", f"₹{total_expenses:,.0f}")
    with col_an3:
        st.metric("बचत दर", f"{savings_rate:.1f}%")

    comp_df = pd.DataFrame({
        "रकम (₹)": [total_gross_income, total_expenses, max(total_gross_income - total_expenses, 0.0)]
    }, index=["कमाई", "ख़र्च", "शुद्ध बचत"])
    st.bar_chart(comp_df)

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("शुद्ध नकद बचत", f"₹{total_net_cash:,.0f}")
    with col_m2:
        st.metric("गोल्ड व एसेट्स", f"₹{total_assets:,.0f}")
    with col_m3:
        st.metric("कर्ज़ (देना है)", f"₹{total_liabilities:,.0f}")
    with col_m4:
        st.metric("शुद्ध नेटवर्थ 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ लक्ष्य प्रोग्रेस: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 करोड़ के लक्ष्य में अभी ₹{TARGET - total_networth:,.0f} शेष हैं।")

    if total_networth > 0:
        st.write("### 🍰 संपत्ति का बँटवारा")
        chart_summary = pd.DataFrame({"राशि (₹)": [total_net_cash, total_assets, total_receivables]}, 
                                     index=["शुद्ध नकद", "गोल्ड व एसेट्स", "लेना बाकी उधारी"])
        st.bar_chart(chart_summary)

    # स्पीड मीटर
    st.divider()
    st.subheader("⚡ 100 करोड़ स्पीड मीटर")
    daily_avg = cash_df["रकम (₹)"].mean() if not cash_df.empty else 0.0
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.write(f"**औसत दैनिक कमाई:** ₹{daily_avg:,.0f}/दिन")
        if daily_avg > 0:
            years_needed = ((TARGET - total_networth) / daily_avg) / 365
            st.write(f"वर्तमान गति से समय लगेगा: **{years_needed:.1f} वर्ष**")
        else:
            st.write("समय: --")
    with col_v2:
        target_years = st.selectbox("लक्ष्य समय (साल):", [10, 15, 20, 25, 30], index=1)
        req_month = (TARGET - total_networth) / (target_years * 12)
        st.write(f"**{target_years} साल में 100 करोड़ के लिए:**")
        st.write(f"मासिक शुद्ध बचत चाहिए: **₹{req_month:,.0f}/महीना**")

    # PDF डाउनलोड
    st.divider()
    def generate_wealth_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("100 CRORE TARGET - OFFICIAL WEALTH AUDIT", styles['Heading1']))
        elements.append(Paragraph(f"Date: {date.today().strftime('%d %B %Y')} | Confidential", styles['Normal']))
        elements.append(Spacer(1, 15))
        summary_data = [
            ["Financial Metric", "Amount (INR)", "Status"],
            ["Total Networth", f"Rs. {total_networth:,.0f}", f"{(total_networth/TARGET)*100:.6f}%"],
            ["Net Liquid Cash", f"Rs. {total_net_cash:,.0f}", "In Hand"],
            ["Total Assets & Gold", f"Rs. {total_assets:,.0f}", "Valuation"],
            ["Total Liabilities", f"Rs. {total_liabilities:,.0f}", "Debt"],
            ["Health Score", f"{score} / 100", "Audited"]
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
        label="📥 वेल्थ ऑडिट PDF रिपोर्ट डाउनलोड करें",
        data=generate_wealth_pdf(),
        file_name=f"Wealth_Report_{date.today()}.pdf",
        mime="application/pdf"
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

    st.divider()
    st.subheader("⚡ कम्पाउंडिंग सिमुलेटर")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        monthly_invest = st.number_input("मासिक निवेश (₹):", min_value=1000, value=25000, step=5000)
    with col_s2:
        annual_rate = st.slider("सालाना रिटर्न (%):", min_value=8.0, max_value=25.0, value=15.0, step=0.5)

    years_list = list(range(1, 31))
    future_values = []
    r = (annual_rate / 100) / 12
    for yr in years_list:
        n = yr * 12
        fv = monthly_invest * (((1 + r)**n - 1) / r) * (1 + r) + (total_networth * ((1 + annual_rate/100)**yr))
        future_values.append(round(fv))
    st.line_chart(pd.DataFrame({"अनुमानित नेटवर्थ (₹)": future_values}, index=[f"वर्ष {y}" for y in years_list]))

# ----------------- TAB: BLUEPRINT -----------------
with tab_blueprint:
    st.subheader("⚡ 100 करोड़ का रिवर्स गणित")
    blueprint_table = [
        {"उत्पाद/सर्विस": "₹1,000 की सर्विस / प्रॉडक्ट", "आवश्यक ग्राहक": "10,00,000 लोग", "कुल": "₹100 करोड़"},
        {"उत्पाद/सर्विस": "₹10,000 का टूल / कोर्स", "आवश्यक ग्राहक": "1,00,000 लोग", "कुल": "₹100 करोड़"},
        {"उत्पाद/सर्विस": "₹50,000 की एजेंसी डील", "आवश्यक ग्राहक": "20,000 लोग", "कुल": "₹100 करोड़"},
        {"उत्पाद/सर्विस": "₹1,00,000 का हाई-टिकट बिज़नेस", "आवश्यक ग्राहक": "10,000 लोग", "कुल": "₹100 करोड़"}
    ]
    st.dataframe(pd.DataFrame(blueprint_table), use_container_width=True)

# ----------------- TAB 5: DISCIPLINE -----------------
with tab5:
    st.subheader("🔥 दैनिक अनुशासन व स्ट्राइक")
    today_str = str(date.today())
    today_savings = 0.0
    if not cash_df.empty:
        today_rows = cash_df[cash_df["तारीख"] == today_str]
        today_savings = today_rows["रकम (₹)"].sum()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        daily_target = st.number_input("दैनिक लक्ष्य (₹):", min_value=500, value=2000, step=500)
    with col_d2:
        st.metric("आज की कमाई", f"₹{today_savings:,.0f}")

    daily_prog = min(today_savings / daily_target, 1.0)
    st.progress(daily_prog)
