import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="100 Crore Target Hub", page_icon="🚀", layout="centered")

# --- डेटाबेस सेटअप (SQLite) ---
conn = sqlite3.connect("wealth_data.db", check_same_thread=False)
cursor = conn.cursor()

# टेबल बनाना (अगर पहले से न बनी हो)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS income_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        daily_amount REAL,
        note TEXT
    )
""")
conn.commit()

# --- ऐप इंटरफ़ेस ---
st.title("🚀 100 Crore Target Web App")
st.caption("आपका निजी वित्तीय डेटाबेस: रोज़ का हिसाब हमेशा सुरक्षित")

TARGET = 1000000000  # 100 करोड़

# फ़ॉर्म: रोज़ की एंट्री जोड़ने के लिए
with st.form("entry_form", clear_on_submit=True):
    st.subheader("📝 आज की नई कमाई दर्ज करें")
    col_a, col_b = st.columns(2)
    with col_a:
        entry_date = st.date_input("तारीख", value=date.today())
    with col_b:
        daily_income = st.number_input("कमाई (₹ में)", min_value=0.0, step=500.0)
    
    note = st.text_input("विवरण / नोट (उदा. बिज़नेस, ट्रेडिंग, बचत)", value="दैनिक बचत")
    submit_button = st.form_submit_button("💾 डेटाबेस में सेव करें")

    if submit_button and daily_income > 0:
        cursor.execute(
            "INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
            (str(entry_date), daily_income, note)
        )
        conn.commit()
        st.success(f"✅ ₹{daily_income:,.0f} सफलतापूर्वक डेटाबेस में सेव हो गए!")

# --- डेटाबेस से डेटा पढ़ना ---
df = pd.read_sql_query("SELECT entry_date as 'तारीख', daily_amount as 'कमाई (₹)', note as 'विवरण' FROM income_history ORDER BY id DESC", conn)

st.divider()

if not df.empty:
    total_saved = df["कमाई (₹)"].sum()
    total_entries = len(df)
    
    # मुख्य कार्ड
    col1, col2 = st.columns(2)
    with col1:
        st.metric("कुल जमा पूँजी", f"₹{total_saved:,.0f}")
    with col2:
        st.metric("कुल दर्ज दिन", f"{total_entries} दिन")

    # प्रोग्रेस बार
    progress_percent = min(total_saved / TARGET, 1.0)
    st.write(f"### 🎯 ₹100 करोड़ में से लक्ष्य पूरा हुआ: `{progress_percent * 100:.6f}%`")
    st.progress(progress_percent)

    remaining = TARGET - total_saved
    st.info(f"💡 100 करोड़ के लक्ष्य तक पहुँचने के लिए अभी ₹{remaining:,.0f} और शेष हैं।")

    # विज़ुअल चार्ट
    st.write("### 📈 कमाई का ट्रेंड (ग्राफ़)")
    chart_df = df.sort_values(by="तारीख").copy()
    chart_df.set_index("तारीख", inplace=True)
    st.line_chart(chart_df["कमाई (₹)"])

    # हिस्ट्री टेबल
    st.write("### 🗂️ पिछली सभी एंट्रियों का रिकॉर्ड")
    st.dataframe(df, use_container_width=True)
else:
    st.info("डेटाबेस अभी खाली है। ऊपर फ़ॉर्म में आज की कमाई दर्ज करके सेव करें!")
