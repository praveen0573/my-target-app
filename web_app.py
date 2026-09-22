import streamlit as st
import pandas as pd

# पेज सेटअप
st.set_page_config(page_title="100 Crore Target Hub", page_icon="🚀", layout="centered")

st.title("🚀 100 Crore Target Web App")
st.write("अपने मोबाइल और लैपटॉप दोनों पर बड़े लक्ष्य का हिसाब रखें।")

TARGET = 1000000000  # 100 करोड़

# इनपुट
daily_income = st.number_input("आज कितने पैसे कमाए? (रुपये दर्ज करें):", min_value=0, value=5000, step=500)

if st.button("📊 हिसाब लगाओ और प्रोग्रेस देखो"):
    monthly = daily_income * 30
    yearly = daily_income * 365
    
    # कमाई के कार्ड
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="महीने की कमाई", value=f"₹{monthly:,.0f}")
    with col2:
        st.metric(label="साल की कमाई", value=f"₹{yearly:,.0f}")

    # प्रोग्रेस बार (% में)
    progress_percent = min(yearly / TARGET, 1.0)
    st.write(f"### 🎯 100 करोड़ के लक्ष्य की वार्षिक गति: `{progress_percent * 100:.4f}%`")
    st.progress(progress_percent)
    
    # 5 साल का चार्ट
    st.write("### 📈 अगले 5 सालों का अनुमानित ग्राफ़")
    years = [f"Year {i}" for i in range(1, 6)]
    projected_wealth = [yearly * i for i in range(1, 6)]
    chart_data = pd.DataFrame({"कुल कमाई (₹)": projected_wealth}, index=years)
    st.bar_chart(chart_data)

    remaining = TARGET - yearly
    if remaining > 0:
        st.info(f"💡 इस रफ़्तार से 100 करोड़ पहुँचने में अभी ₹{remaining:,.0f} सालाना और चाहिए।")
    else:
        st.success("🎉 बधाई! आप 100 करोड़ के वार्षिक लक्ष्य को पार कर चुके हैं!")
