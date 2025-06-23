# import streamlit as st

# def main():
#     st.title("☀️ Solar Savings Calculator")

#     # Initialize session state
#     if 'calc_trigger' not in st.session_state:
#         st.session_state.calc_trigger = False

#     # === FORM SECTION ===
#     with st.form("solar_form"):
#         bill_input = st.text_input("Enter your average monthly electricity bill (MYR):")
#         submit = st.form_submit_button("Calculate Solar Savings")

#     # === VALIDATION ===
#     bill = None
#     if bill_input:
#         try:
#             bill = float(bill_input)
#             if bill < 0:
#                 st.error("Bill cannot be negative.")
#                 bill = None
#         except ValueError:
#             st.error("Please enter a valid number.")

#     # Only set calc_trigger on submit
#     if submit:
#         if bill is None or bill <= 0:
#             st.warning("Please enter a valid monthly bill greater than 0 to perform calculation.")
#             st.session_state.calc_trigger = False
#         else:
#             if bill and bill > 0:
#                 st.session_state.calc_trigger = True
#                 st.session_state.bill = bill
#             else:
#                 st.session_state.calc_trigger = False

#     # === MAIN CALCULATION & DISPLAY ===
#     if st.session_state.calc_trigger:
#         bill = st.session_state.bill

#         # ─── Constants ───
#         tariff = 0.63            # MYR per kWh
#         sunlight_hours = 3.62    # avg sun hours/day
#         panel_watt = 615         # W per panel
#         system_life = 25         # years

#         price_table = {10:21000, 14:26000, 20:34000, 30:43000, 40:52000}
#         allowed_panels = [10, 14, 20, 30, 40]

#         # ─── Advanced Settings ───
#         with st.expander("⚙️ Advanced Settings"):
#             st.subheader("🌧️ No-Sun Day Configuration")
#             no_sun_days = st.selectbox("No-sun days per month:", [0, 15, 30], index=1)

#         # Adjusted sunlight
#         sunny_days = 30 - no_sun_days
#         adjusted_sun = (sunny_days*sunlight_hours + no_sun_days*sunlight_hours*0.1) / 30

#         # ─── Panel Package ───
#         st.subheader("📦 Solar Panel Package Selection")
#         monthly_kwh = bill / tariff
#         rec_kw = monthly_kwh / (sunlight_hours * 30)
#         raw_panels = int(-(-rec_kw*1000 // panel_watt))  # ceiling
#         suggested = next((p for p in allowed_panels if p >= raw_panels), allowed_panels[-1])

#         user_panels = st.selectbox(
#             "Choose your package (or keep recommended):",
#             allowed_panels,
#             index=allowed_panels.index(suggested)
#         )

#         install_cost = price_table[user_panels]
#         cash_price = install_cost - 2000

#         # ─── Generation ───
#         chosen_kw = user_panels * panel_watt / 1000
#         annual_gen = chosen_kw * adjusted_sun * 365
#         monthly_gen = annual_gen / 12

#         # ─── Daytime Consumption Logic ───
#         # Fixed 20% of your usage happens in daylight
#         daytime_need_kwh = monthly_kwh * 0.20
#         # Solar serving that consumption:
#         solar_for_consumption = min(monthly_gen, daytime_need_kwh)
#         # Remaining solar offsets your bill:
#         solar_offset_kwh = monthly_gen - solar_for_consumption

#         # ─── Savings & ROI ───
#         monthly_savings = solar_offset_kwh * tariff
#         yearly_savings = monthly_savings * 12
#         payback = install_cost / yearly_savings if yearly_savings else 0
#         lifetime_sav = yearly_savings * system_life
#         roi = ((lifetime_sav - install_cost) / install_cost) * 100 if install_cost else 0
#         offset_pct = min(100, (solar_offset_kwh * tariff) / bill * 100)

#         # ─── Previous vs New Bill ───
#         new_monthly_bill = bill - monthly_savings

#         # ─── DISPLAY ───
#         st.subheader("📊 Results")
#         st.markdown("""
#         <style>
#           .grid-container {
#             display: grid;
#             grid-template-columns: repeat(2, minmax(0, 1fr));
#             gap: 12px;
#           }
#           .card {
#             background-color: #f0f2f6;
#             border-radius: 12px;
#             padding: 16px;
#             box-shadow: 0 1px 3px rgba(0,0,0,0.05);
#           }
#           .card-title {
#             font-size: 14px;
#             color: #555;
#             margin-bottom: 4px;
#           }
#           .card-value {
#             font-size: 18px;
#             font-weight: bold;
#             color: #222;
#           }
#         </style>
#         """, unsafe_allow_html=True)

