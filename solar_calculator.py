import math
import re
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

# --- Constants ---
PANEL_WATT = 640
GENERAL_TARIFF = 0.4333
TARIFF_ENERGY = 0.4333
DAILY_USAGE_RATIO = 0.7  # 70% daytime usage
INTEREST_RATE = 0.08
INSTALLMENT_YEARS = 4

ENERGY_CHARGE_RATIO = 0.6  # 60% of monthly bill is energy charge

PRICE_TABLE = {
    10: 17000,  # 10 panels
    20: 28000   # 20 panels
}

O_AND_M_PER_YEAR = 800        # RM/year
MICROINV_UNITS   = 5.0        # units


def calculate_values(no_panels, sunlight_hours, monthly_bill):
    monthly_bill = float(monthly_bill) if monthly_bill else 0.0

    # Energy tariff (RM/kWh) for conversion from kWh -> RM for savings
    TARIFF_ENERGY = get_energy_charge_rate(monthly_bill)

    # System size
    kwp = no_panels * PANEL_WATT / 1000.0

    # Per-panel production (total monthly)
    per_panel_monthly_total = (PANEL_WATT / 1000.0) * sunlight_hours * 30.0
    # Daytime portion of generation (what the house can use directly)
    per_panel_daytime_kwh = per_panel_monthly_total * DAILY_USAGE_RATIO

    # Daily & monthly yields
    daily_yield = kwp * sunlight_hours
    daytime_kwh = daily_yield * DAILY_USAGE_RATIO
    daily_saving = daytime_kwh * TARIFF_ENERGY  # RM/day from daytime self-consumption
    monthly_saving = daily_saving * 30.0        # RM/month (generation-driven)

    # For transparency, also provide generation numbers:
    monthly_gen_kwh = no_panels * per_panel_monthly_total
    monthly_gen_daytime_kwh = no_panels * per_panel_daytime_kwh

    # New monthly bill (do not cap unless you want to)
    new_monthly_bill = monthly_bill - monthly_saving

    # Cost tiers
    if no_panels < 10:
        cost_cash = 17000
    elif 10 <= no_panels <= 19:
        cost_cash = 17000 + (no_panels - 10) * 1000
    elif 20 <= no_panels <= 50:
        cost_cash = 28000 + (no_panels - 20) * 1000
    else:
        cost_cash = 58000

    # Installments (8% total interest in your previous logic)
    installment_total = cost_cash * (1 + INTEREST_RATE)  # total with interest
    installment_4yrs = installment_total / (INSTALLMENT_YEARS * 12)

    # ROI and Payback: use yearly saving based on generation-driven monthly_saving
    yearly_saving = monthly_saving * 12.0
    roi_cash = cost_cash / yearly_saving if yearly_saving else float("inf")
    roi_cc = installment_total / yearly_saving if yearly_saving else float("inf")

    save_per_pv = yearly_saving / no_panels if no_panels else 0.0

    # Environmental
    total_fossil = 350 * kwp
    total_trees = 2 * kwp
    total_co2 = 0.85 * kwp

    return {
        "No Panels": no_panels,
        "kWp": round(kwp, 2),
        "Daily Yield (kWh)": round(daily_yield, 2),
        "Daytime Saving (kWh)": round(daytime_kwh, 2),
        "Daytime Saving (RM)": round(daily_saving, 2),
        "Daily Saving (RM)": round(daily_saving, 2),
        "Monthly Saving (RM)": round(monthly_saving, 2),
        "Yearly Saving (RM)": round(yearly_saving, 2),
        "Total Cost (RM)": f"{int(cost_cash):,}",
        "Installment 8% Interests": f"{int(installment_total):,}",
        "Installment 4 Years (RM)": round(installment_4yrs, 1),
        "monthly_kwh": round(monthly_gen_kwh, 2),
        "new_monthly": round(new_monthly_bill, 2),
        "roi_cash": round(roi_cash, 2) if yearly_saving else 0.0,
        "roi_cc": round(roi_cc, 2) if yearly_saving else 0.0,
        "save_per_pv": round(save_per_pv, 2),
        "kwp_installed": round(kwp, 2),
        "kwac": round(kwp * 0.9, 2),
        "cost_cash": cost_cash,
        "cost_cc": round(installment_total, 2),
        "om_fee_monthly": round(cost_cash * 0.01 / 12, 0),
        "total_fossil": round(total_fossil, 2),
        "total_trees": round(total_trees, 2),
        "total_co2": round(total_co2, 2),
        # expose intermediate numbers for debugging
        "per_panel_monthly_total": round(per_panel_monthly_total, 3),
        "per_panel_daytime_kwh": round(per_panel_daytime_kwh, 3),
        "monthly_gen_kwh": round(monthly_gen_kwh, 2),
        "monthly_gen_daytime_kwh": round(monthly_gen_daytime_kwh, 2),
        "tariff_energy": TARIFF_ENERGY,
    }

