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
GENERAL_TARIFF = 1
TARIFF_ENERGY = 1
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

    # --- Step 1: Tariff selection based on bill ---
    if monthly_bill <= 666.45:
        GENERAL_TARIFF = 0.4443
    elif monthly_bill >= 816.45:
        GENERAL_TARIFF = 0.5443
    else:
        # Bill is in the "invalid" middle range — return empty result
        return {
            "No Panels": no_panels,
            "general_tariff": "Invalid range (666.45–816.45)",
            "monthly_bill_warning": "Please enter a bill below RM 666.45 or above RM 816.45"
        }

    # --- Step 2: Fixed parameters ---
    ENERGY_OFFSET_RATIO = 0.6  # 60% of bill offset by solar
    ENERGY_TARIFF = GENERAL_TARIFF
    PANEL_WATT = 640
    DAILY_USAGE_RATIO = 0.7  # 70% usable during daytime

    # --- Step 3: Estimate total consumption ---
    est_kwh = monthly_bill / GENERAL_TARIFF

    # --- Step 4: Energy portion to offset (60%) ---
    energy_portion_rm = monthly_bill * ENERGY_OFFSET_RATIO
    target_kwh = energy_portion_rm / GENERAL_TARIFF

    # --- Step 5: Panel and generation assumptions ---
    per_panel_monthly_total = (PANEL_WATT / 1000.0) * sunlight_hours * 30.0
    per_panel_daytime_kwh = per_panel_monthly_total * DAILY_USAGE_RATIO

    # --- Step 6: System yield ---
    kwp = no_panels * PANEL_WATT / 1000.0
    daily_yield = kwp * sunlight_hours
    daytime_kwh = daily_yield * DAILY_USAGE_RATIO

    # --- Step 7: Savings (calculated precisely) ---
    daily_saving = daytime_kwh * GENERAL_TARIFF
    monthly_saving = daily_saving * 30.0
    yearly_saving = monthly_saving * 12.0

    # --- Step 8: New monthly bill ---
    new_monthly_bill = max(0, monthly_bill - monthly_saving)

    # --- Step 9: Cost tiers ---
    if no_panels < 10:
        cost_cash = 17000
    elif 10 <= no_panels <= 19:
        cost_cash = 17000 + (no_panels - 10) * 1000
    elif 20 <= no_panels <= 50:
        cost_cash = 28000 + (no_panels - 20) * 1000
    else:
        cost_cash = 58000

    # --- Step 10: Installments (8% interest) ---
    installment_total = cost_cash * (1 + INTEREST_RATE)
    installment_4yrs = installment_total / (INSTALLMENT_YEARS * 12)

    # --- Step 11: ROI ---
    roi_cash = cost_cash / yearly_saving if yearly_saving else float("inf")
    roi_cc = installment_total / yearly_saving if yearly_saving else float("inf")
    save_per_pv = yearly_saving / no_panels if no_panels else 0.0

    # --- Step 12: Environmental impact ---
    total_fossil = 350 * kwp
    total_trees = 2 * kwp
    total_co2 = 0.85 * kwp

    return {
        "No Panels": no_panels,
        "kWp": f"{kwp:.2f}".rstrip('0').rstrip('.'),
        "Daily Yield (kWh)": f"{daily_yield:.2f}".rstrip('0').rstrip('.'),
        "Daytime Saving (kWh)": f"{daytime_kwh:.2f}".rstrip('0').rstrip('.'),

        # RM values – half-up rounding, no decimals shown
        "Daytime Saving (RM)": f"{math.floor(daily_saving + 0.5):,}",
        "Daily Saving (RM)": f"{math.floor(daily_saving + 0.5):,}",
        "Monthly Saving (RM)": f"{math.floor(monthly_saving + 0.5):,}",
        "Yearly Saving (RM)": f"{math.floor(yearly_saving + 0.5):,}",
        "Total Cost (RM)": f"{math.floor(cost_cash + 0.5):,}",
        "Installment 8% Interests": f"{math.floor(installment_total + 0.5):,}",
        "Installment 4 Years (RM)": f"{installment_4yrs:,.2f}",
        "monthly_gen_kwh": f"{math.floor(no_panels * per_panel_monthly_total + 0.5):,}",
        "monthly_kwh": f"{est_kwh:.2f}",
        "monthly_gen_daytime_kwh": f"{math.floor(no_panels * per_panel_daytime_kwh + 0.5):,}",
        "new_monthly": f"{math.floor(new_monthly_bill + 0.5):,}",
        "roi_cash": f"{roi_cash:.2f}".rstrip('0').rstrip('.'),
        "roi_cc": f"{roi_cc:.2f}".rstrip('0').rstrip('.'),
        "save_per_pv": f"{math.floor(save_per_pv + 0.5):,}",
        "kwp_installed": f"{kwp:.2f}".rstrip('0').rstrip('.'),
        "kwac": f"{(kwp * 0.9):.2f}".rstrip('0').rstrip('.'),
        "cost_cash": f"{math.floor(cost_cash + 0.5):,}",
        "cost_cc": f"{math.floor(installment_total + 0.5):,}",
        "om_fee_monthly": f"{math.floor(cost_cash * 0.01 / 12 + 0.5):,}",
        "total_fossil": f"{math.floor(total_fossil + 0.5):,}",
        "total_trees": f"{math.floor(total_trees + 0.5):,}",
        "total_co2": f"{math.floor(total_co2 + 0.5):,}",

        # Debug info
        "general_tariff": f"{GENERAL_TARIFF:.4f}",
        "energy_tariff": f"{ENERGY_TARIFF:.4f}",
        "energy_portion_rm": f"{math.floor(energy_portion_rm + 0.5):,}",
        "target_kwh": f"{math.floor(target_kwh + 0.5):,}",
        "per_panel_monthly_total": f"{per_panel_monthly_total:.2f}".rstrip('0').rstrip('.'),
        "per_panel_daytime_kwh": f"{per_panel_daytime_kwh:.2f}".rstrip('0').rstrip('.'),
    }

