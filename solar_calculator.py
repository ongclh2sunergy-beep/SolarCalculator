import math
import streamlit as st

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



def calculate_values(no_panels, sunlight_hours, monthly_bill, daytime_option=0.7):
    monthly_bill = float(monthly_bill) if monthly_bill else 0.0

    # --- Step 1: Tariff selection based on bill ---
    if monthly_bill <= 666.45:
        GENERAL_TARIFF = 0.4443
    elif monthly_bill >= 816.45:
        GENERAL_TARIFF = 0.5443
    else:
        return {
            "No Panels": no_panels,
            "general_tariff": "Invalid range (666.45–816.45)",
            "monthly_bill_warning": "Please enter a bill below RM 666.45 or above RM 816.45"
        }

    # --- Step 2: Fixed constants ---
    PANEL_WATT = 640
    ENERGY_OFFSET_RATIO = 0.6
    ENERGY_TARIFF = GENERAL_TARIFF

    # --- Step 3: Estimate total consumption ---
    est_kwh = monthly_bill / GENERAL_TARIFF

    # --- Step 4: Over-generation target (120%) ---
    oversize_factor = 1.2
    target_kwh = est_kwh * oversize_factor

    # --- Step 5: Per-panel generation ---
    per_panel_monthly_total = (PANEL_WATT / 1000) * sunlight_hours * 30
    per_panel_daytime_kwh = per_panel_monthly_total

    # --- Step 6: Recommended panels (EVEN PANEL RULE) ---
    raw_needed = math.ceil(target_kwh / per_panel_monthly_total)

    # Ensure even number
    if raw_needed % 2 != 0:
        raw_needed += 1

    # If low daytime usage → add 2 panels
    if daytime_option in [0.2, 0.3]:
        raw_needed += 2

    recommended = max(min(raw_needed, 100), 10)

    # --- Step 7: System yield ---
    kwp = no_panels * PANEL_WATT / 1000
    total_solar_kwh = per_panel_monthly_total * no_panels

    # Split generation into direct usage vs export
    direct_used_kwh = est_kwh * daytime_option
    exported_kwh = total_solar_kwh - direct_used_kwh

    # --- Step 8: Export rate ---
    export_rate = 0.20  # fixed SMP rate
    export_credit_rm = exported_kwh * export_rate

    # --- Step 9: Night usage and new bill calculation ---
    night_kwh = est_kwh * (1 - daytime_option)

    # Sub charges
    energy_charge_rm = night_kwh * (0.2703 if est_kwh <= 1500 else 0.3703)
    network_charge_rm = night_kwh * 0.1285
    capacity_charge_rm = night_kwh * 0.0455
    retail_charge_rm = 10.0

    # Apply export credit ONLY to the energy charge
    energy_charge_after_offset = max(energy_charge_rm - export_credit_rm, 0)

    # Now calculate subtotal (export does NOT reduce other charges)
    subtotal_rm = (
        energy_charge_after_offset +
        network_charge_rm +
        capacity_charge_rm +
        retail_charge_rm
    )
    subtotal_rm = max(subtotal_rm, 0)

    # Taxes
    kwtbb_rm = subtotal_rm * 0.016
    after_kwtbb_rm = subtotal_rm + kwtbb_rm
    sst_rm = after_kwtbb_rm * 0.08
    final_new_bill_rm = after_kwtbb_rm + sst_rm

    # --- Step 10: Estimated Saving ---
    estimated_saving = max(monthly_bill - final_new_bill_rm, 0)

    # --- Step 11: Cost tiers ---
    if no_panels < 10:
        cost_cash = 17000
    elif 10 <= no_panels <= 17:
        cost_cash = 17000 + (no_panels - 10) * 1000
    elif no_panels >= 18:
        cost_cash = 26000 + (no_panels - 18) * 1000
    else:
        cost_cash = 58000

    # --- Step 12: Installments ---
    INTEREST_RATE = 0.08
    INSTALLMENT_YEARS = 4
    installment_total = cost_cash * (1 + INTEREST_RATE)
    installment_4yrs = installment_total / (INSTALLMENT_YEARS * 12)

    # --- Step 13: ROI ---
    yearly_saving = estimated_saving * 12
    roi_cash = cost_cash / yearly_saving if yearly_saving else float("inf")
    roi_cc = installment_total / yearly_saving if yearly_saving else float("inf")
    save_per_pv = yearly_saving / no_panels if no_panels else 0.0

    # --- Step 14: Environmental Impact ---
    total_fossil = 350 * kwp
    total_trees = 2 * kwp
    total_co2 = 0.85 * kwp

    # --- Step 15: Battery Calculation ---
    solar_capacity_kw = kwp
    est_battery_capacity = solar_capacity_kw * 2  # solar * 2
    battery_kwh = max(10, math.floor(est_battery_capacity / 5) * 5)  # round to nearest 5
    battery_price = (battery_kwh / 5) * 3300  # RM 3300 per 5kWh

    # --- Step 16: Return Dictionary (unchanged) ---
    return {
        "No Panels": no_panels,
        "Recommended Panels": recommended,
        "kWp": f"{kwp:.2f}".rstrip('0').rstrip('.'),
        "Daily Yield (kWh)": f"{(total_solar_kwh / 30):.2f}".rstrip('0').rstrip('.'),
        "Daytime Saving (kWh)": f"{direct_used_kwh / 30:.2f}".rstrip('0').rstrip('.'),
        "Daytime Saving (RM)": f"{math.floor(estimated_saving / 30 + 0.5):,}",
        "Daily Saving (RM)": f"{math.floor(estimated_saving / 30 + 0.5):,}",
        "Monthly Saving (RM)": f"{math.floor(estimated_saving + 0.5):,}",
        "Yearly Saving (RM)": f"{math.floor(yearly_saving + 0.5):,}",
        "Total Cost (RM)": f"{math.floor(cost_cash + 0.5):,}",
        "Installment 8% Interests": f"{math.floor(installment_total + 0.5):,}",
        "Installment 4 Years (RM)": f"{installment_4yrs:,.2f}",
        "monthly_gen_kwh": f"{math.floor(no_panels * per_panel_monthly_total + 0.5):,}",
        "monthly_kwh": f"{est_kwh:.2f}",
        "new_monthly": f"{math.floor(final_new_bill_rm + 0.5):,}",
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
        "general_tariff": f"{GENERAL_TARIFF:.4f}",
        "energy_tariff": f"{ENERGY_TARIFF:.4f}",
        "energy_portion_rm": f"{math.floor(monthly_bill * ENERGY_OFFSET_RATIO + 0.5):,}",
        "target_kwh": f"{math.floor(target_kwh + 0.5):,}",
        "per_panel_monthly_total": f"{per_panel_monthly_total:.2f}".rstrip('0').rstrip('.'),
        "per_panel_daytime_kwh": f"{per_panel_daytime_kwh:.2f}".rstrip('0').rstrip('.'),
        "Battery Capacity (kWh)": f"{battery_kwh:.0f}",
        "Battery Price (RM)": f"{math.floor(battery_price + 0.5):,}",
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

def build_pdf(bill, raw_needed, pkg, c):
    import io, re, os, urllib.request, tempfile
    from fpdf import FPDF
    # from fpdf.enums import XPos, YPos

    # --- Helper: clean number strings ---
    def clean_number(x):
        if x is None:
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = re.sub(r"[^\d.\-]", "", x)
            try:
                return float(s)
            except:
                return 0.0
        return 0.0

    def get_num(key): return clean_number(c.get(key))
    def get_str(key): return str(c.get(key) or "")

    # --- Setup PDF ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "", 12)

    # === Solar Theme Colors ===
    COLOR_PRIMARY = (255, 193, 7)     # yellow
    COLOR_SECONDARY = (255, 243, 205) # light background
    COLOR_TEXT = (60, 60, 60)

    # --- Header (with logo) ---
    # Use a safe, downloadable image
    logo_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRvUrQzbNoJwW7pypHZ9yweCafrQtCWeKRjUg&s"
    tmp_dir = tempfile.gettempdir()
    logo_path = os.path.join(tmp_dir, "company_logo.png")

    try:
        urllib.request.urlretrieve(logo_url, logo_path)
    except Exception:
        logo_path = None

    # Place logo if exists
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, 10, 6, 25)  # (x, y, width)

    # --- Header ---
    pdf.set_xy(40, 12)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 165, 0)
    pdf.cell(0, 10, "Solar Savings Summary",
             ln=True, align="L")
    pdf.set_text_color(*COLOR_TEXT)
    pdf.ln(10)

    # --- Section Helpers ---
    def section_header(title):
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, title, ln=True, align="L", fill=True)
        pdf.set_font("Helvetica", "", 12)
        pdf.ln(2)

    def add_table(rows, col1_width=95, col2_width=95):
        for label, val in rows:
            pdf.set_fill_color(*COLOR_SECONDARY)
            pdf.cell(col1_width, 8, label, border=1, fill=True)
            pdf.cell(col2_width, 8, str(val), border=1,
                     ln=True, fill=True)
        pdf.ln(4)

    # --- Input Summary ---
    section_header("Input Summary")
    inputs = [
        ("Monthly Bill (RM)", f"{float(bill):,.2f}" if bill else "0.00"),
        ("Panel Needed", str(pkg)),
        ("Tariff Rate (RM/kWh)", get_str("general_tariff")),
        ("Estimated Monthly Consumption (kWh)", get_str("monthly_kwh")),
    ]
    add_table(inputs)

    # --- Solar System Summary ---
    section_header("Solar System Details")
    system = [
        ("Installed kWp", get_str("kwp_installed")),
        ("kWac Output", get_str("kwac")),
        ("Per Panel Yield (kWh/mo)", get_str("per_panel_monthly_total")),
    ]
    add_table(system)

    if c.get("include_battery"):
        # --- Battery Details ---
        section_header("Battery Details")
        battery = [
            ("Battery Capacity (kWh)", get_str("Battery Capacity (kWh)")),
            ("Battery Price (RM)", get_str("Battery Price (RM)")),
        ]
        add_table(battery)

    # --- Key Metrics ---
    section_header("Key Metrics")
    metrics = [
        ("Monthly Generation (kWh)", get_str("monthly_gen_kwh")),
        ("Daytime Saving (kWh/day)", get_str("Daytime Saving (kWh)")),
        ("Daily Saving (RM)", get_str("Daily Saving (RM)")),
        ("Monthly Saving (RM)", get_str("Monthly Saving (RM)")),
        ("Yearly Saving (RM)", get_str("Yearly Saving (RM)")),
        ("New Monthly Bill (RM)", get_str("new_monthly")),
    ]
    add_table(metrics)

    # # --- Financial Summary ---
    # section_header("Financial Summary")
    # fin = [
    #     ("Total System Cost (Cash)", f"RM {get_str('Total Cost (RM)')}"),
    #     ("Installment (8% Interest)", f"RM {get_str('Installment 8% Interests')}"),
    #     ("Installment (4 Years / Month)", f"RM {get_str('Installment 4 Years (RM)')}"),
    #     ("ROI (Cash)", f"{get_str('roi_cash')} years"),
    #     ("ROI (Credit)", f"{get_str('roi_cc')} years"),
    # ]
    # add_table(fin)

    # --- Environmental Impact ---
    section_header("Environmental Impact")
    env = [
        ("Fossil Fuel Saved (kg)", get_str("total_fossil")),
        ("Trees Saved", get_str("total_trees")),
        ("CO2 Avoided (t)", get_str("total_co2")),
    ]
    add_table(env)

    # --- Footer ---
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 5,
        "Note: Figures are estimates and may vary based on site conditions, weather, and system performance.",
        align="L"
    )

    # --- Output PDF correctly ---
    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, str):  # old FPDF
        pdf_bytes = pdf_bytes.encode("latin-1")
    elif isinstance(pdf_bytes, bytearray):  # new FPDF
        pdf_bytes = bytes(pdf_bytes)

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
                # 🔄 Reset old calculation states before new one
                for key in [
                    "calculated", "bill", "solar_result", "daytime_option",
                    "recommended_panels", "pkg", "c", "raw_needed"
                ]:
                    if key in st.session_state:
                        del st.session_state[key]

                # 💡 Now store new input
                st.session_state.bill = bill_val
                st.session_state.calculated = True
                st.session_state.reset_daytime = True

                # 🔑 Clear bill input field
                if "bill_input" in st.session_state:
                    del st.session_state["bill_input"]

                # 🔁 Force refresh with new result
                st.rerun()
            else:
                st.warning("Please enter a positive number.")


    if st.session_state.calculated:
        bill = st.session_state.bill

        st.subheader("📦 Solar Panel Package Selection")

        # --- Step 2: Tariff selection based on bill ---
        if bill <= 666.45:
            GENERAL_TARIFF = 0.4443
        elif bill >= 816.45:
            GENERAL_TARIFF = 0.5443
        else:
            st.warning("⚠️ Please enter a bill below RM 666.45 or above RM 816.45.")
            st.stop()

        # --- Step 3: Constants ---
        PANEL_WATT = 640

        # --- Step 4: Estimate monthly consumption ---
        est_kwh = bill / GENERAL_TARIFF  # total kWh/month (approx)

        # --- Step 5: Daytime usage selection ---
        daytime_option = st.radio(
            "Select estimated daytime usage portion:",
            options=[0.2, 0.3, 0.5, 0.7],
            index=[0.2, 0.3, 0.5, 0.7].index(st.session_state.get("daytime_option", 0.7) if st.session_state.get("daytime_option", 0.7) in [0.2, 0.3, 0.5, 0.7] else 0.7),
            format_func=lambda x: f"{int(x*100)}% daytime usage",
            horizontal=True,
            help="Estimate how much of your solar energy is used directly during the day."
        )
        st.session_state.daytime_option = daytime_option

        # --- Step 6: Solar generation per panel (kWh/month) ---
        per_panel_monthly_total = (PANEL_WATT / 1000) * sunlight_hours * 30

        # --- Step 7: Recommended number of panels ---
        raw_needed = math.ceil(est_kwh / per_panel_monthly_total)

        # Force even number
        if raw_needed % 2 != 0:
            raw_needed += 1

        # Add +2 panels if daytime usage is 20% or 30%
        if daytime_option in [0.2, 0.3]:
            raw_needed += 2

        # Keep within 10–100 range
        recommended = min(max(raw_needed, 10), 100)

        # Reset slider if sunlight changed
        if "last_sunlight" not in st.session_state or st.session_state.last_sunlight != sunlight_hours:
            st.session_state.pkg = recommended
            st.session_state.last_sunlight = sunlight_hours

        # Reset slider if daytime option changed
        if "last_daytime_option" not in st.session_state or st.session_state.last_daytime_option != daytime_option:
            st.session_state.pkg = recommended
            st.session_state.last_daytime_option = daytime_option

        # --- Step 8: Panel count slider ---
        pkg = st.slider(
            "Number of panels:",
            min_value=10,
            max_value=100,
            step=2,
            value=st.session_state.get("pkg", recommended),
            help=f"Recommended to slightly exceed your RM {bill:.0f} monthly usage ({est_kwh:.0f} kWh)."
        )

        # Safety: ensure even
        if pkg % 2 != 0:
            pkg += 1

        st.session_state.pkg = pkg

        # --- Battery option ---
        include_battery = st.checkbox("🔋 Include Battery Storage?", value=st.session_state.get("include_battery", False))
        st.session_state.include_battery = include_battery

        battery_kwh = 0
        battery_price = 0

        if include_battery:
            solar_capacity_kw = (pkg * PANEL_WATT) / 1000
            est_capacity = solar_capacity_kw * 2
            battery_kwh = max(10, math.floor(est_capacity / 5) * 5)
            battery_price = (battery_kwh / 5) * 3300

        st.session_state.battery_kwh = battery_kwh
        st.session_state.battery_price = battery_price

        # --- Step 9: Solar generation & battery logic ---
        total_solar_kwh = per_panel_monthly_total * pkg

        # Daily values
        daily_solar = total_solar_kwh / 30
        daily_usage = est_kwh / 30
        daily_day_use = daily_usage * daytime_option
        daily_night_use = daily_usage * (1 - daytime_option)

        # Direct daytime usage
        direct_used_day = min(daily_solar, daily_day_use)
        excess_after_day = daily_solar - direct_used_day

        # Battery charging
        if include_battery:
            battery_capacity = battery_kwh
            battery_store = min(excess_after_day, battery_capacity)
            solar_left_after_battery = excess_after_day - battery_store
        else:
            battery_store = 0
            solar_left_after_battery = excess_after_day

        # Nighttime usage offset from battery
        if include_battery:
            battery_discharge = min(battery_store, daily_night_use)
            night_from_grid = daily_night_use - battery_discharge
        else:
            battery_discharge = 0
            night_from_grid = daily_night_use

        # Export only if all battery is full
        export_kwh_daily = max(solar_left_after_battery, 0)

        # Convert back to monthly
        direct_used_kwh = direct_used_day * 30
        battery_charge_kwh = battery_store * 30
        battery_to_night_kwh = battery_discharge * 30
        night_from_grid_kwh = night_from_grid * 30
        exported_kwh = export_kwh_daily * 30

        # --- Step 10: Savings calculations ---
        export_rate = 0.20

        direct_saving_rm = direct_used_kwh * GENERAL_TARIFF
        battery_saving_rm = battery_to_night_kwh * GENERAL_TARIFF
        export_credit_rm = exported_kwh * export_rate

        total_saving_rm = direct_saving_rm + battery_saving_rm + export_credit_rm

        # --- Step 11: Bill calculation using NIGHT FROM GRID ---
        def get_energy_charge_rate(monthly_bill):
            est_kwh = monthly_bill / GENERAL_TARIFF
            return 0.2703 if est_kwh <= 1500 else 0.3703

        energy_charge_rm = night_from_grid_kwh * get_energy_charge_rate(bill)
        network_charge_rm = night_from_grid_kwh * 0.1285
        capacity_charge_rm = night_from_grid_kwh * 0.0455
        retail_charge_rm = 10.0

        # Apply export credit to energy charge
        energy_charge_after_offset = max(energy_charge_rm - export_credit_rm, 0)

        subtotal_rm = (
            energy_charge_after_offset
            + network_charge_rm
            + capacity_charge_rm
            + retail_charge_rm
        )

        kwtbb_rm = subtotal_rm * 0.016
        after_kwtbb_rm = subtotal_rm + kwtbb_rm
        sst_rm = after_kwtbb_rm * 0.08

        final_new_bill_rm = after_kwtbb_rm + sst_rm

        estimated_saving_rm = max(bill - final_new_bill_rm, 0)

        # --- Step 12: Summary ---
        st.success(
            f"""
            💰 **Estimated Monthly Saving:** RM {estimated_saving_rm:,.2f}  
            🧾 **New Bill (after solar):** RM {final_new_bill_rm:,.2f}  
            ☀️ **Solar Generation:** {total_solar_kwh:.0f} kWh/month  
            🔋 Battery Charge: {battery_charge_kwh:.0f} kWh/month  
            🌙 Nighttime Offset from Battery: {battery_to_night_kwh:.0f} kWh/month  
            📤 Exported Energy: {exported_kwh:.0f} kWh/month  
            Recommended Panels: **{recommended}**
            """
        )

        st.markdown(
            f"_Note: Savings depend on your actual daytime consumption, nighttime usage, and export credit rate._",
            unsafe_allow_html=True
        )

        # --- Your calculate_values integration ---
        c = calculate_values(pkg, sunlight_hours if sunlight_hours else 3.5, bill, daytime_option)

        if include_battery:
            # Parsing helper
            def parse_float(val):
                try:
                    return float(str(val).replace(",", ""))
                except:
                    return 0.0

            cost_cash_val = parse_float(c.get("Total Cost (RM)", 0))
            battery_price_val = float(battery_price) if include_battery else 0

            total_cost_with_battery = cost_cash_val + battery_price_val

            interest_rate = 0.08
            months = 48
            installment_total = total_cost_with_battery * (1 + interest_rate)
            installment_monthly = installment_total / months

            yearly_saving_rm = parse_float(c.get("Yearly Saving (RM)", 0))
            roi_cash_years = total_cost_with_battery / yearly_saving_rm if yearly_saving_rm else float("inf")
            roi_cc_years = installment_total / yearly_saving_rm if yearly_saving_rm else float("inf")

            c["Total Cost (RM)"] = f"{total_cost_with_battery:,.0f}"
            c["Installment 8% Interests"] = f"{installment_total:,.0f}"
            c["Installment 4 Years (RM)"] = f"{installment_monthly:,.2f}"
            c["roi_cash"] = f"{roi_cash_years:.2f}".rstrip("0").rstrip(".")
            c["roi_cc"] = f"{roi_cc_years:.2f}".rstrip("0").rstrip(".")
            c['include_battery'] = include_battery
            c['new_monthly'] = f"{final_new_bill_rm:,.0f}"
            c["Monthly Saving (RM)"] = f"{estimated_saving_rm:,.0f}"

        # # --- 5) O&M rounding logic ---
        # raw_sav = float(str(c["Monthly Saving (RM)"]).replace(",", ""))
        # rem = raw_sav % 100
        # base_hund = raw_sav - rem

        # if rem > 40:
        #     om_fee = base_hund + 100
        # else:
        #     om_fee = base_hund

        # om_fee = max(500, min(om_fee, 1000))  # clamp
        # c["O&M Fee (RM)"] = om_fee

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

        # Show battery info if applicable
        if c.get("include_battery"):
            st.markdown(f"""
            <div class="grid-container">
            <div class="card"><div class="title">Battery Storage</div><div class="value">{c['Battery Capacity (kWh)']} kWh</div></div>
            <div class="card"><div class="title">Battery Cost</div><div class="value">RM {c['Battery Price (RM)']}</div></div>
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
        """, unsafe_allow_html=True)

        # Show battery info if applicable
        if c.get("include_battery"):
            st.markdown(f"""
            <div class="grid-container">
            <div class="card"><div class="title">Battery Storage</div><div class="value">{c['Battery Capacity (kWh)']} kWh</div></div>
            <div class="card"><div class="title">Battery Cost</div><div class="value">RM {c['Battery Price (RM)']}</div></div>
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

        # --- Step 11: Display results ---
        st.markdown(
            f"""
            ## ☀️ Solar Generation & Usage
            - **Monthly consumption:** {est_kwh:.0f} kWh  
            - **Total solar generation:** {total_solar_kwh:.0f} kWh/month  
            - **Direct daytime usage:** {direct_used_kwh:.0f} kWh × RM {GENERAL_TARIFF:.4f} = RM {direct_saving_rm:.2f}  
            {"- **Battery discharge (nighttime offset):** " + f"{battery_to_night_kwh:.0f} kWh × RM {GENERAL_TARIFF:.4f} = RM {battery_saving_rm:.2f}" if include_battery else ""}
            - **Exported:** {exported_kwh:.0f} kWh × RM {export_rate:.4f} = RM {export_credit_rm:.2f}  

            ## 🔋 Battery Flow Breakdown {("(Enabled)" if include_battery else "(Not used)")}
            - **Battery capacity:** {battery_kwh:.0f} kWh  
            - **Solar stored into battery:** {battery_charge_kwh:.0f} kWh/month  
            - **Battery discharged at night:** {battery_to_night_kwh:.0f} kWh/month  
            - **Nighttime grid usage:** {night_from_grid_kwh:.0f} kWh/month  

            ## 🧾 New Monthly Bill Breakdown (with Formulas)
            ### 🌙 Nighttime Charges (after battery offset)
            **Nighttime kWh (from grid):** {night_from_grid_kwh:.0f}

            | Charge Type | Formula | Amount (RM) |
            |--------------|----------|-------------|
            | Energy Charge | {night_from_grid_kwh:.0f} × {get_energy_charge_rate(bill):.4f} | {energy_charge_rm:.2f} |
            | Network Charge | {night_from_grid_kwh:.0f} × 0.1285 | {network_charge_rm:.2f} |
            | Capacity Charge | {night_from_grid_kwh:.0f} × 0.0455 | {capacity_charge_rm:.2f} |
            | Retail Charge | Flat RM 10 | {retail_charge_rm:.2f} |
            | Export Credit | - {exported_kwh:.0f} × {export_rate:.4f} | -{export_credit_rm:.2f} |

            **Subtotal (before tax)** = (Energy + Network + Capacity + Retail - Export)  
            → **RM {subtotal_rm:.2f}**

            ### ⚡ Taxes & Fees
            - **KWTBB (1.6%)** = {subtotal_rm:.2f} × 1.6% = **RM {kwtbb_rm:.2f}**  
            - **After KWTBB:** RM {after_kwtbb_rm:.2f}  
            - **SST (8%)** = {after_kwtbb_rm:.2f} × 8% = **RM {sst_rm:.2f}**  
            - **Final New Monthly Bill:** **RM {final_new_bill_rm:.2f}**
            """,
            unsafe_allow_html=True
        )



if __name__ == "__main__":
    main()