#         html = f"""
#         <div class="grid-container">
#           <div class="card"><div class="card-title">Previous Monthly Bill</div><div class="card-value">MYR {bill:,.2f}</div></div>
#           <div class="card"><div class="card-title">New Monthly Bill</div><div class="card-value">MYR {new_monthly_bill:,.2f}</div></div>
#           <div class="card"><div class="card-title">Recommended Capacity</div><div class="card-value">{rec_kw:.2f} kW</div></div>
#           <div class="card"><div class="card-title">Panels Needed</div><div class="card-value">{raw_panels} panels</div></div>
#           <div class="card"><div class="card-title">Selected Package</div><div class="card-value">{user_panels} panels</div></div>
#           <div class="card"><div class="card-title">Installation Cost</div><div class="card-value">MYR {install_cost:,.0f}</div></div>
#           <div class="card"><div class="card-title">Cash Price</div><div class="card-value">MYR {cash_price:,.0f}</div></div>
#           <div class="card"><div class="card-title">Monthly Generation</div><div class="card-value">{monthly_gen:.0f} kWh</div></div>
#           <div class="card"><div class="card-title">Solar for Daytime Consumption</div><div class="card-value">{solar_for_consumption:.0f} kWh</div></div>
#           <div class="card"><div class="card-title">Solar Offset</div><div class="card-value">{solar_offset_kwh:.0f} kWh</div></div>
#           <div class="card"><div class="card-title">Monthly Savings</div><div class="card-value">MYR {monthly_savings:.2f}</div></div>
#           <div class="card"><div class="card-title">Payback Period</div><div class="card-value">{payback:.1f} yrs</div></div>
#           <div class="card"><div class="card-title">ROI</div><div class="card-value">{roi:.1f}%</div></div>
#           <div class="card"><div class="card-title">Bill Offset</div><div class="card-value">{offset_pct:.1f}%</div></div>
#         </div>
#         """
#         st.markdown(html, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()

import streamlit as st

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

    # 4) Financials
    cost_cc        = PRICE_TABLE[package_panels]
    cost_cash      = cost_cc - 2000
    monthly_save   = offset_kwh * TARIFF_MYR_PER_KWH
    yearly_save    = monthly_save * 12
    payback_cc     = cost_cc  / yearly_save  if yearly_save else 0
    payback_cash   = cost_cash/ yearly_save  if yearly_save else 0
    lifetime_sav   = yearly_save * SYSTEM_LIFE_YEARS
    roi_cc_pct     = (lifetime_sav - cost_cc)   / cost_cc   * 100
    roi_cash_pct   = (lifetime_sav - cost_cash) / cost_cash * 100
    new_monthly    = bill_myr - monthly_save

    # 5) Environmental
    total_fossil = kwp_installed * 350
    total_trees  = kwp_installed * 2
    total_co2    = kwp_installed * 0.85

    return {
        "monthly_save": monthly_save,
        "yearly_save":  yearly_save,
        "payback_cc":   payback_cc,
        "payback_cash": payback_cash,
        "roi_cc":       roi_cc_pct,
        "roi_cash":     roi_cash_pct,
        "new_monthly":  new_monthly,
        "kwp_installed":kwp_installed,
        "monthly_gen":  monthly_gen_kwh,
        "kwac":         kwac,
        "cost_cc":      cost_cc,
        "cost_cash":    cost_cash,
        "total_fossil": total_fossil,
        "total_trees":  total_trees,
        "total_co2":    total_co2
    }

def main():
    st.title("☀️ Solar Savings Calculator")

    if 'calculated' not in st.session_state:
        st.session_state.calculated = False

    # === INPUT FORM ===
    with st.form("solar_form"):
        bill_input = st.text_input("Monthly Electricity Bill (MYR):")
        submitted  = st.form_submit_button("Calculate")

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
        allowed     = list(PRICE_TABLE.keys())
        rec_kwh     = bill / TARIFF_MYR_PER_KWH
        rec_kwp     = rec_kwh / (SUNLIGHT_HOURS * 30)
        raw_needed  = int(-(-rec_kwp*1000 // PANEL_WATT))
        recommended = next((p for p in allowed if p>=raw_needed), allowed[-1])
        pkg         = st.selectbox(
            "Choose package size (panels):", allowed, index=allowed.index(recommended)
        )

        # Perform calculations
        c = generate_calculations(bill, no_sun_days, pkg)

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

if __name__ == "__main__":
    main()