def get_energy_charge_rate(monthly_bill):
    """
    Returns the correct ENERGY CHARGE (RM/kWh) based on total monthly consumption.
    """
    # Rough estimate to get monthly consumption (since the bill includes other charges)
    avg_tariff_all = 0.4333  # average including network etc.
    est_kwh = monthly_bill / avg_tariff_all

    if est_kwh <= 1500:
        return 0.2703  # Energy charge below 1500 kWh
    else:
        return 0.3703  # Energy charge above 1500 kWh

# === PDF GENERATOR ===
def build_pdf(bill, raw_needed, pkg, c, no_sun_days):
    # helper: make a safe float from many display formats ("38,880", "RM 38,880", "5.2 yrs")
    def clean_number(x):
        if x is None:
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip()
            # remove currency label, percent, years text, commas and parentheses
            s = s.replace("RM", "").replace("rm", "")
            s = s.replace("%", "").replace("yrs", "").replace("year", "")
            s = s.replace("(", "").replace(")", "")
            s = s.replace(",", "")
            s = s.strip()
            if s == "":
                return 0.0
            # if it's something like "38 880" remove spaces
            s = re.sub(r"\s+", "", s)
            try:
                return float(s)
            except Exception:
                # fallback: remove any non-digit/decimal minus sign and try again
                s2 = re.sub(r"[^0-9.\-]+", "", s)
                try:
                    return float(s2) if s2 not in ("", "-", ".") else 0.0
                except Exception:
                    return 0.0
        return 0.0

    # safe getters for c dict with fallback
    def get_str(key, fmt="{:s}"):
        v = c.get(key)
        return fmt.format(str(v)) if v is not None else ""

    def get_num(key):
        return clean_number(c.get(key))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Solar Savings Report", ln=1, align="C")
    pdf.ln(6)

    # User inputs (left column/right column)
    pdf.set_font("Helvetica", size=12)
    pdf.set_fill_color(240,240,240)

    inputs = [
        ("Monthly Bill (MYR)", f"{float(bill):,.2f}" if bill not in (None, "") else "0.00"),
        ("No-Sun Days/Month", str(no_sun_days)),
        ("Panels Needed", str(raw_needed)),
        ("Package Qty", str(pkg))
    ]
    for i,(label,val) in enumerate(inputs):
        fill = True if i % 2 == 0 else False
        pdf.cell(90, 8, label, border=1, fill=fill)
        pdf.cell(90, 8, val, border=1, ln=1, fill=fill)
    pdf.ln(6)

    # Key Metrics
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Key Metrics", ln=1)
    pdf.set_font("Helvetica", size=12)
    colw = pdf.w/2 - 20

    metrics = [
        ("Consumption (kWh/mo)", f"{get_num('monthly_kwh') :,.2f}"),
        ("Monthly Gen (kWh)", f"{get_num('monthly_gen') :,.2f}" if 'monthly_gen' in c else f"{get_num('Daily Yield (kWh)')*30:,.2f}"),
        ("Unit Rate (RM/kWh)", f"{get_num('unit_rate') :,.2f}"),
        ("Retail Charge (RM/mo)", f"{get_num('retail_charge') :,.2f}"),
        ("Monthly Savings (RM)", f"{get_num('Monthly Saving (RM)') :,.2f}" if 'Monthly Saving (RM)' in c else f"{get_num('Monthly Saving (RM)') :,.2f}"),
        ("O&M Fee (RM/mo)", f"{get_num('om_fee_monthly') :,.2f}"),
        ("New Bill After Solar (RM)", f"{get_num('new_monthly') :,.2f}")
    ]

    for i,(label,val) in enumerate(metrics):
        fill = (i % 2 == 0)
        pdf.set_fill_color(245,245,245 if fill else 255)
        pdf.cell(colw, 8, label, border=1, fill=fill)
        pdf.cell(colw, 8, val, border=1, ln=1, fill=fill)
    pdf.ln(6)

    # Financial Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Financial Summary", ln=1)
    pdf.set_font("Helvetica", size=12)

    fin = [
        ("Estimated Total Sav/Month", f"RM {get_num('Monthly Saving (RM)') :,.2f}"),
        ("Estimated Total Sav/Year", f"RM {get_num('Yearly Saving (RM)') :,.2f}"),
        ("Total Cost (Cash)", f"RM {get_num('cost_cash') :,.2f}" if 'cost_cash' in c else get_str("Total Cost (RM)", "{:s}")),
        ("Installment (8% Interest) (Total)", f"RM {get_num('Installment 8% Interests') :,.2f}"),
        ("Installment (4 Years) (Monthly)", f"RM {get_num('Installment 4 Years (RM)') :,.2f}"),
        ("Estimated ROI (Cash) (yrs)", f"{get_num('roi_cash') :,.2f}"),
        ("Estimated ROI (CC) (yrs)", f"{get_num('roi_cc') :,.2f}")
    ]

    for i,(label,val) in enumerate(fin):
        fill = (i % 2 == 0)
        pdf.set_fill_color(245,245,245 if fill else 255)
        pdf.cell(colw, 8, label, border=1, fill=fill)
        pdf.cell(colw, 8, val, border=1, ln=1, fill=fill)
    pdf.ln(6)

    # Environmental Benefits
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Environmental Benefits", ln=1)
    pdf.set_font("Helvetica", size=12)

    env = [
        ("Fossil Fuel Saved (kg)", f"{get_num('total_fossil') :,.2f}"),
        ("Trees Saved", f"{get_num('total_trees') :,.2f}"),
        ("CO2 Avoided (t)", f"{get_num('total_co2') :,.2f}")
    ]
    for i,(label,val) in enumerate(env):
        fill = (i % 2 == 0)
        pdf.set_fill_color(240,240,240 if fill else 255)
        pdf.cell(90, 8, label, border=1, fill=fill)
        pdf.cell(90, 8, val, border=1, ln=1, fill=fill)

    # Footer note
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Note: Figures are estimates. Actual results depend on site conditions, weather and system performance.", align="L")

    return io.BytesIO(pdf.output(dest="S").encode("latin-1"))

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
            bill_input = float(bill_input) if bill_input else 0
            submitted = st.form_submit_button("Calculate")

        try:
            bill_val = float(bill_input)
        except:
            bill_val = None

        # --- Step 0: Select location (for sunlight hours) ---
        st.subheader("📍 Select Location")

        area_sun_map = {
            "Johor Bahru":   3.42,
            "BP/Muar":       3.56,
            "Kuala Lumpur":  3.62,
            "North":         3.75,
            "Other (Default 3.5 h/day)": 3.5
        }

        # Default 3.5 hours/day if nothing selected
        selected_area = st.selectbox(
            "Select your area:",
            options=list(area_sun_map.keys()),
            index=len(area_sun_map) - 1  # Default to the first option (Johor Bahru)
        )

        # Use the selected area's sunlight hours or fallback to default
        sunlight_hours = area_sun_map.get(selected_area, 3.5)

        st.markdown(
            f"<p style='color:#555; font-size:14px;'>☀️ Average sunlight hours for <b>{selected_area}</b>: <b>{sunlight_hours} hours/day</b></p>",
            unsafe_allow_html=True
        )


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

        # === PANEL PACKAGE SELECTION ===
        st.subheader("📦 Solar Panel Package Selection")

        # --- User bill input ---
        # (assuming you've already collected 'bill' earlier)
        # Example: bill = st.number_input("Enter your average monthly bill (RM):", min_value=0.0, step=10.0)

        # --- Step 1: Energy-charge portion (RM) ---
        ENERGY_CHARGE_RATIO = 0.6
        energy_portion_rm = bill * ENERGY_CHARGE_RATIO

        # --- Step 2: Energy tariff (RM/kWh) based on consumption ---
        TARIFF_ENERGY = get_energy_charge_rate(bill)

        # --- Step 3: target kWh to offset (monthly) ---
        target_kwh = energy_portion_rm / TARIFF_ENERGY

        # --- Step 4: per-panel monthly production (total & daytime) ---
        per_panel_monthly_total = (PANEL_WATT / 1000) * sunlight_hours * 30
        per_panel_daytime_kwh = per_panel_monthly_total * DAILY_USAGE_RATIO

        # --- Step 5: panels needed to offset the energy portion ---
        raw_needed = math.ceil(target_kwh / per_panel_daytime_kwh)
        recommended = min(max(raw_needed, 10), 100)

        # --- Step 6: slider ---
        pkg = st.slider(
            "Number of panels:",
            min_value=10,
            max_value=100,
            step=1,
            value=recommended,
            help=f"Recommended to offset ~60% (energy charge portion) of your RM {bill:.0f} monthly bill."
        )

        # Info text below slider
        st.markdown(
            f"<p style='color:#555;'>💡 Based on RM {bill:.0f} and {sunlight_hours} h/day, recommended ≈ <b>{recommended}</b> panels to offset energy charge (60%).</p>",
            unsafe_allow_html=True
        )

        st.markdown("_Note: All savings and impacts are estimated based on 70% daytime usage._")
        st.caption(f"💡 Calculations use only the Energy Charge (RM {TARIFF_ENERGY:.4f}/kWh) based on your usage level.")

        # --- 2) Run calculation using your function ---
        c = calculate_values(pkg, sunlight_hours if sunlight_hours else 3.5, bill)

        # --- 3) Override financial data ---
        c["Cost Cash (RM)"] = float(c["Total Cost (RM)"].replace(',', ''))
        c["Cost CC (RM)"]   = c["cost_cc"]
        c["ROI Cash (%)"] = c["roi_cash"]
        c["ROI CC (%)"]   = c["roi_cc"]

        # --- 4) O&M rounding logic ---
        raw_sav   = float(c["Monthly Saving (RM)"])
        rem       = raw_sav % 100
        base_hund = raw_sav - rem

        if rem > 40:
            om_fee = base_hund + 100
        else:
            om_fee = base_hund

        om_fee = max(500, min(om_fee, 1000))  # clamp
        c["O&M Fee (RM)"] = om_fee

        # Inject card CSS
        st.markdown("""
        <style>
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px,1fr));
            gap: 14px;
            margin: 16px 0;
        }
        .card {
            background: #fff;
            border-radius: 10px;
            padding: 12px 14px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 90px; /* ✅ Fixed height for alignment */
        }
        .card .title {
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 6px;
            line-height: 1.2;
            white-space: normal;
        }
        .card .value {
            font-size: 1.1rem;
            font-weight: 600;
            color: #222;
            line-height: 1.2;
        }
        </style>
        """, unsafe_allow_html=True)

        # === KEY METRICS ===
        st.subheader("📈 Key Metrics")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Estimated Solar Panel Needed</div><div class="value">{c['No Panels']}</div></div>
        <div class="card"><div class="title">Estimated Monthly Saving (RM)</div><div class="value">RM {c['Monthly Saving (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Previous Bill</div><div class="value">RM {bill:.2f}</div></div>
        <div class="card"><div class="title">New Bill</div><div class="value">RM {c['new_monthly']:.2f}</div></div>
        <div class="card"><div class="title">Total Cost(Cash)</div><div class="value">RM {c['Total Cost (RM)']}</div></div>
        <div class="card"><div class="title">Total Installment (4 Years @ 8% Interest)</div><div class="value">RM {c['Installment 8% Interests']}</div></div>
        <div class="card"><div class="title">Estimated ROI (Cash)</div><div class="value">{c['roi_cash']:.2f} yrs</div></div>
        <div class="card"><div class="title">Estimated ROI (CC)</div><div class="value">{c['roi_cc']:.2f} yrs</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === PANEL & SAVINGS SUMMARY ===
        st.subheader("🔆 Panel & Savings Summary")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Consumption</div><div class="value">{c['monthly_kwh']:.2f} kWh</div></div>
        <div class="card"><div class="title">Estimated No. of Panels</div><div class="value">{c['No Panels']}</div></div>
        <div class="card"><div class="title">Installed Capacity</div><div class="value">{c['kWp']:.2f} kWp</div></div>
        <div class="card"><div class="title">Estimated Daily Yield</div><div class="value">{c['Daily Yield (kWh)']:.2f} kWh</div></div>
        <div class="card"><div class="title">Estimated Daytime Saving (kWh)</div><div class="value">{c['Daytime Saving (kWh)']:.2f} kWh</div></div>
        <div class="card"><div class="title">Estimated Daytime Saving (RM)</div><div class="value">RM {c['Daytime Saving (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Estimated Daily Saving (RM)</div><div class="value">RM {c['Daily Saving (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Estimated Monthly Saving (RM)</div><div class="value">RM {c['Monthly Saving (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Estimated Yearly Saving (RM)</div><div class="value">RM {c['Yearly Saving (RM)']:.2f}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === FINANCIAL SUMMARY ===
        st.subheader("💰 Financial Summary")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Estimated Total Sav/Month</div><div class="value">RM {c['Monthly Saving (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Estimated Total Sav/Year</div><div class="value">RM {c['Yearly Saving (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Total Cost(Cash)</div><div class="value">RM {c['Total Cost (RM)']}</div></div>
        <div class="card"><div class="title">Installment (8% Interest)</div><div class="value">RM {c['Installment 8% Interests']}</div></div>
        <div class="card"><div class="title">Installment (4 Years)</div><div class="value">RM {c['Installment 4 Years (RM)']:.2f}</div></div>
        <div class="card"><div class="title">Estimated ROI (Cash)</div><div class="value">{c['roi_cash']:.2f} yrs</div></div>
        <div class="card"><div class="title">Estimated ROI (CC)</div><div class="value">{c['roi_cc']:.2f} yrs</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === ENVIRONMENTAL BENEFITS ===
        st.subheader("🌳 Environmental Benefits")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Total Fossil /1 kWp</div><div class="value">{c['total_fossil']:.2f} kg</div></div>
        <div class="card"><div class="title">Total Trees /1 kWp</div><div class="value">{c['total_trees']:.2f}</div></div>
        <div class="card"><div class="title">Total CO₂ /1 kWp</div><div class="value">{c['total_co2']:.2f} t</div></div>
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