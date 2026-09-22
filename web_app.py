import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- पेज कॉन्फ़िगरेशन ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- सुरक्षा पिन (Secret PIN) ---
SECRET_PIN = "1234"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("यह एक सुरक्षित वित्तीय ऐप है। जारी रखने के लिए पिन दर्ज करें।")
    pin_input = st.text_input("अपना 4-अंकों का गुप्त पिन डालें:", type="password")
    if st.button("लॉगिन करें 🔓", type="primary"):
        if pin_input == SECRET_PIN:
            st.session_state["authenticated"] = True
            st.success("सफलतापूर्वक अनलॉक हुआ!")
            st.rerun()
        else:
            st.error("गलत पिन! कृपया सही पिन दर्ज करें।")
    st.stop()

# --- थीम सेलेक्टर (Sidebar Theme Customizer) ---
with st.sidebar:
    st.title("🎨 थीम व सेटिंग्स")
    theme_choice = st.selectbox(
        "अपनी पसंद का रंग/थीम चुनें:",
        ["🌟 रॉयल गोल्ड डार्क (Dark Gold)", "☀️ क्लासिक लाइट (Bright White)", "🌌 डीप नेवी ब्लू (Navy Blue)", "🌿 लग्ज़री ग्रीन (Emerald)"]
    )
    if st.button("लॉगआउट 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

# थीम्स के अनुसार कस्टम CSS (सभी लेबल्स और बटन टेक्स्ट 100% साफ़ दिखेंगे)
if theme_choice == "☀️ क्लासिक लाइट (Bright White)":
    bg_color = "#f8f9fa"
    text_color = "#111827"
    card_bg = "#ffffff"
    accent = "#d97706"
    tab_bg = "#e5e7eb"
    btn_bg = "#2563eb"
    btn_text = "#ffffff"
elif theme_choice == "🌌 डीप नेवी ब्लू (Navy Blue)":
    bg_color = "#0a192f"
    text_color = "#e6f1ff"
    card_bg = "#112240"
    accent = "#64ffda"
    tab_bg = "#172a45"
    btn_bg = "#64ffda"
    btn_text = "#0a192f"
elif theme_choice == "🌿 लग्ज़री ग्रीन (Emerald)":
    bg_color = "#06231a"
    text_color = "#e8f5e9"
    card_bg = "#0c3b2e"
    accent = "#69db7c"
    tab_bg = "#134e3f"
    btn_bg = "#69db7c"
    btn_text = "#06231a"
else:  # रॉयल गोल्ड डार्क
    bg_color = "#12141a"
    text_color = "#ffffff"
    card_bg = "#1c1f2a"
    accent = "#f59e0b"
    tab_bg = "#232736"
    btn_bg = "#f59e0b"
    btn_text = "#111827"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    label, .stMarkdown, p, h1, h2, h3, span {{
        color: {text_color} !important;
        font-weight: 500;
    }}
    div[data-testid="stMetricValue"] {{
        color: {accent} !important;
        font-weight: 800 !important;
        font-size: 1.8rem;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {text_color} !important;
        font-weight: 600 !important;
        opacity: 0.9;
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
        padding: 10px 20px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }}
    .stDownloadButton button:hover {{
        opacity: 0.9;
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
conn.commit()

TARGET = 1000000000  # 100 करोड़

# मुख्य हेडिंग
st.title("👑 100 Crore Wealth Hub")
st.caption("रंग बदलें, नकद, ख़र्च, संपत्तियां और 100 करोड़ का लक्ष्य ट्रैक करें")

# 8 टैब्स
tab1, tab2, tab_exp, tab_analytics, tab3, tab4, tab_blueprint, tab5 = st.tabs([
    "📊 कुल डैशबोर्ड", 
    "💵 नकद कमाई", 
    "💸 दैनिक ख़र्च",
    "📈 बचत दर",
    "🥇 गोल्ड व एसेट्स", 
    "🚀 100 Cr रोडमैप",
    "⚡ बिज़नेस ब्लूप्रिंट",
    "🔥 अनुशासन व लक्ष्य"
])

# ----------------- TAB 2: CASH INCOME -----------------
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
                "व्यापार / बिज़नेस (Business)",
                "दैनिक बचत (Daily Savings)",
                "ट्रेडिंग व निवेश (Trading/Investments)",
                "साइड वर्क / फ़्रीलांसिंग (Side Hustle)",
                "अन्य स्रोत (Other)"
            ])
        with col_cat2:
            custom_note = st.text_input("अतिरिक्त नोट", value="")
        
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 कमाई सेव करें")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
                           (str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} कमाई में जुड़ गए!")
            st.rerun()

    cash_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', daily_amount as 'रकम (₹)', note as 'विवरण' FROM income_history ORDER BY id DESC", conn)
    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        csv_cash = cash_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 कमाई डेटा डाउनलोड करें", data=csv_cash, file_name="income_records.csv", mime="text/csv")
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
            exp_cat = st.selectbox("ख़र्च की श्रेणी", ["ज़रूरी ख़र्च (Essentials)", "सफ़र / पेट्रोल", "खाना / राशन", "बिज़नेस ख़र्च", "मनोरंजन / अन्य"])
        with col_e2:
            exp_amt = st.number_input("ख़र्च रकम (₹ में)", min_value=0.0, step=100.0)
            exp_note = st.text_input("ख़र्च का विवरण", value="")
        submit_exp = st.form_submit_button("💾 ख़र्च दर्ज करें")

        if submit_exp and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (entry_date, amount, category, note) VALUES (?, ?, ?, ?)",
                           (str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} ख़र्च में दर्ज हुए!")
            st.rerun()

    exp_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', amount as 'रकम (₹)', category as 'श्रेणी', note as 'विवरण' FROM expense_history ORDER BY id DESC", conn)
    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ ख़र्च एंट्री हटाएँ"):
            del_exp_id = st.selectbox("ख़र्च चुनें:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'रकम (₹)'].values[0]:,.0f} ({exp_df.loc[exp_df['id']==x, 'श्रेणी'].values[0]})")
            if st.button("❌ ख़र्च मिटाएँ"):
                cursor.execute("DELETE FROM expense_history WHERE id = ?", (del_exp_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 कमाई बनाम ख़र्च व बचत दर (Savings Rate)")
    total_inc = cash_df["रकम (₹)"].sum() if not cash_df.empty else 0.0
    total_exp = exp_df["रकम (₹)"].sum() if not exp_df.empty else 0.0
    savings_rate = ((total_inc - total_exp) / total_inc * 100) if total_inc > 0 else 0.0

    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1:
        st.metric("कुल नकद कमाई", f"₹{total_inc:,.0f}")
    with col_an2:
        st.metric("कुल ख़र्च", f"₹{total_exp:,.0f}")
    with col_an3:
        st.metric("बचत दर (Savings Rate)", f"{savings_rate:.1f}%")

    comp_df = pd.DataFrame({
        "रकम (₹)": [total_inc, total_exp, max(total_inc - total_exp, 0.0)]
    }, index=["कुल कमाई", "कुल ख़र्च", "शुद्ध बचत"])
    st.bar_chart(comp_df)

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 गोल्ड व अन्य संपत्तियां")
    asset_mode = st.radio("जोड़ने का तरीका:", ["गोल्ड ऑटो-कैलकुलेटर (Gram based)", "अन्य एसेट (Manual Value)"], horizontal=True)

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("तारीख", value=date.today(), key="asset_date")
        
        if asset_mode == "गोल्ड ऑटो-कैलकुलेटर (Gram based)":
            with col2:
                gold_purity = st.selectbox("शुद्धता", ["24K (99.9% शुद्ध सोना)", "22K (गहने)", "चाँदी (Silver)"])
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                grams = st.number_input("मात्रा (ग्राम में):", min_value=0.1, value=10.0, step=0.5)
            with c_g2:
                rate_per_gram = st.number_input("प्रति 1 ग्राम भाव (₹):", min_value=100.0, value=7500.0, step=50.0)
            calc_val = grams * rate_per_gram
            st.info(f"💡 अनुमानित वैल्यू: **₹{calc_val:,.0f}**")
            asset_type = f"Gold ({gold_purity})" if "2" in gold_purity else "Silver"
            final_val = calc_val
            final_qty = grams
            asset_note = st.text_input("विवरण:", value=f"{grams}g @ ₹{rate_per_gram}/g")
        else:
            with col2:
                asset_type = st.selectbox("एसेट प्रकार", ["ज़मीन / प्लॉट", "मकान / फ्लैट", "शेयर / म्यूचुअल फंड", "अन्य संपत्ति"])
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                final_val = st.number_input("कुल वैल्यू (₹):", min_value=1000.0, step=5000.0)
            with c_m2:
                final_qty = st.number_input("मात्रा:", min_value=1.0, value=1.0, step=1.0)
            asset_note = st.text_input("विवरण:", value="दीर्घकालिक संपत्ति")

        submit_asset = st.form_submit_button("💾 एसेट सेव करें")
        if submit_asset and final_val > 0:
            cursor.execute("INSERT INTO assets_history (entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?)",
                           (str(asset_date), asset_type, final_qty, final_val, asset_note))
            conn.commit()
            st.success("एसेट जुड़ गया!")
            st.rerun()

    asset_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', asset_type as 'प्रकार', quantity as 'मात्रा', current_value as 'वैल्यू (₹)', note as 'विवरण' FROM assets_history ORDER BY id DESC", conn)
    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ एसेट एंट्री हटाएँ"):
            del_asset_id = st.selectbox("एसेट चुनें:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'प्रकार'].values[0]} (₹{asset_df.loc[asset_df['id']==x, 'वैल्यू (₹)'].values[0]:,.0f})")
            if st.button("❌ एसेट मिटाएँ"):
                cursor.execute("DELETE FROM assets_history WHERE id = ?", (del_asset_id,))
                conn.commit()
                st.rerun()

# मुख्य वित्तीय गणनाएँ
total_gross_income = cash_df["रकम (₹)"].sum() if not cash_df.empty else 0.0
total_expenses = exp_df["रकम (₹)"].sum() if not exp_df.empty else 0.0
total_net_cash = max(total_gross_income - total_expenses, 0.0)
total_assets = asset_df["वैल्यू (₹)"].sum() if not asset_df.empty else 0.0
total_networth = total_net_cash + total_assets

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("कुल कमाई", f"₹{total_gross_income:,.0f}")
    with col_m2:
        st.metric("कुल ख़र्च", f"₹{total_expenses:,.0f}")
    with col_m3:
        st.metric("शुद्ध नकद बचत", f"₹{total_net_cash:,.0f}")
    with col_m4:
        st.metric("कुल नेटवर्थ 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ के लक्ष्य का सफर: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 करोड़ तक पहुँचने में अभी ₹{TARGET - total_networth:,.0f} और शेष हैं।")

    if total_networth > 0:
        st.write("### 🍰 संपत्ति का बँटवारा (Asset Allocation)")
        chart_summary = pd.DataFrame({"राशि (₹)": [total_net_cash, total_assets]}, index=["शुद्ध नकद", "गोल्ड व एसेट्स"])
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
            st.write("वर्तमान गति से समय लगेगा: -- वर्ष")
    with col_v2:
        target_years = st.selectbox("100 करोड़ पाने का लक्ष्य समय (साल):", [10, 15, 20, 25, 30], index=1)
        req_month = (TARGET - total_networth) / (target_years * 12)
        st.write(f"**{target_years} साल में 100 करोड़ के लिए:**")
        st.write(f"मासिक शुद्ध बचत चाहिए: **₹{req_month:,.0f}/महीना**")

    # PDF डाउनलोड बटन (सुपर क्लियर)
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
            ["Total Income", f"Rs. {total_gross_income:,.0f}", "Gross Earnings"],
            ["Total Expenses", f"Rs. {total_expenses:,.0f}", "Outflow"],
            ["Net Liquid Cash", f"Rs. {total_net_cash:,.0f}", "In Hand"],
            ["Total Assets & Gold", f"Rs. {total_assets:,.0f}", "Valuation"]
        ]
        t = Table(summary_data, colWidths=[200, 170, 170])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2d3748")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ('FONTSIZE', (0, 0), (-1, -1), 10)
        ]))
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    st.download_button(
        label="📥 वेल्थ ऑडिट PDF डाउनलोड करें (Click to Download)",
        data=generate_wealth_pdf(),
        file_name=f"Wealth_Report_{date.today()}.pdf",
        mime="application/pdf"
    )

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 माइलस्टोन लेडर (Wealth Milestones)")
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

