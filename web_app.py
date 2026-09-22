import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import random

# --- पेज कॉन्फ़िगरेशन ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- कस्टम डार्क लग्ज़री CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    div[data-testid="stMetricValue"] {
        color: #d4af37 !important;
        font-weight: 700;
        font-size: 1.8rem;
    }
    div[data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1c24;
        border-radius: 8px;
        color: #d4af37;
        padding: 6px 12px;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262936 !important;
        border-bottom: 2px solid #d4af37 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- सुरक्षा पिन (Secret PIN Protection) ---
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

# हेडर और लॉगआउट
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("👑 100 Crore Wealth Hub")
    st.caption("नकद, सोना, संपत्तियां और मल्टीपल इनकम स्ट्रीम्स")
with header_col2:
    if st.button("लॉगआउट 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

# 6 टैब्स
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 कुल डैशबोर्ड", 
    "💵 नकद बचत", 
    "🥇 गोल्ड व एसेट्स", 
    "🚀 100 Cr रोडमैप",
    "🔥 अनुशासन व लक्ष्य",
    "👑 इनकम स्ट्रीम्स व विज़न"
])

# ----------------- TAB 2: CASH INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 नई नकद बचत दर्ज करें")
        col_a, col_b = st.columns(2)
        with col_a:
            entry_date = st.date_input("तारीख", value=date.today(), key="cash_date")
        with col_b:
            daily_income = st.number_input("रकम (₹ में)", min_value=0.0, step=500.0)
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("आय का स्रोत (Category)", [
                "व्यापार / बिज़नेस (Business)",
                "दैनिक बचत (Daily Savings)",
                "ट्रेडिंग व निवेश (Trading/Investments)",
                "साइड वर्क / फ़्रीलांसिंग (Side Hustle)",
                "अन्य स्रोत (Other)"
            ])
        with col_cat2:
            custom_note = st.text_input("अतिरिक्त नोट", value="")
        
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 कैश सेव करें")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
                           (str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} कैश में जुड़ गए!")
            st.rerun()

    cash_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', daily_amount as 'रकम (₹)', note as 'विवरण' FROM income_history ORDER BY id DESC", conn)
    
    if not cash_df.empty:
        cash_df["Date_Obj"] = pd.to_datetime(cash_df["तारीख"])
        cash_df["महीना"] = cash_df["Date_Obj"].dt.strftime('%B %Y')
        
        st.divider()
        st.subheader("📅 महीनेवार रिपोर्ट (Monthly Analysis)")
        
        available_months = ["सभी महीने"] + list(cash_df["महीना"].unique())
        selected_month = st.selectbox("महीना चुनें:", available_months)
        
        if selected_month == "सभी महीने":
            filtered_cash = cash_df
        else:
            filtered_cash = cash_df[cash_df["महीना"] == selected_month]
            
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("चुने महीने की कुल बचत", f"₹{filtered_cash['रकम (₹)'].sum():,.0f}")
        with m_col2:
            st.metric("कुल एंट्रियां", f"{len(filtered_cash)} बार")
        with m_col3:
            avg_val = filtered_cash['रकम (₹)'].mean() if len(filtered_cash) > 0 else 0
            st.metric("औसत प्रति एंट्री", f"₹{avg_val:,.0f}")

        st.dataframe(filtered_cash.drop(columns=["id", "Date_Obj", "महीना"]), use_container_width=True)
        
        csv_cash = cash_df.drop(columns=["Date_Obj", "महीना"]).to_csv(index=False).encode('utf-8')
        st.download_button("📥 नकद डेटा डाउनलोड करें", data=csv_cash, file_name="cash_records.csv", mime="text/csv")
        
        with st.expander("🗑️ नकद एंट्री हटाएँ"):
            del_id = st.selectbox("एंट्री चुनें:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'रकम (₹)'].values[0]:,.0f}")
            if st.button("❌ कैश एंट्री मिटाएँ"):
                cursor.execute("DELETE FROM income_history WHERE id = ?", (del_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 गोल्ड व अन्य संपत्तियां दर्ज करें")
    
    asset_mode = st.radio("जोड़ने का तरीका चुनें:", ["गोल्ड ऑटो-कैलकुलेटर (Gram based)", "अन्य एसेट (Manual Value)"], horizontal=True)

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("तारीख", value=date.today(), key="asset_date")
        
        if asset_mode == "गोल्ड ऑटो-कैलकुलेटर (Gram based)":
            with col2:
                gold_purity = st.selectbox("शुद्धता", ["24K (99.9% शुद्ध सोना)", "22K (गहने/ज्वेलरी)", "चाँदी (Silver)"])
            
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                grams = st.number_input("सोना / चाँदी (ग्राम में):", min_value=0.1, value=10.0, step=0.5)
            with c_g2:
                rate_per_gram = st.number_input("प्रति 1 ग्राम का भाव (₹ में):", min_value=100.0, value=7500.0, step=50.0)
            
            calc_val = grams * rate_per_gram
            st.info(f"💡 कुल अनुमानित वैल्यू: **₹{calc_val:,.0f}**")
            asset_type = f"Gold ({gold_purity})" if "2" in gold_purity else "Silver"
            final_val = calc_val
            final_qty = grams
            asset_note = st.text_input("विवरण / नोट:", value=f"{grams}g सोना @ ₹{rate_per_gram}/g")
        else:
            with col2:
                asset_type = st.selectbox("एसेट का प्रकार", ["ज़मीन / प्लॉट", "मकान / फ्लैट", "शेयर / म्यूचुअल फंड", "अन्य संपत्ति"])
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                final_val = st.number_input("कुल मौजूदा वैल्यू (₹ में):", min_value=1000.0, step=5000.0)
            with c_m2:
                final_qty = st.number_input("मात्रा (Units / Sq.Ft / Qty):", min_value=1.0, value=1.0, step=1.0)
            asset_note = st.text_input("विवरण:", value="दीर्घकालिक संपत्ति")

        submit_asset = st.form_submit_button("💾 एसेट डेटाबेस में जोड़ें")

        if submit_asset and final_val > 0:
            cursor.execute("INSERT INTO assets_history (entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?)",
                           (str(asset_date), asset_type, final_qty, final_val, asset_note))
            conn.commit()
            st.success("एसेट सफलतापूर्वक जुड़ गया!")
            st.rerun()

    asset_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', asset_type as 'प्रकार', quantity as 'मात्रा/ग्राम', current_value as 'वैल्यू (₹)', note as 'विवरण' FROM assets_history ORDER BY id DESC", conn)
    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        csv_asset = asset_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 एसेट डेटा डाउनलोड करें", data=csv_asset, file_name="asset_records.csv", mime="text/csv")
        
        with st.expander("🗑️ एसेट एंट्री हटाएँ"):
            del_asset_id = st.selectbox("एसेट चुनें:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'प्रकार'].values[0]} (₹{asset_df.loc[asset_df['id']==x, 'वैल्यू (₹)'].values[0]:,.0f})")
            if st.button("❌ चुनी हुई एसेट मिटाएँ"):
                cursor.execute("DELETE FROM assets_history WHERE id = ?", (del_asset_id,))
                conn.commit()
                st.rerun()

# कुल आंकड़े
total_cash = cash_df["रकम (₹)"].sum() if not cash_df.empty else 0.0
total_assets = asset_df["वैल्यू (₹)"].sum() if not asset_df.empty else 0.0
total_networth = total_cash + total_assets

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("कुल नकद बचत", f"₹{total_cash:,.0f}")
    with col_m2:
        st.metric("कुल एसेट्स / गोल्ड", f"₹{total_assets:,.0f}")
    with col_m3:
        st.metric("कुल नेटवर्थ", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ के लक्ष्य का सफर: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 करोड़ तक पहुँचने में अभी ₹{TARGET - total_networth:,.0f} और शेष हैं।")

    if total_networth > 0:
        st.write("### 🍰 संपत्ति का बँटवारा (Asset Allocation)")
        chart_summary = pd.DataFrame({"राशि (₹)": [total_cash, total_assets]}, index=["नकद बचत", "गोल्ड व एसेट्स"])
        st.bar_chart(chart_summary)

    # 100 करोड़ स्पीड मीटर
    st.divider()
    st.subheader("⚡ 100 करोड़ स्पीड व समय कैलकुलेटर")
    daily_avg = cash_df["रकम (₹)"].mean() if not cash_df.empty else 0.0
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.write(f"**आपकी औसत दैनिक बचत:** ₹{daily_avg:,.0f}/दिन")
        if daily_avg > 0:
            days_needed = (TARGET - total_networth) / daily_avg
            years_needed = days_needed / 365
            st.write(f"वर्तमान गति से समय लगेगा: **{years_needed:.1f} वर्ष**")
        else:
            st.write("वर्तमान गति से समय लगेगा: -- वर्ष")
    
    with col_v2:
        target_years = st.selectbox("यदि आप 100 करोड़ पाना चाहते हैं:", [10, 15, 20, 25, 30], index=1)
        required_per_month = (TARGET - total_networth) / (target_years * 12)
        required_per_day = required_per_month / 30
        st.write(f"**{target_years} साल का लक्ष्य पाने के लिए:**")
        st.write(f"रोज़ाना चाहिए: **₹{required_per_day:,.0f}/दिन**")
        st.write(f"मासिक चाहिए: **₹{required_per_month:,.0f}/महीना**")

# ----------------- TAB 4: ROADMAP & COMPOUNDING -----------------
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
    st.subheader("⚡ कम्पाउंडिंग ग्रोथ सिमुलेटर (Power of Compounding)")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        monthly_invest = st.number_input("हर महीने का निवेश / बचत (₹):", min_value=1000, value=25000, step=5000)
    with col_s2:
        annual_rate = st.slider("अनुमानित सालाना रिटर्न (% में):", min_value=8.0, max_value=25.0, value=15.0, step=0.5)

    years_list = list(range(1, 31))
    future_values = []
    r = (annual_rate / 100) / 12

    for yr in years_list:
        n = yr * 12
        fv = monthly_invest * (((1 + r)**n - 1) / r) * (1 + r) + (total_networth * ((1 + annual_rate/100)**yr))
        future_values.append(round(fv))

    sim_df = pd.DataFrame({"अनुमानित नेटवर्थ (₹)": future_values}, index=[f"वर्ष {y}" for y in years_list])
    
    st.write(f"📈 अगले 30 सालों में कम्पाउंडिंग का ग्राफ़ ({annual_rate}% सालाना रिटर्न पर):")
    st.line_chart(sim_df)

    reach_year = None
    for yr, val in zip(years_list, future_values):
        if val >= TARGET:
            reach_year = yr
            break

    if reach_year:
        st.success(f"🎯 इस रफ़्तार और कम्पाउंडिंग के साथ आप **{reach_year}वें साल** में ₹100 करोड़ पार कर जाएँगे!")
    else:
        st.info("💡 100 करोड़ और तेज़ी से पाने के लिए अपनी मासिक बचत या बिज़नेस कैशफ़्लो को बढ़ाएँ।")

# ----------------- TAB 5: DISCIPLINE & DAILY TARGET -----------------
with tab5:
    st.subheader("🔥 दैनिक अनुशासन व स्ट्राइक (Daily Streak & Target)")
    
    quotes = [
        "\"अमीर बनने की शुरुआत बड़े सपनों से नहीं, रोज़ के छोटे अनुशासन से होती है।\"",
        "\"जो व्यक्ति छोटे-छोटे रुपयों की कद्र नहीं करता, वह 100 करोड़ कभी नहीं संभाल सकता।\"",
        "\"कम्पाउंडिंग दुनिया का आठवाँ अजूबा है—जो इसे समझता है वह कमाता है।\"",
        "\"वित्तीय अनुशासन आज की कुर्बानी और कल की आज़ादी का सौदा है।\""
    ]
    st.info(f"💡 {random.choice(quotes)}")

    today_str = str(date.today())
    today_savings = 0.0
    if not cash_df.empty:
        today_rows = cash_df[cash_df["तारीख"] == today_str]
        today_savings = today_rows["रकम (₹)"].sum()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        daily_target = st.number_input("आज का बचत लक्ष्य (₹):", min_value=500, value=2000, step=500)
    with col_d2:
        st.metric("आज की कुल बचत", f"₹{today_savings:,.0f}")

    daily_prog = min(today_savings / daily_target, 1.0)
    st.write(f"**आज का दैनिक लक्ष्य पूरा हुआ:** `{daily_prog * 100:.1f}%`")
    st.progress(daily_prog)

    if today_savings >= daily_target:
        st.success("🎯 आज का दैनिक अनुशासन लक्ष्य पूरा हुआ! निरंतरता ही सफलता की कुंजी है।")
    else:
        st.warning(f"⏳ आज के लक्ष्य से अभी ₹{daily_target - today_savings:,.0f} दूर हैं।")

    unique_dates = sorted(cash_df["तारीख"].unique().tolist(), reverse=True) if not cash_df.empty else []
    streak = 0
    check_day = date.today()
    
    if today_str not in unique_dates:
        check_day = date.today() - timedelta(days=1)

    while str(check_day) in unique_dates:
        streak += 1
        check_day = check_day - timedelta(days=1)

    st.divider()
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.metric("वर्तमान स्ट्राइक (Streak)", f"🔥 {streak} दिन")
    with s_col2:
        st.metric("कुल सक्रिय दिन", f"📅 {len(unique_dates)} दिन")

# ----------------- TAB 6: INCOME STREAMS & VISION -----------------
with tab6:
    st.subheader("👑 आय के स्रोत (Income Streams Breakdown)")
    
    if not cash_df.empty:
        # विवरण से कैटेगरी निकालना
        def extract_cat(val):
            if "[" in str(val) and "]" in str(val):
                return str(val).split("]")[0].replace("[", "").strip()
            return "अन्य स्रोत"

        cash_df["Category"] = cash_df["विवरण"].apply(extract_cat)
        cat_summary = cash_df.groupby("Category")["रकम (₹)"].sum().reset_index()
        
        st.write("📊 किस स्रोत से कितना धन आया:")
        chart_cat = cat_summary.set_index("Category")
        st.bar_chart(chart_cat)
        st.dataframe(cat_summary, use_container_width=True)
    else:
        st.info("जैसे-जैसे आप नकद बचत जोड़ेंगे, आय स्रोतों का विश्लेषण यहाँ दिखेगा।")

    st.divider()
    st.subheader("🎯 100 करोड़ एलीट माइंडसेट रूल्स (Rules of Elite Wealth)")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("""
        **1. एसेट्स पर फ़ोकस:**
        * कभी सिर्फ़ पैसे जमा मत करो; उसे ऐसे एसेट्स (सोना, प्रॉपर्टी, बिज़नेस) में बदलो जो अपने आप बढ़ें।
        
        **2. कैशफ़्लो का विस्तार:**
        * कभी भी सिर्फ़ एक इनकम पर निर्भर न रहें। नए स्किल्स और बिज़नेस से आय के नए रास्ते खोलें।
        """)
    with col_v2:
        st.markdown("""
        **3. सख्त वित्तीय अनुशासन:**
        * दिखावे वाले खर्च शून्य, निवेश शत-प्रतिशत। 
        
        **4. दीर्घकालिक दृष्टि:**
        * 100 करोड़ का लक्ष्य रातों-रात का लॉटरी टिकट नहीं, बल्कि वर्षों का अटूट संकल्प है।
        """)
