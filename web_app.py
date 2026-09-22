import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="100 Crore Target Hub", page_icon="🚀", layout="centered")

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
conn.commit()

# --- मुख्य हेडिंग ---
st.title("🚀 100 Crore Target Web App")
st.caption("निजी वित्तीय ट्रैकर: डेटाबेस और रिकॉर्ड मैनेजमेंट")

TARGET = 1000000000  # 100 करोड़

# --- नया डेटा जोड़ने का फ़ॉर्म ---
with st.form("entry_form", clear_on_submit=True):
    st.subheader("📝 नई कमाई दर्ज करें")
    col_a, col_b = st.columns(2)
    with col_a:
        entry_date = st.date_input("तारीख", value=date.today())
    with col_b:
        daily_income = st.number_input("कमाई (₹ में)", min_value=0.0, step=500.0)
    
    note = st.text_input("विवरण / नोट", value="दैनिक बचत")
    submit_button = st.form_submit_button("💾 डेटाबेस में सेव करें")

    if submit_button and daily_income > 0:
        cursor.execute(
            "INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
            (str(entry_date), daily_income, note)
        )
        conn.commit()
        st.success(f"✅ ₹{daily_income:,.0f} डेटाबेस में जुड़ गए!")
        st.rerun()

# --- डेटा पढ़ना ---
df = pd.read_sql_query("SELECT id, entry_date as 'तारीख', daily_amount as 'कमाई (₹)', note as 'विवरण' FROM income_history ORDER BY id DESC", conn)

st.divider()

if not df.empty:
    total_saved = df["कमाई (₹)"].sum()
    total_entries = len(df)
    
    # मेट्रिक्स
    col1, col2 = st.columns(2)
    with col1:
        st.metric("कुल जमा पूँजी", f"₹{total_saved:,.0f}")
    with col2:
        st.metric("कुल दर्ज दिन", f"{total_entries} दिन")

    # प्रोग्रेस बार
    progress_percent = min(total_saved / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ का लक्ष्य: `{progress_percent * 100:.6f}%`")
    st.progress(progress_percent)

    # ट्रेंड चार्ट
    st.write("### 📈 कमाई का ट्रेंड (Line Chart)")
    chart_df = df.sort_values(by="id").copy()
    chart_df.set_index("तारीख", inplace=True)
    st.line_chart(chart_df["कमाई (₹)"])

    # रिकॉर्ड टेबल
    st.write("### 🗂️ पिछली सभी एंट्रियों का रिकॉर्ड")
    display_df = df.drop(columns=["id"])
    st.dataframe(display_df, use_container_width=True)

    # --- ग़लत एंट्री हटाने का विकल्प ---
    with st.expander("🗑️ ग़लत एंट्री हटाएँ (Delete Entry)"):
        entry_to_delete = st.selectbox(
            "हटाने के लिए एंट्री चुनें:",
            options=df["id"].tolist(),
            format_func=lambda x: f"ID {x} - {df.loc[df['id'] == x, 'तारीख'].values[0]} | ₹{df.loc[df['id'] == x, 'कमाई (₹)'].values[0]:,.0f} ({df.loc[df['id'] == x, 'विवरण'].values[0]})"
        )
        if st.button("❌ चुनी हुई एंट्री मिटाएँ", type="primary"):
            cursor.execute("DELETE FROM income_history WHERE id = ?", (entry_to_delete,))
            conn.commit()
            st.warning("एंट्री मिटा दी गई!")
            st.rerun()
else:
    st.info("डेटाबेस खाली है। ऊपर फ़ॉर्म से पहली एंट्री जोड़ें!")
