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

# --- پیج سیٹ اپ ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- ڈارک لگژری تھیم CSS ---
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

# --- خفیہ پن پروٹیکشن ---
SECRET_PIN = "1234"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("محفوظ رسائی کے لیے 4 ہندسوں کا پن درج کریں۔")
    pin_input = st.text_input("خفیہ پن درج کریں:", type="password")
    if st.button("لاگ ان 🔓", type="primary"):
        if pin_input == SECRET_PIN:
            st.session_state["authenticated"] = True
            st.success("درست پن! ایپ کھل گئی ہے۔")
            st.rerun()
        else:
            st.error("غلط پن! دوبارہ کوشش کریں۔")
    st.stop()

# --- ڈیٹا بیس کنکشن ---
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

TARGET = 1000000000  # 100 کروڑ

# ہیڈر
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("👑 100 Crore Wealth Hub")
    st.caption("آمدن، اخراجات، اثاثے اور بجٹ اینالیٹکس")
with header_col2:
    if st.button("لاگ آؤٹ 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

# ٹیبز
tab1, tab2, tab_exp, tab_analytics, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 کل ڈیش بورڈ", 
    "💵 نقد آمدن", 
    "💸 روزانہ اخراجات",
    "📈 بجٹ اینالیٹکس",
    "🥇 گولڈ و اثاثے", 
    "🚀 100 Cr روڈ میپ",
    "🔥 اہداف و تسلسل",
    "👑 وژن بورڈ"
])

