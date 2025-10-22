import math
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
TARIFF_MYR_PER_KWH = 0.4333
DAILY_USAGE_RATIO = 0.7  # 70% daytime usage
INTEREST_RATE = 0.08
INSTALLMENT_YEARS = 4

PRICE_TABLE = {
    10: 17000,  # 10 panels
    20: 28000   # 20 panels
}

O_AND_M_PER_YEAR    = 800        # RM/year
MICROINV_UNITS      = 5.0        # units

def calculate_values(no_panels, sunlight_hours, monthly_bill):
    # System size
    kwp = no_panels * PANEL_WATT / 1000
    
    # Daily yield
    daily_yield = kwp * sunlight_hours
    
    # Daytime saving (kWh)
    daytime_kwh = daily_yield * DAILY_USAGE_RATIO
    
    # Daytime saving (RM)
    daytime_rm = daytime_kwh * TARIFF_MYR_PER_KWH
    
    # Daily, monthly, yearly saving
    daily_saving = daytime_rm
    monthly_saving = daily_saving * 30
    yearly_saving = monthly_saving * 12
    monthly_bill = float(monthly_bill) if monthly_bill else 0
    monthly_kwh = monthly_bill / TARIFF_MYR_PER_KWH  # if you have access to monthly_bill
    new_monthly_bill = max(monthly_bill - monthly_saving,0)
    
    # --- Cost (Tiered) ---
    if no_panels < 10:
        cost_cash = 17000
    elif 10 <= no_panels <= 19:
        cost_cash = 17000 + (no_panels - 10) * 1000
    elif 20 <= no_panels <= 50:
        cost_cash = 28000 + (no_panels - 20) * 1000
    else:
        cost_cash = 58000

    cost_cc = cost_cash + 2000

    save_per_pv = yearly_saving / no_panels if no_panels else 0
    kwp = no_panels * PANEL_WATT / 1000
    kwp_installed = kwp
    inverter_efficiency = 0.9
    kwac = kwp * inverter_efficiency    
        
    # --- Installments ---
    installment_interest = cost_cash * (1 + INTEREST_RATE)
    installment_4yrs = installment_interest / (INSTALLMENT_YEARS * 12)

    cost_cc = installment_interest

    # --- Payback & ROI ---
    roi_cash = cost_cash / yearly_saving if yearly_saving else 0
    roi_cc = cost_cc / yearly_saving if yearly_saving else 0

    # --- Operating & Maintenance Fee ---
    om_fee_monthly = cost_cash * 0.01 / 12  # 1% per year

    # --- Environmental Impact ---
    # Reference: per 1 kWp = 350 kg fossil saved, 2 trees, 0.85 t CO₂
    total_fossil = 350 * kwp_installed  # kg
    total_trees  = 2 * kwp_installed    # trees
    total_co2    = 0.85 * kwp_installed # tons
    
    return {
        "No Panels": no_panels,
        "kWp": round(kwp, 2),
        "Daily Yield (kWh)": round(daily_yield, 2),
        "Daytime Saving (kWh)": round(daytime_kwh, 2),
        "Daytime Saving (RM)": round(daytime_rm, 2),
        "Daily Saving (RM)": round(daily_saving, 2),
        "Monthly Saving (RM)": round(monthly_saving, 0),
        "Yearly Saving (RM)": round(yearly_saving, 0),
        "Total Cost (RM)": f"{int(cost_cash):,}",
        "Installment 8% Interests": f"{int(installment_interest):,}",
        "Installment 4 Years (RM)": round(installment_4yrs, 1),
        "monthly_kwh": round(monthly_kwh, 2),
        "new_monthly": round(new_monthly_bill, 0),
        "roi_cash": roi_cash,
        "roi_cc": roi_cc,
        "save_per_pv": round(save_per_pv, 2),
        "kwp_installed": round(kwp_installed, 2),
        "kwac": round(kwac, 2),
        "cost_cash": cost_cash,
        "cost_cc": round(cost_cc, 2),
        "om_fee_monthly": round(om_fee_monthly, 0),
        "total_fossil": round(total_fossil, 2),
        "total_trees": round(total_trees, 2),
        "total_co2": round(total_co2, 2),

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
    
    # --- Default sunlight hours ---
    default_sunlight = 3.5

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

        # ---- Location ----
        location     = st.selectbox(
                "Location:",
                ["Use Default (3.5 hrs)", "Johor Bahru", "BP/Muar", "Kuala Lumpur", "North"],
                index=0
            )

        # Map each choice to its peak sun hours
        area_sun_map = {
            "Johor Bahru":   3.42,
            "BP/Muar":       3.56,
            "Kuala Lumpur":  3.62,
            "North":         3.75
        }
        # Use default 3.5 if "Use Default" is selected
        sunlight_hours = default_sunlight if location == "Use Default (3.5 hrs)" else area_sun_map[location]


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
            # use_daytime = st.checkbox("Enable daytime consumption (20%)", value=False)
            # location     = st.selectbox(
            #     "Location:",
            #     ["Johor Bahru", "BP/Muar", "Kuala Lumpur", "North"]
            # )

            # # Map each choice to its peak sun hours
            # area_sun_map = {
            #     "Johor Bahru":   3.42,
            #     "BP/Muar":       3.56,
            #     "Kuala Lumpur":  3.62,
            #     "North":         3.75
            # }
            # # grab the correct value for this run
            # sunlight_hours = area_sun_map[location]

        # Panel package selection
        st.subheader("📦 Solar Panel Package Selection")
        
        # --- 1) Estimate monthly energy usage (kWh) from bill ---
        rec_kwh = bill / TARIFF_MYR_PER_KWH  # monthly usage in kWh

        rec_kwp = bill / (sunlight_hours * DAILY_USAGE_RATIO * TARIFF_MYR_PER_KWH * 30)
        raw_needed = math.ceil(rec_kwp * 1000 / PANEL_WATT)
        recommended = min(max(raw_needed, 10), 50)

        # --- 4) Let user adjust from recommended baseline ---
        pkg = st.slider(
            "Number of panels:",
            min_value=10,
            max_value=50,
            step=1,
            value=recommended,
            help=f"Recommended to offset your monthly bill of RM {bill:.0f} is about {recommended} panels."
        )

        # 3️⃣ Info text under slider
        st.markdown(
            f"<p style='color: #555; font-size: 14px;'>💡 Recommended: Estimated <b>{recommended}</b> solar panels are needed to fully cover your monthly bill.</p>",
            unsafe_allow_html=True
        )

        st.markdown("_Note: All savings and impacts are estimated based on 70% daytime usage._")

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
        <div class="card"><div class="title">Estimated ROI (CC)</div><div class="value">{c['roi_cc']:.2f} yrs</div></div>
        <div class="card"><div class="title">Estimated ROI (Cash)</div><div class="value">{c['roi_cash']:.2f} yrs</div></div>
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