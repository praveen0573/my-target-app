import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

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
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1c24;
        border-radius: 8px;
        color: #d4af37;
        padding: 8px 16px;
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
    st.caption("नकद, सोना, संपत्तियां और कम्पाउंडिंग रोडमैप")
with header_col2:
    if st.button("लॉगआउट 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

# टैब्स
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 कुल डैशबोर्ड", 
    "💵 नकद बचत व महीनेवार", 
    "🥇 गोल्ड व एसेट्स", 
    "🚀 100 Cr रोडमैप"
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
        note = st.text_input("विवरण", value="दैनिक बचत", key="cash_note")
        submit_cash = st.form_submit_button("💾 कैश सेव करें")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
                           (str(entry_date), daily_income, note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} कैश में जुड़ गए!")
            st.rerun()

    cash_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', daily_amount as 'रकम (₹)', note as 'विवरण' FROM income_history ORDER BY id DESC", conn)
    
    if not cash_df.empty:
        # तारीख को डेटटाइम में बदलना ताकि महीने निकाल सकें
        cash_df["Date_Obj"] = pd.to_datetime(cash_df["तारीख"])
        cash_df["महीना"] = cash_df["Date_Obj"].dt.strftime('%B %Y')
        
        st.divider()
        st.subheader("📅 महीनेवार रिपोर्ट (Monthly Analysis)")
        
        # महीने का फ़िल्टर
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
    with st.form("asset_form", clear_on_submit=True):
        st.subheader("🥇 नया एसेट / सोना दर्ज करें")
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("तारीख", value=date.today(), key="asset_date")
            asset_type = st.selectbox("एसेट का प्रकार", ["गोल्ड (Gold)", "चाँदी (Silver)", "ज़मीन / प्रॉपर्टी", "अन्य एसेट"])
        with col2:
            current_value = st.number_input("कुल मौजूदा वैल्यू (₹ में)", min_value=0.0, step=1000.0)
            quantity = st.number_input("मात्रा (उदा. ग्राम / यूनिट)", min_value=0.0, step=1.0)
        asset_note = st.text_input("विवरण (उदा. 24K Gold, 10 ग्राम सिक्का)", value="गोल्ड इनवेस्टमेंट")
        submit_asset = st.form_submit_button("💾 एसेट सेव करें")

        if submit_asset and current_value > 0:
            cursor.execute("INSERT INTO assets_history (entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?)",
                           (str(asset_date), asset_type, quantity, current_value, asset_note))
            conn.commit()
            st.success("एसेट दर्ज हो गया!")
            st.rerun()

    asset_df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', asset_type as 'प्रकार', quantity as 'मात्रा', current_value as 'वैल्यू (₹)', note as 'विवरण' FROM assets_history ORDER BY id DESC", conn)
    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        csv_asset = asset_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 एसेट डेटा डाउनलोड करें", data=csv_asset, file_name="asset_records.csv", mime="text/csv")
        
        with st.expander("🗑️ एसेट एंट्री हटाएँ"):
            del_asset_id = st.selectbox("एसेट चुनें:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'प्रकार'].values[0]} (₹{asset_df.loc[asset_df['id']==x, 'वैल्यू (₹)'].values[0]:,.0f})")
            if st.button("❌ एसेट मिटाएँ"):
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