def get_energy_charge_rate(monthly_bill):
    """
    Returns the correct ENERGY CHARGE (RM/kWh) based on total monthly consumption.
    """
    # Rough estimate to get monthly consumption (since the bill includes other charges)
    est_kwh = monthly_bill / GENERAL_TARIFF

    if est_kwh <= 1500:
        return 0.2703  # Energy charge below 1500 kWh
    else:
        return 0.3703  # Energy charge above 1500 kWh

# === PDF GENERATOR ===
def build_pdf(bill, raw_needed, pkg, c):
    import io, re
    from fpdf import FPDF

    # helper: make a safe float from many display formats ("38,880", "RM 38,880", "5.2 yrs")
    def clean_number(x):
        if x is None:
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip()
            s = s.replace("RM", "").replace("rm", "").replace("%", "")
            s = s.replace("yrs", "").replace("year", "").replace("(", "").replace(")", "")
            s = s.replace(",", "").strip()
            s = re.sub(r"\s+", "", s)
            try:
                return float(s)
            except Exception:
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

    # User inputs
    pdf.set_font("Helvetica", size=12)
    pdf.set_fill_color(240, 240, 240)

    inputs = [
        ("Monthly Bill (MYR)", f"{float(bill):,.2f}" if bill not in (None, "") else "0.00"),
        ("Panels Needed", str(raw_needed)),
        ("Package Qty", str(pkg))
    ]
    for i, (label, val) in enumerate(inputs):
        fill = True if i % 2 == 0 else False
        pdf.cell(90, 8, label, border=1, fill=fill)
        pdf.cell(90, 8, val, border=1, ln=1, fill=fill)
    pdf.ln(6)

    # === Key Metrics ===
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Key Metrics", ln=1)
    pdf.set_font("Helvetica", size=12)
    colw = pdf.w / 2 - 20

    metrics = [
        ("Consumption (kWh/mo)", f"{get_num('monthly_kwh') :,.2f}"),
        ("Monthly Gen (kWh)", f"{get_num('monthly_gen') :,.2f}" if 'monthly_gen' in c else f"{get_num('Daily Yield (kWh)') * 30 :,.2f}"),
        ("Monthly Savings (RM)", f"{get_num('Monthly Saving (RM)') :,.2f}"),
        ("New Bill After Solar (RM)", f"{get_num('new_monthly') :,.2f}")
    ]

    for i, (label, val) in enumerate(metrics):
        fill = (i % 2 == 0)
        pdf.set_fill_color(245, 245, 245 if fill else 255)
        pdf.cell(colw, 8, label, border=1, fill=fill)
        pdf.cell(colw, 8, val, border=1, ln=1, fill=fill)
    pdf.ln(6)

    # === Financial Summary ===
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

    for i, (label, val) in enumerate(fin):
        fill = (i % 2 == 0)
        pdf.set_fill_color(245, 245, 245 if fill else 255)
        pdf.cell(colw, 8, label, border=1, fill=fill)
        pdf.cell(colw, 8, val, border=1, ln=1, fill=fill)
    pdf.ln(6)

    # === Environmental Benefits ===
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Environmental Benefits", ln=1)
    pdf.set_font("Helvetica", size=12)

    env = [
        ("Fossil Fuel Saved (kg)", f"{get_num('total_fossil') :,.2f}"),
        ("Trees Saved", f"{get_num('total_trees') :,.2f}"),
        ("CO2 Avoided (t)", f"{get_num('total_co2') :,.2f}")
    ]
    for i, (label, val) in enumerate(env):
        fill = (i % 2 == 0)
        pdf.set_fill_color(240, 240, 240 if fill else 255)
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
                key="bill_input",
                placeholder="Below 666.45 or above 816.45",
                help="Please enter a bill amount below RM 666.45 or above RM 816.45"
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
            "Default": 3.5
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
            f"<p style='color:#555; font-size:14px;'>☀️ Sunlight hours for <b>{selected_area}</b>: <b>{sunlight_hours} hours/day</b></p>",
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

        # # Advanced settings
        # with st.expander("⚙️ Advanced Settings"):
        #     no_sun_days = st.selectbox("No-sun days per month:", [0,15,30], index=0)

        # === PANEL PACKAGE SELECTION ===
        st.subheader("📦 Solar Panel Package Selection")

        # --- User bill input ---
        # (assuming you've already collected 'bill' earlier)
        # Example: bill = st.number_input("Enter your average monthly bill (RM):", min_value=0.0, step=10.0)

        # --- Step 2: Select tariff based on bill ---
        if bill <= 666.45:
            GENERAL_TARIFF = 0.4443  # RM/kWh for low usage
        elif bill >= 816.45:
            GENERAL_TARIFF = 0.5443  # RM/kWh for high usage
        else:
            st.warning("⚠️ Please enter a bill below RM 666.45 or above RM 816.45.")
            st.stop()

        # --- Step 3: Other constants ---
        ENERGY_OFFSET_RATIO = 0.6  # 60% of bill offsettable
        PANEL_WATT = 640
        DAILY_USAGE_RATIO = 0.7

        # --- Step 4: Estimate monthly consumption ---
        est_kwh = bill / GENERAL_TARIFF  # total monthly usage in kWh

        # --- Step 5: Energy portion to offset (60%) ---
        energy_portion_rm = bill * ENERGY_OFFSET_RATIO
        target_kwh = energy_portion_rm / GENERAL_TARIFF

        # --- Step 6: Per-panel generation (daytime only) ---
        per_panel_monthly_total = (PANEL_WATT / 1000) * sunlight_hours * 30
        per_panel_daytime_kwh = per_panel_monthly_total * DAILY_USAGE_RATIO

        # --- Step 7: Determine number of panels needed ---
        raw_needed = math.ceil(target_kwh / per_panel_daytime_kwh)
        recommended = min(max(raw_needed, 10), 100)

        # --- Step 8: Panel slider ---
        pkg = st.slider(
            "Number of panels:",
            min_value=10,
            max_value=100,
            step=1,
            value=recommended,
            help=f"Recommended to offset ~60% (RM {energy_portion_rm:.0f}) of your RM {bill:.0f} monthly bill."
        )

        # --- Step 9: Info display ---
        st.markdown(
            f"""
            <p style='color:#555;'>
            💡 Based on your RM {bill:.0f} monthly bill and {sunlight_hours}h/day sunlight:<br>
            • Applied tariff: <b>RM {GENERAL_TARIFF:.4f}/kWh</b><br>
            • Energy Charge (60%): <b>RM {energy_portion_rm:.0f}</b> ≈ <b>{target_kwh:.0f} kWh</b><br>
            • Recommended solar panels: <b>{recommended}</b> pcs<br>
            </p>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <p style='color:#777;font-size:13px;'>
            ⚡ <b>Note:</b> Solar offsets the energy charge only (≈60% of your total bill).<br>
            Tariff varies by usage: below RM666.45 → RM0.4443/kWh, above RM816.45 → RM0.5443/kWh.<br>
            </p>
            """,
            unsafe_allow_html=True
        )

        st.markdown("_Note: All savings and impacts are estimated based on 70% daytime usage._")

        # --- 2) Run calculation using your function ---
        c = calculate_values(pkg, sunlight_hours if sunlight_hours else 3.5, bill)

        # --- 3) Override financial data ---
        c["Cost Cash (RM)"] = float(c["Total Cost (RM)"].replace(',', ""))
        c["Cost CC (RM)"]   = c["cost_cc"]
        c["ROI Cash (%)"] = c["roi_cash"]
        c["ROI CC (%)"]   = c["roi_cc"]

        # --- 4) O&M rounding logic ---
        raw_sav = float(str(c["Monthly Saving (RM)"]).replace(",", ""))
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
        <div class="card"><div class="title">Estimated Monthly Saving (RM)</div><div class="value">RM {c['Monthly Saving (RM)']}</div></div>
        <div class="card"><div class="title">Previous Bill</div><div class="value">RM {bill:,.0f}</div></div>
        <div class="card"><div class="title">New Bill</div><div class="value">RM {c['new_monthly']}</div></div>
        <div class="card"><div class="title">Total Cost (Cash)</div><div class="value">RM {c['Total Cost (RM)']}</div></div>
        <div class="card"><div class="title">Total Installment (4 Years @ 8% Interest)</div><div class="value">RM {c['Installment 8% Interests']}</div></div>
        <div class="card"><div class="title">Estimated ROI (Cash)</div><div class="value">{c['roi_cash']} yrs</div></div>
        <div class="card"><div class="title">Estimated ROI (CC)</div><div class="value">{c['roi_cc']} yrs</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === PANEL & SAVINGS SUMMARY ===
        st.subheader("🔆 Panel & Savings Summary")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Consumption</div><div class="value">{c['monthly_kwh']} kWh</div></div>
        <div class="card"><div class="title">Estimated No. of Panels</div><div class="value">{c['No Panels']}</div></div>
        <div class="card"><div class="title">Installed Capacity</div><div class="value">{c['kWp']} kWp</div></div>
        <div class="card"><div class="title">Estimated Daily Yield</div><div class="value">{c['Daily Yield (kWh)']} kWh</div></div>
        <div class="card"><div class="title">Estimated Daytime Saving (kWh)</div><div class="value">{c['Daytime Saving (kWh)']} kWh</div></div>
        <div class="card"><div class="title">Estimated Daytime Saving (RM)</div><div class="value">RM {c['Daytime Saving (RM)']}</div></div>
        <div class="card"><div class="title">Estimated Daily Saving (RM)</div><div class="value">RM {c['Daily Saving (RM)']}</div></div>
        <div class="card"><div class="title">Estimated Monthly Saving (RM)</div><div class="value">RM {c['Monthly Saving (RM)']}</div></div>
        <div class="card"><div class="title">Estimated Yearly Saving (RM)</div><div class="value">RM {c['Yearly Saving (RM)']}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === FINANCIAL SUMMARY ===
        st.subheader("💰 Financial Summary")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Estimated Total Sav/Month</div><div class="value">RM {c['Monthly Saving (RM)']}</div></div>
        <div class="card"><div class="title">Estimated Total Sav/Year</div><div class="value">RM {c['Yearly Saving (RM)']}</div></div>
        <div class="card"><div class="title">Total Cost (Cash)</div><div class="value">RM {c['Total Cost (RM)']}</div></div>
        <div class="card"><div class="title">Installment (8% Interest)</div><div class="value">RM {c['Installment 8% Interests']}</div></div>
        <div class="card"><div class="title">Installment (4 Years)</div><div class="value">RM {c['Installment 4 Years (RM)']}</div></div>
        <div class="card"><div class="title">Estimated ROI (Cash)</div><div class="value">{c['roi_cash']} yrs</div></div>
        <div class="card"><div class="title">Estimated ROI (CC)</div><div class="value">{c['roi_cc']} yrs</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === ENVIRONMENTAL BENEFITS ===
        st.subheader("🌳 Environmental Benefits")
        st.markdown(f"""
        <div class="grid-container">
        <div class="card"><div class="title">Total Fossil /1 kWp</div><div class="value">{c['total_fossil']} kg</div></div>
        <div class="card"><div class="title">Total Trees /1 kWp</div><div class="value">{c['total_trees']}</div></div>
        <div class="card"><div class="title">Total CO₂ /1 kWp</div><div class="value">{c['total_co2']} t</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === DOWNLOAD PDF BUTTON ===
        pdf_buffer = build_pdf(bill, raw_needed, pkg, c)
        st.download_button(
            label="📄 Download Report as PDF",
            data=pdf_buffer,
            file_name="solar_savings_report.pdf",
            mime="application/pdf"
        )


if __name__ == "__main__":
    main()