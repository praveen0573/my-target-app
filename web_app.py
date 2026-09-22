import streamlit as st

# वेब पेज का टाइटल
st.title("🚀 100 Crore Target Web App")
st.write("अपने मोबाइल और लैपटॉप दोनों पर हिसाब रखें।")

# इनपुट बॉक्स
aaj_ki_kamai = st.number_input("आज कितने पैसे कमाए? (रुपये दर्ज करें):", min_value=0, step=1000)

# बटन और हिसाब
if st.button("Hisaab Lagao"):
    mahina = aaj_ki_kamai * 30
    bache = 1000000000 - mahina
    
    st.success(f"महीने की कमाई बनेगी: ₹{mahina:,.0f}")
    st.info(f"100 करोड़ के टारगेट से बचे: ₹{bache:,.0f}")
    
    if mahina >= 2000000:
        st.balloons()