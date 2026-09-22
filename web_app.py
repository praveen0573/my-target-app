import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- डेटाबेस सेटअप ---
conn = sqlite3.connect("wealth_data.db", check_same_thread=False)
cursor = conn.cursor()

# नकद कमाई टेबल
cursor.execute("""
    CREATE TABLE IF NOT EXISTS income_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        daily_amount REAL,
        note TEXT
    )
""")

# एसेट/गोल्ड टेबल
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

st.title("👑 100 Crore Wealth Hub")
st.caption("नकद, सोना और संपत्तियों का पूरा हिसाब एक जगह")

# 3 अलग-अलग टैब्स
tab1, tab2, tab3 = st.tabs(["📊 कुल नेटवर्थ (Dashboard)", "💵 नकद बचत (Cash)", "🥇 गोल्ड और एसेट्स (Assets)"])

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
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
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
            st.success(f"एसेट दर्ज हो गया!")
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

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    total_cash = cash_df["रकम (₹)"].sum() if not cash_df.empty else 0.0
    total_assets = asset_df["वैल्यू (₹)"].sum() if not asset_df.empty else 0.0
    total_networth = total_cash + total_assets

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("कुल नकद बचत", f"₹{total_cash:,.0f}")
    with col_m2:
        st.metric("कुल एसेट्स / गोल्ड", f"₹{total_assets:,.0f}")
    with col_m3:
        st.metric("कुल नेटवर्थ", f"₹{total_networth:,.0f}")

    # प्रोग्रेस बार
    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ के लक्ष्य का सफर: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 करोड़ तक पहुँचने में अभी ₹{TARGET - total_networth:,.0f} और चाहिए।")

    # पाई चार्ट / विभाजन
    if total_networth > 0:
        st.write("### 🍰 संपत्ति का बँटवारा (Asset Allocation)")
        pie_data = pd.DataFrame({"राशि (₹)": [total_cash, total_assets]}, index=["नकद बचत", "गोल्ड व एसेट्स"])
        st.bar_chart(pie_data)
