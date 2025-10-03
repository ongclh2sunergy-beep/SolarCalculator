import streamlit as st
from fpdf import FPDF
from PIL import Image
import io
import cronitor

# Initialize Cronitor with your API key
cronitor.api_key = "e8461f90b16b168b919ff56c008ac375"

# Example: Ping a monitor named "my-job"
monitor = cronitor.Monitor("my-job")

# Send start signal
monitor.ping(state="run")

# Do some work here...
print("Running some process...")

# Send complete signal
monitor.ping(state="complete")

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

def generate_calculations(
    bill_myr,
    no_sun_days,
    package_panels,
    use_daytime,
    sunlight_hours=SUNLIGHT_HOURS
):
    # 1) Adjusted sun hours
    sunny_days   = 30 - no_sun_days
    adjusted_sun = (
        sunny_days * sunlight_hours +
        no_sun_days * sunlight_hours * 0.1
    ) / 30

    # 2) Back-out their rough kWh/month from the bill
    approx_kwh = bill_myr / TARIFF_MYR_PER_KWH

    # 3) Choose the correct energy rate tier
    if approx_kwh <= 1500:
        energy_sen = 27.03
    else:
        energy_sen = 37.03

    # 4) Other tariff components
    capacity_sen = 4.55
    network_sen  = 12.85
    retail_rm    = 10.00

    # 5) Build the final unit rate in RM/kWh
    unit_rate = (energy_sen + capacity_sen + network_sen) / 100

    # Monthly energy per single panel:
    monthly_gen_per_pv = (PANEL_WATT / 1000) * sunlight_hours * 30

    # Saving per PV = monthly kWh per panel × your RM/kWh rate
    saving_per_pv = monthly_gen_per_pv * unit_rate

    # 6) Generation sizing (unchanged)
    monthly_kwh     = approx_kwh
    kwp_installed   = package_panels * PANEL_WATT / 1000
    annual_gen_kwh  = kwp_installed * adjusted_sun * 365
    monthly_gen_kwh = annual_gen_kwh / 12
    kwac            = kwp_installed * 0.77

    # 7) Daytime consumption toggle
    if use_daytime:
        daytime_need = monthly_kwh * 0.20
        used_day_kwh = min(monthly_gen_kwh, daytime_need)
        offset_kwh   = monthly_gen_kwh - used_day_kwh
    else:
        used_day_kwh = 0
        offset_kwh   = monthly_gen_kwh

    # 8) Panel pricing (tiered + fallback + CC)
    cash_price_map = {10:19000,11:20000,12:21000,13:22000,14:24000,20:32000,30:41000}
    for tier in sorted(cash_price_map, reverse=True):
        if package_panels >= tier:
            base_tier = tier
            break
    cost_cash = cash_price_map[base_tier] + (package_panels - base_tier) * 1000
    cost_cc   = cost_cash + 2000

    # 9) Financials using the true tariff + retail fee
    true_bill     = monthly_kwh * unit_rate + retail_rm
    monthly_save  = offset_kwh  * unit_rate
    yearly_save   = monthly_save * 12

    payback_cc    = cost_cc   / yearly_save  if yearly_save else 0
    payback_cash  = cost_cash / yearly_save  if yearly_save else 0
    lifetime_sav  = yearly_save * SYSTEM_LIFE_YEARS
    roi_cc_pct    = (lifetime_sav - cost_cc)   / cost_cc   * 100
    roi_cash_pct  = (lifetime_sav - cost_cash) / cost_cash * 100
    new_monthly   = true_bill   - monthly_save

    # 10) Environmental
    total_fossil = kwp_installed * 350
    total_trees  = kwp_installed * 2
    total_co2    = kwp_installed * 0.85

    return {
        "monthly_kwh":    monthly_kwh,
        "unit_rate":      unit_rate,
        "retail_charge":  retail_rm,
        "true_bill":      true_bill,
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
        "total_co2":      total_co2,
        "save_per_pv": saving_per_pv
    }