# ----------------- TAB: 100 CR BUSINESS BLUEPRINT -----------------
with tab_blueprint:
    st.subheader("⚡ 100 करोड़ का रिवर्स गणित")
    blueprint_table = [
        {"उत्पाद/सर्विस मूल्य (Ticket Size)": "₹1,000 की सर्विस / प्रॉडक्ट", "आवश्यक बिक्री / ग्राहक": "10,00,000 (10 लाख लोग)", "कुल वैल्यू": "₹100 करोड़"},
        {"उत्पाद/सर्विस मूल्य (Ticket Size)": "₹10,000 की डील / कोर्स / टूल", "आवश्यक बिक्री / ग्राहक": "1,00,000 (1 लाख लोग)", "कुल वैल्यू": "₹100 करोड़"},
        {"उत्पाद/सर्विस मूल्य (Ticket Size)": "₹50,000 की कॉन्ट्रैक्ट / एजेंसी डील", "आवश्यक बिक्री / ग्राहक": "20,000 लोग", "कुल वैल्यू": "₹100 करोड़"},
        {"उत्पाद/सर्विस मूल्य (Ticket Size)": "₹1,00,000 का हाई-टिकट बिज़नेस", "आवश्यक बिक्री / ग्राहक": "10,000 लोग", "कुल वैल्यू": "₹100 करोड़"}
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