# ----------------- TAB 2: CASH INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 نئی نقد آمدن درج کریں")
        col_a, col_b = st.columns(2)
        with col_a:
            entry_date = st.date_input("تاریخ", value=date.today(), key="cash_date")
        with col_b:
            daily_income = st.number_input("رقم (₹ میں)", min_value=0.0, step=500.0)
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("آمدن کا ذریعہ", [
                "کاروبار / بزنس (Business)",
                "روزانہ بچت (Daily Savings)",
                "سرمایہ کاری (Trading/Investments)",
                "اضافی کام (Side Hustle)",
                "دیگر ذرائع (Other)"
            ])
        with col_cat2:
            custom_note = st.text_input("تفصیل / نوٹ", value="")
        
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 آمدن محفوظ کریں")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
                           (str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} آمدن میں شامل ہو گئے!")
            st.rerun()

    cash_df = pd.read_sql_query("SELECT id, entry_date as 'تاریخ', daily_amount as 'رقم (₹)', note as 'تفصیل' FROM income_history ORDER BY id DESC", conn)
    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        csv_cash = cash_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 آمدن ڈیٹا ڈاؤن لوڈ کریں", data=csv_cash, file_name="income_records.csv", mime="text/csv")
        with st.expander("🗑️ آمدن اینٹری ڈیلیٹ کریں"):
            del_id = st.selectbox("اینٹری منتخب کریں:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'رقم (₹)'].values[0]:,.0f}")
            if st.button("❌ آمدن اینٹری حذف کریں"):
                cursor.execute("DELETE FROM income_history WHERE id = ?", (del_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB: EXPENSES -----------------
with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("💸 روزانہ کا خرچ درج کریں")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            exp_date = st.date_input("تاریخ", value=date.today(), key="exp_date")
            exp_cat = st.selectbox("خرچ کی قسم", ["ضروری اخراجات", "سفر / ایندھن", "کھانا پینا", "بزنس خرچ", "غیر ضروری خرچ"])
        with col_e2:
            exp_amt = st.number_input("خرچ رقم (₹ میں)", min_value=0.0, step=100.0)
            exp_note = st.text_input("تفصیل", value="")
        submit_exp = st.form_submit_button("💾 خرچ محفوظ کریں")

        if submit_exp and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (entry_date, amount, category, note) VALUES (?, ?, ?, ?)",
                           (str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} خرچ درج ہو گیا!")
            st.rerun()

    exp_df = pd.read_sql_query("SELECT id, entry_date as 'تاریخ', amount as 'رقم (₹)', category as 'قسم', note as 'تفصیل' FROM expense_history ORDER BY id DESC", conn)
    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ خرچ اینٹری ڈیلیٹ کریں"):
            del_exp_id = st.selectbox("خرچ منتخب کریں:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'رقم (₹)'].values[0]:,.0f} ({exp_df.loc[exp_df['id']==x, 'قسم'].values[0]})")
            if st.button("❌ خرچ حذف کریں"):
                cursor.execute("DELETE FROM expense_history WHERE id = ?", (del_exp_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 آمدن بمقابلہ اخراجات (Monthly Savings Rate)")
    
    total_inc = cash_df["رقم (₹)"].sum() if not cash_df.empty else 0.0
    total_exp = exp_df["رقم (₹)"].sum() if not exp_df.empty else 0.0
    savings_rate = ((total_inc - total_exp) / total_inc * 100) if total_inc > 0 else 0.0

    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1:
        st.metric("کل آمدن", f"₹{total_inc:,.0f}")
    with col_an2:
        st.metric("کل اخراجات", f"₹{total_exp:,.0f}")
    with col_an3:
        st.metric("بچت کی شرح (Savings Rate)", f"{savings_rate:.1f}%")

    # آمدن اور خرچ کا تقابل
    comp_df = pd.DataFrame({
        "رقم (₹)": [total_inc, total_exp, max(total_inc - total_exp, 0.0)]
    }, index=["کل کمائی", "کل اخراجات", "خالص بچت"])
    st.bar_chart(comp_df)

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 گولڈ اور دیگر اثاثے")
    asset_mode = st.radio("شامل کرنے کا طریقہ:", ["گولڈ گرام کیلکولیٹر", "دیگر اثاثے"], horizontal=True)

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("تاریخ", value=date.today(), key="asset_date")
        
        if asset_mode == "گولڈ گرام کیلکولیٹر":
            with col2:
                gold_purity = st.selectbox("خالص پن", ["24K (خالص سونا)", "22K (زیورات)", "چاندی (Silver)"])
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                grams = st.number_input("وزن (گرام میں):", min_value=0.1, value=10.0, step=0.5)
            with c_g2:
                rate_per_gram = st.number_input("فی 1 گرام ریٹ (₹):", min_value=100.0, value=7500.0, step=50.0)
            calc_val = grams * rate_per_gram
            st.info(f"💡 کل مالیت: **₹{calc_val:,.0f}**")
            asset_type = f"Gold ({gold_purity})" if "2" in gold_purity else "Silver"
            final_val = calc_val
            final_qty = grams
            asset_note = st.text_input("نوٹ:", value=f"{grams}g @ ₹{rate_per_gram}/g")
        else:
            with col2:
                asset_type = st.selectbox("اثاثہ کی قسم", ["زمین / پلاٹ", "مکان / فلیٹ", "شیئرز / میوچل فنڈ", "دیگر اثاثے"])
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                final_val = st.number_input("کل قیمت (₹):", min_value=1000.0, step=5000.0)
            with c_m2:
                final_qty = st.number_input("مقدار:", min_value=1.0, value=1.0, step=1.0)
            asset_note = st.text_input("تفصیل:", value="طویل مدتی اثاثہ")

        submit_asset = st.form_submit_button("💾 اثاثہ محفوظ کریں")
        if submit_asset and final_val > 0:
            cursor.execute("INSERT INTO assets_history (entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?)",
                           (str(asset_date), asset_type, final_qty, final_val, asset_note))
            conn.commit()
            st.success("اثاثہ شامل کر دیا گیا!")
            st.rerun()

    asset_df = pd.read_sql_query("SELECT id, entry_date as 'تاریخ', asset_type as 'قسم', quantity as 'مقدار', current_value as 'قیمت (₹)', note as 'تفصیل' FROM assets_history ORDER BY id DESC", conn)
    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ اثاثہ اینٹری ڈیلیٹ کریں"):
            del_asset_id = st.selectbox("اثاثہ منتخب کریں:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'قسم'].values[0]} (₹{asset_df.loc[asset_df['id']==x, 'قیمت (₹)'].values[0]:,.0f})")
            if st.button("❌ اثاثہ حذف کریں"):
                cursor.execute("DELETE FROM assets_history WHERE id = ?", (del_asset_id,))
                conn.commit()
                st.rerun()

# حساب کتاب
total_gross_income = cash_df["رقم (₹)"].sum() if not cash_df.empty else 0.0
total_expenses = exp_df["رقم (₹)"].sum() if not exp_df.empty else 0.0
total_net_cash = max(total_gross_income - total_expenses, 0.0)
total_assets = asset_df["قیمت (₹)"].sum() if not asset_df.empty else 0.0
total_networth = total_net_cash + total_assets

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("کل کمائی", f"₹{total_gross_income:,.0f}")
    with col_m2:
        st.metric("کل اخراجات", f"₹{total_expenses:,.0f}")
    with col_m3:
        st.metric("خالص نقد بچت", f"₹{total_net_cash:,.0f}")
    with col_m4:
        st.metric("کل نیٹ ورتھ 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 100 کروڑ ہدف کی پیش رفت: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 کروڑ مکمل ہونے میں ابھی ₹{TARGET - total_networth:,.0f} باقی ہیں۔")

    if total_networth > 0:
        st.write("### 🍰 اثاثوں کی تقسیم (Asset Allocation)")
        chart_summary = pd.DataFrame({"رقم (₹)": [total_net_cash, total_assets]}, index=["خالص کیش", "گولڈ و اثاثے"])
        st.bar_chart(chart_summary)

    st.divider()
    st.subheader("⚡ 100 کروڑ رفتار کیلکولیٹر")
    daily_avg = cash_df["رقم (₹)"].mean() if not cash_df.empty else 0.0
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.write(f"**اوسط روزانہ کمائی:** ₹{daily_avg:,.0f}/دن")
        if daily_avg > 0:
            years_needed = ((TARGET - total_networth) / daily_avg) / 365
            st.write(f"موجودہ رفتار سے وقت درکار: **{years_needed:.1f} سال**")
        else:
            st.write("موجودہ رفتار سے وقت درکار: -- سال")
    with col_v2:
        target_years = st.selectbox("ہدف کا دورانیہ منتخب کریں:", [10, 15, 20, 25, 30], index=1)
        req_month = (TARGET - total_networth) / (target_years * 12)
        st.write(f"**{target_years} سال میں 100 کروڑ کے لیے:**")
        st.write(f"ماہانہ خالص بچت درکار: **₹{req_month:,.0f}/ماہ**")

    # PDF رپورٹ ڈاؤن لوڈ
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
        label="📥 ویلتھ آڈٹ PDF رپورٹ حاصل کریں",
        data=generate_wealth_pdf(),
        file_name=f"Wealth_Report_{date.today()}.pdf",
        mime="application/pdf"
    )

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 دولت کے مراحل (Wealth Milestones)")
    milestones = [
        ("پہلا مرحلہ: 10 لاکھ", 1000000),
        ("دوسرا مرحلہ: 50 لاکھ", 5000000),
        ("تیسرا مرحلہ: 1 کروڑ", 10000000),
        ("چوتھا مرحلہ: 5 کروڑ", 50000000),
        ("پانچواں مرحلہ: 10 کروڑ", 100000000),
        ("چھٹا مرحلہ: 50 کروڑ", 500000000),
        ("حتمی ہدف: 100 کروڑ 👑", 1000000000),
    ]
    for name, target_amt in milestones:
        if total_networth >= target_amt:
            st.success(f"✅ **{name}** — مکمل ہو گیا! (₹{target_amt:,.0f})")
        else:
            diff = target_amt - total_networth
            pct = min((total_networth / target_amt) * 100, 100.0)
            st.warning(f"⏳ **{name}** — `{pct:.2f}%` مکمل (بقایا رقم: ₹{diff:,.0f})")

    st.divider()
    st.subheader("⚡ کمپاؤنڈنگ سمیلیٹر")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        monthly_invest = st.number_input("ماہانہ سرمایہ کاری (₹):", min_value=1000, value=25000, step=5000)
    with col_s2:
        annual_rate = st.slider("سالانہ متوقع منافع (%):", min_value=8.0, max_value=25.0, value=15.0, step=0.5)

    years_list = list(range(1, 31))
    future_values = []
    r = (annual_rate / 100) / 12
    for yr in years_list:
        n = yr * 12
        fv = monthly_invest * (((1 + r)**n - 1) / r) * (1 + r) + (total_networth * ((1 + annual_rate/100)**yr))
        future_values.append(round(fv))
    st.line_chart(pd.DataFrame({"متوقع نیٹ ورتھ (₹)": future_values}, index=[f"سال {y}" for y in years_list]))

# ----------------- TAB 5: DISCIPLINE -----------------
with tab5:
    st.subheader("🔥 مالی تسلسل اور روزانہ ہدف")
    quotes = [
        "\"امیر بننے کا آغاز روزانہ کے چھوٹے مگر سخت مالی نظم و ضبط سے ہوتا ہے۔\"",
        "\"مالی آزادی موجودہ دکھاوے کی قربانی مانگتی ہے۔\""
    ]
    st.info(f"💡 {random.choice(quotes)}")

    today_str = str(date.today())
    today_savings = 0.0
    if not cash_df.empty:
        today_rows = cash_df[cash_df["تاریخ"] == today_str]
        today_savings = today_rows["رقم (₹)"].sum()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        daily_target = st.number_input("آج کا بچت ہدف (₹):", min_value=500, value=2000, step=500)
    with col_d2:
        st.metric("آج کی کمائی", f"₹{today_savings:,.0f}")

    daily_prog = min(today_savings / daily_target, 1.0)
    st.progress(daily_prog)

# ----------------- TAB 6: VISION -----------------
with tab6:
    st.subheader("👑 100 کروڑ ایلیٹ مائنڈ سیٹ")
    st.markdown("""
    * **اخراجات پر مکمل کنٹرول:** آمدن بڑھنے کے ساتھ دکھاوے کے اخراجات ہرگز نہ بڑھائیں۔
    * **کیش کو اثاثوں میں بدلیں:** نقد رقم کو محفوظ سونے، زمین یا منافع بخش کاروبار میں منتقل کرتے رہیں۔
    * **کمپاؤنڈنگ کا صبر:** دولت ایک طویل اور مستقل سفر کا نام ہے۔
    """)
