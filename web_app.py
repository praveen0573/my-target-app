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

# --- Page Config ---
st.set_page_config(page_title="100 Crore Wealth Hub", page_icon="👑", layout="centered")

# --- Security PIN ---
SECRET_PIN = "1234"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 100 Crore Wealth Vault")
    st.caption("Surakshit financial hub me login karein.")
    pin_input = st.text_input("4-digit secret PIN dalein:", type="password")
    if st.button("Unlock Dashboard 🔓", type="primary"):
        if pin_input == SECRET_PIN:
            st.session_state["authenticated"] = True
            st.success("Unlocked successfully!")
            st.rerun()
        else:
            st.error("Galat PIN! Sahi PIN dalein.")
    st.stop()

# --- Sidebar Theme Switcher ---
with st.sidebar:
    st.title("🎨 Visual Customizer")
    theme_choice = st.selectbox(
        "Pasandida Theme Chunein:",
        ["🌟 Royal Gold Dark", "☀️ Classic Bright Light", "🌌 Deep Navy Blue", "🌿 Emerald Wealth"]
    )
    if st.button("Logout 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

# Theme CSS Colors
if theme_choice == "☀️ Classic Bright Light":
    bg_color = "#ffffff"
    text_color = "#111827"
    accent = "#b45309"
    tab_bg = "#f3f4f6"
    btn_bg = "#1d4ed8"
    btn_text = "#ffffff"
elif theme_choice == "🌌 Deep Navy Blue":
    bg_color = "#0a192f"
    text_color = "#f8fafc"
    accent = "#38bdf8"
    tab_bg = "#1e293b"
    btn_bg = "#38bdf8"
    btn_text = "#0f172a"
elif theme_choice == "🌿 Emerald Wealth":
    bg_color = "#06231a"
    text_color = "#f0fdf4"
    accent = "#4ade80"
    tab_bg = "#14532d"
    btn_bg = "#4ade80"
    btn_text = "#052e16"
else:  # Royal Gold Dark
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

# --- Database Setup ---
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

TARGET = 1000000000  # 100 Crore

st.title("👑 100 Crore Wealth Hub")
st.caption("Real-time Networth, Cashflow, Gold Assets & Debt Manager")

# Tabs
tab1, tab2, tab_exp, tab_debt, tab_analytics, tab3, tab4, tab_blueprint, tab5 = st.tabs([
    "📊 Dashboard", 
    "💵 Income", 
    "💸 Expenses",
    "⚖️ Debt / Loan",
    "📈 Savings Rate", 
    "🥇 Gold & Assets", 
    "🚀 100 Cr Roadmap",
    "⚡ Blueprint",
    "🔥 Streaks"
])

# ----------------- TAB 2: INCOME -----------------
with tab2:
    with st.form("cash_form", clear_on_submit=True):
        st.subheader("📝 Record Income")
        col_a, col_b = st.columns(2)
        with col_a:
            entry_date = st.date_input("Date", value=date.today(), key="cash_date")
        with col_b:
            daily_income = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
        
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            income_category = st.selectbox("Category", [
                "Business", "Daily Savings", "Trading/Investments", "Side Hustle", "Other"
            ])
        with col_cat2:
            custom_note = st.text_input("Note", value="")
        
        final_note = f"[{income_category}] {custom_note}".strip()
        submit_cash = st.form_submit_button("💾 Save Income")

        if submit_cash and daily_income > 0:
            cursor.execute("INSERT INTO income_history (entry_date, daily_amount, note) VALUES (?, ?, ?)",
                           (str(entry_date), daily_income, final_note))
            conn.commit()
            st.success(f"₹{daily_income:,.0f} added!")
            st.rerun()

    cash_df = pd.read_sql_query("SELECT id, entry_date as 'Date', daily_amount as 'Amount (₹)', note as 'Description' FROM income_history ORDER BY id DESC", conn)
    if not cash_df.empty:
        st.dataframe(cash_df.drop(columns=["id"]), use_container_width=True)
        csv_cash = cash_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Income CSV", data=csv_cash, file_name="income_records.csv", mime="text/csv")
        with st.expander("🗑️ Delete Income Entry"):
            del_id = st.selectbox("Select entry:", options=cash_df["id"].tolist(),
                                  format_func=lambda x: f"ID {x} - ₹{cash_df.loc[cash_df['id']==x, 'Amount (₹)'].values[0]:,.0f}")
            if st.button("❌ Delete Income"):
                cursor.execute("DELETE FROM income_history WHERE id = ?", (del_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB: EXPENSES -----------------
with tab_exp:
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("💸 Record Daily Expense")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            exp_date = st.date_input("Date", value=date.today(), key="exp_date")
            exp_cat = st.selectbox("Category", ["Essentials", "Travel/Fuel", "Food/Groceries", "Business Costs", "Discretionary"])
        with col_e2:
            exp_amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            exp_note = st.text_input("Note", value="")
        submit_exp = st.form_submit_button("💾 Save Expense")

        if submit_exp and exp_amt > 0:
            cursor.execute("INSERT INTO expense_history (entry_date, amount, category, note) VALUES (?, ?, ?, ?)",
                           (str(exp_date), exp_amt, exp_cat, exp_note))
            conn.commit()
            st.warning(f"₹{exp_amt:,.0f} expense recorded!")
            st.rerun()

    exp_df = pd.read_sql_query("SELECT id, entry_date as 'Date', amount as 'Amount (₹)', category as 'Category', note as 'Note' FROM expense_history ORDER BY id DESC", conn)
    if not exp_df.empty:
        st.dataframe(exp_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Expense Entry"):
            del_exp_id = st.selectbox("Select expense:", options=exp_df["id"].tolist(),
                                      format_func=lambda x: f"ID {x} - ₹{exp_df.loc[exp_df['id']==x, 'Amount (₹)'].values[0]:,.0f}")
            if st.button("❌ Delete Expense"):
                cursor.execute("DELETE FROM expense_history WHERE id = ?", (del_exp_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB: DEBT / LOAN -----------------
with tab_debt:
    st.subheader("⚖️ Debt & Udhaar Manager")
    with st.form("debt_form", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            d_date = st.date_input("Date", value=date.today(), key="debt_date")
            debt_type = st.radio("Type", ["Mera Karz (Mujhe Dena Hai - Liability)", "Mera Paisa Bahar Hai (Mujhe Lena Hai - Asset)"])
        with col_d2:
            d_person = st.text_input("Person / Bank Name", value="")
            d_amount = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
        d_note = st.text_input("Reason / Deadline", value="")
        submit_debt = st.form_submit_button("💾 Save Debt Record")

        if submit_debt and d_amount > 0:
            cursor.execute("INSERT INTO debt_history (entry_date, debt_type, person_name, amount, note) VALUES (?, ?, ?, ?, ?)",
                           (str(d_date), debt_type, d_person, d_amount, d_note))
            conn.commit()
            st.success("Debt record saved!")
            st.rerun()

    debt_df = pd.read_sql_query("SELECT id, entry_date as 'Date', debt_type as 'Type', person_name as 'Party', amount as 'Amount (₹)', note as 'Note' FROM debt_history ORDER BY id DESC", conn)
    if not debt_df.empty:
        st.dataframe(debt_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Debt Entry"):
            del_debt_id = st.selectbox("Select record:", options=debt_df["id"].tolist(),
                                       format_func=lambda x: f"ID {x} - ₹{debt_df.loc[debt_df['id']==x, 'Amount (₹)'].values[0]:,.0f}")
            if st.button("❌ Delete Debt"):
                cursor.execute("DELETE FROM debt_history WHERE id = ?", (del_debt_id,))
                conn.commit()
                st.rerun()

# ----------------- TAB: ANALYTICS & BUDGET -----------------
with tab_analytics:
    st.subheader("📈 Savings Rate Analysis")
    total_inc = cash_df["Amount (₹)"].sum() if not cash_df.empty else 0.0
    total_exp = exp_df["Amount (₹)"].sum() if not exp_df.empty else 0.0
    savings_rate = ((total_inc - total_exp) / total_inc * 100) if total_inc > 0 else 0.0

    col_an1, col_an2, col_an3 = st.columns(3)
    with col_an1:
        st.metric("Total Income", f"₹{total_inc:,.0f}")
    with col_an2:
        st.metric("Total Expenses", f"₹{total_exp:,.0f}")
    with col_an3:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")

    comp_df = pd.DataFrame({
        "Amount (₹)": [total_inc, total_exp, max(total_inc - total_exp, 0.0)]
    }, index=["Income", "Expenses", "Net Savings"])
    st.bar_chart(comp_df)

# ----------------- TAB 3: GOLD & ASSETS -----------------
with tab3:
    st.subheader("🥇 Gold & Real Assets")
    asset_mode = st.radio("Add Method:", ["Gold Calculator (Gram based)", "Other Physical Asset"], horizontal=True)

    with st.form("asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asset_date = st.date_input("Date", value=date.today(), key="asset_date")
        
        if asset_mode == "Gold Calculator (Gram based)":
            with col2:
                gold_purity = st.selectbox("Purity", ["24K (99.9% Pure)", "22K (Jewellery)", "Silver"])
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                grams = st.number_input("Grams:", min_value=0.1, value=10.0, step=0.5)
            with c_g2:
                rate_per_gram = st.number_input("Rate per gram (₹):", min_value=100.0, value=7500.0, step=50.0)
            calc_val = grams * rate_per_gram
            st.info(f"Estimated Value: **₹{calc_val:,.0f}**")
            asset_type = f"Gold ({gold_purity})" if "2" in gold_purity else "Silver"
            final_val = calc_val
            final_qty = grams
            asset_note = st.text_input("Description:", value=f"{grams}g @ ₹{rate_per_gram}/g")
        else:
            with col2:
                asset_type = st.selectbox("Type", ["Land / Plot", "Commercial / Property", "Stocks / Equity", "Other Assets"])
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                final_val = st.number_input("Total Valuation (₹):", min_value=1000.0, step=5000.0)
            with c_m2:
                final_qty = st.number_input("Units / Qty:", min_value=1.0, value=1.0, step=1.0)
            asset_note = st.text_input("Note:", value="Long term asset")

        submit_asset = st.form_submit_button("💾 Save Asset")
        if submit_asset and final_val > 0:
            cursor.execute("INSERT INTO assets_history (entry_date, asset_type, quantity, current_value, note) VALUES (?, ?, ?, ?, ?)",
                           (str(asset_date), asset_type, final_qty, final_val, asset_note))
            conn.commit()
            st.success("Asset recorded!")
            st.rerun()

    asset_df = pd.read_sql_query("SELECT id, entry_date as 'Date', asset_type as 'Type', quantity as 'Qty', current_value as 'Value (₹)', note as 'Note' FROM assets_history ORDER BY id DESC", conn)
    if not asset_df.empty:
        st.dataframe(asset_df.drop(columns=["id"]), use_container_width=True)
        with st.expander("🗑️ Delete Asset Entry"):
            del_asset_id = st.selectbox("Select asset:", options=asset_df["id"].tolist(),
                                        format_func=lambda x: f"ID {x} - {asset_df.loc[asset_df['id']==x, 'Type'].values[0]} (₹{asset_df.loc[asset_df['id']==x, 'Value (₹)'].values[0]:,.0f})")
            if st.button("❌ Delete Asset"):
                cursor.execute("DELETE FROM assets_history WHERE id = ?", (del_asset_id,))
                conn.commit()
                st.rerun()

# Calculations
total_gross_income = cash_df["Amount (₹)"].sum() if not cash_df.empty else 0.0
total_expenses = exp_df["Amount (₹)"].sum() if not exp_df.empty else 0.0
total_net_cash = max(total_gross_income - total_expenses, 0.0)
total_assets = asset_df["Value (₹)"].sum() if not asset_df.empty else 0.0

total_liabilities = 0.0
total_receivables = 0.0
if not debt_df.empty:
    liab_rows = debt_df[debt_df["Type"].str.contains("Liability")]
    rec_rows = debt_df[debt_df["Type"].str.contains("Asset")]
    total_liabilities = liab_rows["Amount (₹)"].sum()
    total_receivables = rec_rows["Amount (₹)"].sum()

# Shuddh Networth: Cash + Assets + Lena hai - Dena hai
total_networth = max(total_net_cash + total_assets + total_receivables - total_liabilities, 0.0)

# ----------------- TAB 1: TOTAL DASHBOARD -----------------
with tab1:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Net Cash", f"₹{total_net_cash:,.0f}")
    with col_m2:
        st.metric("Gold & Assets", f"₹{total_assets:,.0f}")
    with col_m3:
        st.metric("Liabilities (Karz)", f"₹{total_liabilities:,.0f}")
    with col_m4:
        st.metric("Clean Networth 👑", f"₹{total_networth:,.0f}")

    progress_val = min(total_networth / TARGET, 1.0)
    st.write(f"### 🎯 Target Progress: `{progress_val * 100:.6f}%`")
    st.progress(progress_val)
    st.info(f"💡 100 Crore Target Remaining: ₹{TARGET - total_networth:,.0f}")

    if total_networth > 0:
        st.write("### 🍰 Asset Allocation Breakdown")
        chart_summary = pd.DataFrame({"Value (₹)": [total_net_cash, total_assets, total_receivables]}, 
                                     index=["Cash", "Physical Assets", "Receivables"])
        st.bar_chart(chart_summary)

    # Speed Meter
    st.divider()
    st.subheader("⚡ 100 Crore Velocity Meter")
    daily_avg = cash_df["Amount (₹)"].mean() if not cash_df.empty else 0.0
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.write(f"**Average Daily Run Rate:** ₹{daily_avg:,.0f}/day")
        if daily_avg > 0:
            years_needed = ((TARGET - total_networth) / daily_avg) / 365
            st.write(f"Years required at current pace: **{years_needed:.1f} years**")
        else:
            st.write("Years required: --")
    with col_v2:
        target_years = st.selectbox("Target Horizon (Years):", [10, 15, 20, 25, 30], index=1)
        req_month = (TARGET - total_networth) / (target_years * 12)
        st.write(f"**To hit ₹100 Cr in {target_years} years:**")
        st.write(f"Monthly clean savings required: **₹{req_month:,.0f}/month**")

    # PDF Report
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
            ["Total Liabilities", f"Rs. {total_liabilities:,.0f}", "Debt Outflow"],
            ["Target Remaining", f"Rs. {TARGET - total_networth:,.0f}", "Goal: 100 Crore"]
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
        label="📥 Download Wealth Audit PDF Report",
        data=generate_wealth_pdf(),
        file_name=f"Wealth_Report_{date.today()}.pdf",
        mime="application/pdf"
    )

# ----------------- TAB 4: ROADMAP -----------------
with tab4:
    st.subheader("🪜 Wealth Milestones Ladder")
    milestones = [
        ("Step 1: 10 Lakh", 1000000),
        ("Step 2: 50 Lakh", 5000000),
        ("Step 3: 1 Crore", 10000000),
        ("Step 4: 5 Crore", 50000000),
        ("Step 5: 10 Crore", 100000000),
        ("Step 6: 50 Crore", 500000000),
        ("Final Target: 100 Crore 👑", 1000000000),
    ]
    for name, target_amt in milestones:
        if total_networth >= target_amt:
            st.success(f"✅ **{name}** — Reached! (₹{target_amt:,.0f})")
        else:
            diff = target_amt - total_networth
            pct = min((total_networth / target_amt) * 100, 100.0)
            st.warning(f"⏳ **{name}** — `{pct:.2f}%` done (₹{diff:,.0f} to go)")

    st.divider()
    st.subheader("⚡ Compounding Simulator")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        monthly_invest = st.number_input("Monthly Investment (₹):", min_value=1000, value=25000, step=5000)
    with col_s2:
        annual_rate = st.slider("Expected Return (% p.a.):", min_value=8.0, max_value=25.0, value=15.0, step=0.5)

    years_list = list(range(1, 31))
    future_values = []
    r = (annual_rate / 100) / 12
    for yr in years_list:
        n = yr * 12
        fv = monthly_invest * (((1 + r)**n - 1) / r) * (1 + r) + (total_networth * ((1 + annual_rate/100)**yr))
        future_values.append(round(fv))
    st.line_chart(pd.DataFrame({"Projected Networth (₹)": future_values}, index=[f"Year {y}" for y in years_list]))

# ----------------- TAB: BLUEPRINT -----------------
with tab_blueprint:
    st.subheader("⚡ 100 Crore Reverse Math Engine")
    blueprint_table = [
        {"Ticket Size": "₹1,000 Volume Product", "Required Sales/Clients": "10,00,000 buyers", "Total": "₹100 Crore"},
        {"Ticket Size": "₹10,000 High-Demand Tool/Course", "Required Sales/Clients": "1,00,000 buyers", "Total": "₹100 Crore"},
        {"Ticket Size": "₹50,000 Retainer / Agency Client", "Required Sales/Clients": "20,000 buyers", "Total": "₹100 Crore"},
        {"Ticket Size": "₹1,00,000 High-Ticket Enterprise", "Required Sales/Clients": "10,000 buyers", "Total": "₹100 Crore"}
    ]
    st.dataframe(pd.DataFrame(blueprint_table), use_container_width=True)

# ----------------- TAB 5: DISCIPLINE -----------------
with tab5:
    st.subheader("🔥 Daily Streak & Discipline")
    today_str = str(date.today())
    today_savings = 0.0
    if not cash_df.empty:
        today_rows = cash_df[cash_df["Date"] == today_str]
        today_savings = today_rows["Amount (₹)"].sum()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        daily_target = st.number_input("Today's Target (₹):", min_value=500, value=2000, step=500)
    with col_d2:
        st.metric("Today Saved", f"₹{today_savings:,.0f}")

    daily_prog = min(today_savings / daily_target, 1.0)
    st.progress(daily_prog)
