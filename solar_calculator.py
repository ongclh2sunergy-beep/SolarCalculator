import streamlit as st
from fpdf import FPDF
from PIL import Image
import io

# --- page-wide light yellow background ---
st.markdown(
    """
    <style>
      /* 1) keep the overall app light yellow */
      .stApp {
        background-color: #ffffe0 !important;
      }
      /* 2) target only the form wrapper to make it white */
      .stApp .stForm {
        background-color: white !important;
        padding: 16px !important;
        border-radius: 8px !important;
      }
      /* 3) ensure the text‐input itself is white */
      .stApp .stTextInput>div>input,
      .stApp .stNumberInput>div>input {
        background-color: white !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# === CONSTANTS ===
TARIFF_MYR_PER_KWH   = 0.63
SUNLIGHT_HOURS       = 3.62       # avg sun hrs/day
PANEL_WATT           = 615        # W per panel
SYSTEM_LIFE_YEARS    = 25         # yrs

PRICE_TABLE = {
    10: 21000,
    14: 26000,
    20: 34000,
    30: 43000,
    40: 52000
}

O_AND_M_PER_YEAR    = 800        # RM/year
MICROINV_UNITS      = 5.0        # units

# === CALCULATION FUNCTION ===
def generate_calculations(bill_myr, no_sun_days, package_panels):
    # 1) Adjusted sun hours
    sunny_days = 30 - no_sun_days
    adjusted_sun = (
        sunny_days * SUNLIGHT_HOURS +
        no_sun_days * SUNLIGHT_HOURS * 0.1
    ) / 30

    # 2) Usage & generation
    monthly_kwh      = bill_myr / TARIFF_MYR_PER_KWH
    kwp_installed    = package_panels * PANEL_WATT / 1000
    annual_gen_kwh   = kwp_installed * adjusted_sun * 365
    monthly_gen_kwh  = annual_gen_kwh / 12
    kwac             = kwp_installed * 0.77

    # 3) Daytime consumption (20%)
    daytime_need      = monthly_kwh * 0.20
    used_day_kwh      = min(monthly_gen_kwh, daytime_need)
    offset_kwh        = monthly_gen_kwh - used_day_kwh

    # 4) NEW PRICING LOGIC (no more PRICE_TABLE lookup)
    cash_price_map = {
        10: 19000,
        11: 20000,
        12: 21000,
        13: 22000,
        14: 24000,
        20: 32000,
        30: 41000
    }
    # pick the highest tier ≤ package_panels
    for tier in sorted(cash_price_map.keys(), reverse=True):
        if package_panels >= tier:
            base_tier = tier
            break

    cost_cash = cash_price_map[base_tier] + (package_panels - base_tier) * 1000
    cost_cc   = cost_cash + 2000
    print(cost_cash)
    print(cost_cc)
    # 5) Financials
    monthly_save   = offset_kwh * TARIFF_MYR_PER_KWH
    yearly_save    = monthly_save * 12
    payback_cc     = cost_cc   / yearly_save  if yearly_save else 0
    payback_cash   = cost_cash / yearly_save  if yearly_save else 0
    lifetime_sav   = yearly_save * SYSTEM_LIFE_YEARS
    roi_cc_pct     = (lifetime_sav - cost_cc)   / cost_cc   * 100
    roi_cash_pct   = (lifetime_sav - cost_cash) / cost_cash * 100
    new_monthly    = bill_myr - monthly_save

    # 6) Environmental
    total_fossil = kwp_installed * 350
    total_trees  = kwp_installed * 2
    total_co2    = kwp_installed * 0.85

    return {
        "monthly_save":   monthly_save,
        "yearly_save":    yearly_save,
        "payback_cc":     payback_cc,
        "payback_cash":   payback_cash,
        "roi_cc":         roi_cc_pct,
        "roi_cash":       roi_cash_pct,
        "new_monthly":    new_monthly,
        "kwp_installed":  kwp_installed,
        "monthly_gen":    monthly_gen_kwh,
        "kwac":           kwac,
        "cost_cc":        cost_cc,
        "cost_cash":      cost_cash,
        "total_fossil":   total_fossil,
        "total_trees":    total_trees,
        "total_co2":      total_co2
    }

# === PDF GENERATOR ===
def build_pdf(bill, raw_needed, pkg, c, no_sun_days):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Solar Savings Report", ln=1, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Monthly Bill: MYR {bill:.2f}", ln=1)
    pdf.cell(0, 8, f"No-Sun Days/Month: {no_sun_days}", ln=1)
    pdf.cell(0, 8, f"Panels Needed: {raw_needed}", ln=1)
    pdf.cell(0, 8, f"Package Qty: {pkg}", ln=1)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Key Metrics", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"New Bill After Solar: MYR {c['new_monthly']:.2f}", ln=1)
    pdf.cell(0, 8, f"Monthly Savings: MYR {c['monthly_save']:.2f}", ln=1)
    pdf.cell(0, 8, f"Payback (CC): {c['payback_cc']:.2f} yrs", ln=1)
    pdf.cell(0, 8, f"Payback (Cash): {c['payback_cash']:.2f} yrs", ln=1)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Financial Summary", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"ROI (CC): {c['roi_cc']:.2f}%", ln=1)
    pdf.cell(0, 8, f"ROI (Cash): {c['roi_cash']:.2f}%", ln=1)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Environmental Benefits", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Fossil Fuel Saved: {c['total_fossil']:.2f} kg", ln=1)
    pdf.cell(0, 8, f"Trees Saved: {c['total_trees']:.2f}", ln=1)
    pdf.cell(0, 8, f"CO2 Avoided: {c['total_co2']:.2f} t", ln=1)

    # Return PDF as BytesIO
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_bytes)

def main():
    st.title("☀️ Solar Savings Calculator")

    if 'calculated' not in st.session_state:
        st.session_state.calculated = False

    # === two columns: left for image, right for form ===
    col_img, col_form = st.columns([1, 1])

    # -- LEFT: your image --
    with col_img:
        st.image(
            "https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=1172&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            width=400,    # <-- adjust this to whatever width you like
            caption=None
        )

    # -- RIGHT: your input form --
    with col_form:
        with st.form("solar_form"):
            bill_input = st.text_input("Monthly Electricity Bill (MYR):")
            submitted  = st.form_submit_button("Calculate")

        # do your parsing / state logic immediately under the form
        try:
            bill_val = float(bill_input)
        except:
            bill_val = None

    if submitted:
        if bill_val and bill_val > 0:
            st.session_state.calculated = True
            st.session_state.bill = bill_val
        else:
            st.warning("Please enter a positive number.")

    if st.session_state.calculated:
        bill = st.session_state.bill

        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            no_sun_days = st.selectbox("No-sun days per month:", [0,15,30], index=0)

        # Panel package selection
        st.subheader("📦 Solar Panel Package Selection")
        
        # 1) recommend based on kWp as before
        allowed = list(range(10, 41))
        rec_kwh     = bill / TARIFF_MYR_PER_KWH
        rec_kwp     = rec_kwh / (SUNLIGHT_HOURS * 30)
        raw_needed  = int(-(-rec_kwp*1000 // PANEL_WATT))
        recommended = min(max(raw_needed, 10), 40)

        # 2) slider 10→40
        pkg = st.slider(
            "Number of panels:",
            min_value=10,
            max_value=40,
            step=1,
            value=recommended
        )

        # 3) cash-price map for the “special” tiers
        cash_price_map = {
            10: 19000,
            11: 20000,
            12: 21000,
            13: 22000,
            14: 24000,
            20: 32000,
            30: 41000
        }

        # 4) find the base tier (highest key ≤ pkg) and compute cash/CC price
        for tier in sorted(cash_price_map.keys(), reverse=True):
            if pkg >= tier:
                base_tier = tier
                break

        cost_cash = cash_price_map[base_tier] + (pkg - base_tier) * 1000
        cost_cc   = cost_cash + 2000

        # 5) run your generation logic…
        c = generate_calculations(bill, no_sun_days, pkg)

        # 6) override the cost/payback/ROI fields
        lifetime_sav      = c["yearly_save"] * SYSTEM_LIFE_YEARS
        c["cost_cash"]    = cost_cash
        c["cost_cc"]      = cost_cc
        c["payback_cash"] = cost_cash / c["yearly_save"] if c["yearly_save"] else 0
        c["payback_cc"]   = cost_cc   / c["yearly_save"] if c["yearly_save"] else 0
        c["roi_cash"]     = (lifetime_sav - cost_cash) / cost_cash * 100
        c["roi_cc"]       = (lifetime_sav - cost_cc)   / cost_cc   * 100

        
        # Inject card CSS
        st.markdown("""
        <style>
          .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px,1fr));
            gap: 12px;
            margin: 16px 0;
          }
          .card {
            background: #fff;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
          }
          .card .title { font-size:0.8rem; color:#666; margin-bottom:4px; }
          .card .value { font-size:1.1rem; font-weight:600; color:#222; }
        </style>
        """, unsafe_allow_html=True)

        # === KEY METRICS ===
        st.subheader("📈 Key Metrics")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Previous Bill</div><div class="value">RM {bill:.2f}</div></div>
          <div class="card"><div class="title">New Bill</div><div class="value">RM {c['new_monthly']:.2f}</div></div>
          <div class="card"><div class="title">Payback (CC)</div><div class="value">{c['payback_cc']:.2f} yrs</div></div>
          <div class="card"><div class="title">Payback (Cash)</div><div class="value">{c['payback_cash']:.2f} yrs</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === PANEL & SAVINGS SUMMARY ===
        st.subheader("🔧 Panel & Savings Summary")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Panels Needed</div><div class="value">{raw_needed} panels</div></div>
          <div class="card"><div class="title">Package Qty</div><div class="value">{pkg} panels</div></div>
          <div class="card"><div class="title">Saving per PV</div><div class="value">RM {c['monthly_save']/pkg:.2f}</div></div>
          <div class="card"><div class="title">Installed kWp</div><div class="value">{c['kwp_installed']:.2f} kWp</div></div>
          <div class="card"><div class="title">kWac</div><div class="value">{c['kwac']:.2f} kW</div></div>
          <div class="card"><div class="title">Price (CC)</div><div class="value">RM {c['cost_cc']:.2f}</div></div>
          <div class="card"><div class="title">Price (Cash)</div><div class="value">RM {c['cost_cash']:.2f}</div></div>
          <div class="card"><div class="title">O&M (Annual)</div><div class="value">RM {O_AND_M_PER_YEAR:.2f}</div></div>
          <div class="card"><div class="title">Microinverters</div><div class="value">{MICROINV_UNITS:.2f} units</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === FINANCIAL SUMMARY (with ROI) ===
        st.subheader("💰 Financial Summary")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Total Sav/Month</div><div class="value">RM {c['monthly_save']:.2f}</div></div>
          <div class="card"><div class="title">Total Sav/Year</div><div class="value">RM {c['yearly_save']:.2f}</div></div>
          <div class="card"><div class="title">Payback (CC)</div><div class="value">{c['payback_cc']:.2f} yrs</div></div>
          <div class="card"><div class="title">Payback (Cash)</div><div class="value">{c['payback_cash']:.2f} yrs</div></div>
          <div class="card"><div class="title">ROI (CC)</div><div class="value">{c['roi_cc']:.2f}%</div></div>
          <div class="card"><div class="title">ROI (Cash)</div><div class="value">{c['roi_cash']:.2f}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === ENVIRONMENTAL BENEFITS ===
        st.subheader("🌳 Environmental Benefits")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Fossil Fuel /1 kWp</div><div class="value">350 kg</div></div>
          <div class="card"><div class="title">Trees /1 kWp</div><div class="value">2</div></div>
          <div class="card"><div class="title">CO₂ /1 kWp</div><div class="value">0.85 t</div></div>
          <div class="card"><div class="title">Total Fossil</div><div class="value">{c['total_fossil']:.2f} kg</div></div>
          <div class="card"><div class="title">Total Trees</div><div class="value">{c['total_trees']:.2f}</div></div>
          <div class="card"><div class="title">Total CO₂</div><div class="value">{c['total_co2']:.2f} t</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === DOWNLOAD PDF BUTTON ===
        pdf_buffer = build_pdf(bill, raw_needed, pkg, c, no_sun_days)
        st.download_button(
            label="📄 Download Report as PDF",
            data=pdf_buffer,
            file_name="solar_savings_report.pdf",
            mime="application/pdf"
        )


if __name__ == "__main__":
    main()