# === PDF GENERATOR ===
def build_pdf(bill, raw_needed, pkg, c, no_sun_days):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Solar Savings Report", ln=1, align="C")
    pdf.ln(4)

    # User inputs
    pdf.set_font("Helvetica", size=12)
    pdf.set_fill_color(240,240,240)
    pdf.cell(90, 8, "Monthly Bill (MYR)", border=1, fill=True)
    pdf.cell(90, 8, f"{bill:.2f}", border=1, ln=1)
    pdf.cell(90, 8, "No-Sun Days/Month", border=1, fill=True)
    pdf.cell(90, 8, f"{no_sun_days}", border=1, ln=1)
    pdf.cell(90, 8, "Panels Needed", border=1, fill=True)
    pdf.cell(90, 8, f"{raw_needed}", border=1, ln=1)
    pdf.cell(90, 8, "Package Qty", border=1, fill=True)
    pdf.cell(90, 8, f"{pkg}", border=1, ln=1)

    pdf.ln(6)
    # Key Metrics header
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Key Metrics", ln=1)
    pdf.set_font("Helvetica", size=12)
    colw = pdf.w/2 - 20

    # Row 1
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "Consumption (kWh/mo)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('monthly_kwh',0):.2f}", border=1, ln=1)
    # Row 2
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "Monthly Gen (kWh)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('monthly_gen',0):.2f}", border=1, ln=1)
    # Row 3
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "Unit Rate (RM/kWh)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('unit_rate',0):.2f}", border=1, ln=1)
    # Row 4
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "Retail Charge (RM/mo)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('retail_charge',0):.2f}", border=1, ln=1)
    # Row 5
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "Monthly Savings (RM)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('monthly_save',0):.2f}", border=1, ln=1)
    # Row 6
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "Saving per PV (RM)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('save_per_pv',0):.2f}", border=1, ln=1)
    # Row 7
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "O&M Fee (RM/mo)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('om_fee_monthly',0):.2f}", border=1, ln=1)
    # Row 8
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "New Bill After Solar (RM)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('new_monthly',0):.2f}", border=1, ln=1)

    pdf.ln(6)
    # Financial Summary header
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Financial Summary", ln=1)
    pdf.set_font("Helvetica", size=12)

    # Fin row 1
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "ROI (Cash)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('roi_cash',0):.2f}%", border=1, ln=1)
    # Fin row 2
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "ROI (CC)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('roi_cc',0):.2f}%", border=1, ln=1)
    # Fin row 3
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "Payback (Cash)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('payback_cash',0):.2f} yrs", border=1, ln=1)
    # Fin row 4
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "Payback (CC)", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('payback_cc',0):.2f} yrs", border=1, ln=1)
    # Fin row 5
    pdf.set_fill_color(245,245,245)
    pdf.cell(colw, 8, "3-Year Installment", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('inst_3yr',0):.2f}/mo", border=1, ln=1)
    # Fin row 6
    pdf.set_fill_color(255,255,255)
    pdf.cell(colw, 8, "5-Year Installment", border=1, fill=True)
    pdf.cell(colw, 8, f"{c.get('inst_5yr',0):.2f}/mo", border=1, ln=1)

    pdf.ln(6)
    # Environmental header
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Environmental Benefits", ln=1)
    pdf.set_font("Helvetica", size=12)

    pdf.set_fill_color(240,240,240)
    pdf.cell(90, 8, "Fossil Fuel Saved (kg)", border=1, fill=True)
    pdf.cell(90, 8, f"{c.get('total_fossil',0):.2f}", border=1, ln=1)
    pdf.cell(90, 8, "Trees Saved", border=1, fill=True)
    pdf.cell(90, 8, f"{c.get('total_trees',0):.2f}", border=1, ln=1)
    pdf.cell(90, 8, "CO2 Avoided (t)", border=1, fill=True)
    pdf.cell(90, 8, f"{c.get('total_co2',0):.2f}", border=1, ln=1)

    # Return PDF as BytesIO
    return io.BytesIO(pdf.output(dest='S').encode('latin-1'))

def main():
    st.title("☀️ Solar Savings Calculator")

    if 'calculated' not in st.session_state:
        st.session_state.calculated = False

    # === two columns: left for image, right for form ===
    col_img, col_form = st.columns([1, 1])

    # -- LEFT: your image --
    with col_img:
        st.image(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRvUrQzbNoJwW7pypHZ9yweCafrQtCWeKRjUg&s",
            width=400,    # <-- adjust this to whatever width you like
            caption=None
        )

    # -- RIGHT: your input form --
    with col_form:
        with st.form("solar_form"):
            bill_input = st.text_input(
                "Monthly Electricity Bill (MYR):",
                key="bill_input"
            )
            submitted = st.form_submit_button("Calculate")

        try:
            bill_val = float(bill_input)
        except:
            bill_val = None

        # ---- Handle buttons ----
        if submitted:
            if bill_val and bill_val > 0:
                st.session_state.calculated = True
                st.session_state.bill = bill_val
            else:
                st.warning("Please enter a positive number.")

            # 🔑 Clear the input after Calculate
            if "bill_input" in st.session_state:
                del st.session_state["bill_input"]
            st.rerun()


    if st.session_state.calculated:
        bill = st.session_state.bill

        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            no_sun_days = st.selectbox("No-sun days per month:", [0,15,30], index=0)
            use_daytime = st.checkbox("Enable daytime consumption (20%)", value=False)
            location     = st.selectbox(
                "Location:",
                ["Johor Bahru", "BP/Muar", "Kuala Lumpur", "North"]
            )

            # Map each choice to its peak sun hours
            area_sun_map = {
                "Johor Bahru":   3.42,
                "BP/Muar":       3.56,
                "Kuala Lumpur":  3.62,
                "North":         3.75
            }
            # grab the correct value for this run
            sunlight_hours = area_sun_map[location]

        # Panel package selection
        st.subheader("📦 Solar Panel Package Selection")
        
        # 1) recommend based on kWp as before
        allowed = list(range(10, 41))
        rec_kwh     = bill / TARIFF_MYR_PER_KWH
        rec_kwp     = rec_kwh / (sunlight_hours * 30)
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

        # 3-year (36 months) and 5-year (60 months) monthly payments
        inst_3yr = cost_cc / (3 * 12)
        inst_5yr = cost_cc / (5 * 12)

        # 5) run your generation logic…
        c = generate_calculations(
            bill_myr=bill,
            no_sun_days=no_sun_days,
            package_panels=pkg,
            use_daytime=use_daytime,
            sunlight_hours=sunlight_hours
        )

        # 6) override the cost/payback/ROI fields
        lifetime_sav      = c["yearly_save"] * SYSTEM_LIFE_YEARS
        c["cost_cash"]    = cost_cash
        c["cost_cc"]      = cost_cc
        c["payback_cash"] = cost_cash / c["yearly_save"] if c["yearly_save"] else 0
        c["payback_cc"]   = cost_cc   / c["yearly_save"] if c["yearly_save"] else 0
        c["roi_cash"]     = (lifetime_sav - cost_cash) / cost_cash * 100
        c["roi_cc"]       = (lifetime_sav - cost_cc)   / cost_cc   * 100
        c["inst_3yr"]     = inst_3yr
        c["inst_5yr"]     = inst_5yr
        c["save_per_pv"] = c["save_per_pv"]
        c["new_monthly"] = max(c["new_monthly"], 0)

        # ─── insert O&M rounding logic here ───
        raw_sav   = c["monthly_save"]
        rem       = raw_sav % 100
        base_hund = raw_sav - rem

        if rem > 40:
            om_fee = base_hund + 100
        else:
            om_fee = base_hund

        # clamp between 500 and 1000
        om_fee = max(500, min(om_fee, 1000))

        c["om_fee_monthly"] = om_fee

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
          <div class="card"><div class="title">Consumption</div><div class="value">{c['monthly_kwh']:.2f} kWh</div></div>
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
          <div class="card"><div class="title">Saving per PV</div><div class="value">RM {c['save_per_pv']:.2f}</div></div>
          <div class="card"><div class="title">Installed kWp</div><div class="value">{c['kwp_installed']:.2f} kWp</div></div>
          <div class="card"><div class="title">kWac</div><div class="value">{c['kwac']:.2f} kW</div></div>
          <div class="card"><div class="title">Price (CC)</div><div class="value">RM {c['cost_cc']:.2f}</div></div>
          <div class="card"><div class="title">Price (Cash)</div><div class="value">RM {c['cost_cash']:.2f}</div></div>
          <div class="card"><div class="title">Operating & Maintenance</div><div class="value">RM {c['om_fee_monthly']:.0f}</div></div>
          <div class="card"><div class="title">Inverters</div><div class="value">{MICROINV_UNITS:.2f} units</div></div>
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
          <div class="card"><div class="title">3-Year Installment(0%)</div><div class="value">RM {c['inst_3yr']:.2f}/month</div></div>
          <div class="card"><div class="title">5-Year Installment(0%)</div><div class="value">RM {c['inst_5yr']:.2f}/month</div></div>
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