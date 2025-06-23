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

# === Hard-coded price table ===
price_table = {
    10: 21000,
    14: 26000,
    20: 34000,
    30: 43000,
    40: 52000
}

def generate_calculations(bill, no_sun_days, user_panels):
    tariff = 0.63
    sunlight_hours = 3.62
    panel_watt = 615
    system_life = 25

    # Adjust for cloudy/rainy days
    sunny_days = 30 - no_sun_days
    adjusted_sun = (sunny_days*sunlight_hours + no_sun_days*sunlight_hours*0.1)/30

    monthly_kwh = bill / tariff
    chosen_kw = user_panels * panel_watt / 1000
    annual_gen = chosen_kw * adjusted_sun * 365
    monthly_gen = annual_gen / 12
    kWac = chosen_kw * 0.77

    # Fixed 20% daytime consumption
    daytime_need_kwh = monthly_kwh * 0.20
    solar_for_consumption = min(monthly_gen, daytime_need_kwh)
    solar_offset_kwh = monthly_gen - solar_for_consumption

    # Savings & ROI
    monthly_savings = solar_offset_kwh * tariff
    yearly_savings = monthly_savings * 12
    install_cost = price_table[user_panels]
    payback = install_cost / yearly_savings if yearly_savings else 0
    lifetime_sav = yearly_savings * system_life
    roi_cc = (lifetime_sav - install_cost) / install_cost * 100
    roi_cash = (lifetime_sav - (install_cost - 2000)) / (install_cost - 2000) * 100
    new_monthly_bill = bill - monthly_savings

    # Environmental impact
    total_fossil = chosen_kw * 350
    total_trees = chosen_kw * 2
    total_co2 = chosen_kw * 0.85

    return {
        "monthly_gen": monthly_gen,
        "chosen_kw": chosen_kw,
        "kWac": kWac,
        "monthly_savings": monthly_savings,
        "yearly_savings": yearly_savings,
        "payback": payback,
        "roi_cc": roi_cc,
        "roi_cash": roi_cash,
        "new_monthly_bill": new_monthly_bill,
        "total_fossil": total_fossil,
        "total_trees": total_trees,
        "total_co2": total_co2
    }

def main():
    st.title("☀️ Solar Savings Calculator")

    if 'calc_trigger' not in st.session_state:
        st.session_state.calc_trigger = False

    # === INPUT FORM ===
    with st.form("solar_form"):
        bill_input = st.text_input("Enter your average monthly electricity bill (MYR):")
        submit = st.form_submit_button("Calculate Solar Savings")

    bill = None
    if bill_input:
        try:
            bill = float(bill_input)
            if bill < 0:
                st.error("Bill cannot be negative.")
                bill = None
        except ValueError:
            st.error("Please enter a valid number.")

    if submit:
        st.session_state.calc_trigger = bool(bill and bill > 0)
        if st.session_state.calc_trigger:
            st.session_state.bill = bill

    # === CALC & DISPLAY ===
    if st.session_state.calc_trigger:
        bill = st.session_state.bill

        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            no_sun_days = st.selectbox("No-sun days per month:", [0,15,30], index=1)

        # Panel selection
        allowed_panels = [10,14,20,30,40]
        monthly_kwh = bill / 0.63
        rec_kw = monthly_kwh / (3.62 * 30)
        raw_panels = int(-(-rec_kw * 1000 // 615))
        suggested = next((p for p in allowed_panels if p>=raw_panels), allowed_panels[-1])
        user_panels = st.selectbox(
            "Choose your package (or keep recommended):",
            allowed_panels, index=allowed_panels.index(suggested)
        )

        calc = generate_calculations(bill, no_sun_days, user_panels)

        # === GLOBAL CARD CSS ===
        st.markdown("""
        <style>
          .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
          }
          .card {
            background: #ffffff;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
          }
          .card .title {
            font-size: 0.85rem;
            color: #555;
            margin-bottom: 6px;
          }
          .card .value {
            font-size: 1.2rem;
            font-weight: bold;
            color: #222;
          }
        </style>
        """, unsafe_allow_html=True)

        # === KEY METRICS ===
        st.subheader("📈 Key Metrics")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Previous Bill</div><div class="value">RM {bill:.2f}</div></div>
          <div class="card"><div class="title">New Bill After Solar</div><div class="value">RM {calc['new_monthly_bill']:.2f}</div></div>
          <div class="card"><div class="title">Monthly Savings</div><div class="value">RM {calc['monthly_savings']:.2f}</div></div>
          <div class="card"><div class="title">ROI (CC)</div><div class="value">{calc['roi_cc']:.2f}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === PANEL & SAVINGS SUMMARY ===
        st.subheader("🔧 Panel & Savings Summary")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Saving per PV</div><div class="value">RM {calc['monthly_savings']/user_panels:.2f}</div></div>
          <div class="card"><div class="title">Panel Qty</div><div class="value">{user_panels}</div></div>
          <div class="card"><div class="title">Installed kWp</div><div class="value">{calc['chosen_kw']:.2f} kWp</div></div>
          <div class="card"><div class="title">kWac</div><div class="value">{calc['kWac']:.2f} kW</div></div>
          <div class="card"><div class="title">Solar Price (CC)</div><div class="value">RM {price_table[user_panels]:.2f}</div></div>
          <div class="card"><div class="title">Solar Price (Cash)</div><div class="value">RM {price_table[user_panels]-2000:.2f}</div></div>
          <div class="card"><div class="title">Inverter Qty</div><div class="value">1 Unit</div></div>
          <div class="card"><div class="title">O&M (Yearly)</div><div class="value">RM 800.00</div></div>
          <div class="card"><div class="title">Microinverters</div><div class="value">5.00 units</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === FINANCIAL SUMMARY ===
        st.subheader("💰 Financial Summary")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Total Sav/Month</div><div class="value">RM {calc['monthly_savings']:.2f}</div></div>
          <div class="card"><div class="title">Total Sav/Year</div><div class="value">RM {calc['yearly_savings']:.2f}</div></div>
          <div class="card"><div class="title">Payback Period</div><div class="value">{calc['payback']:.2f} yrs</div></div>
          <div class="card"><div class="title">ROI (Cash)</div><div class="value">{calc['roi_cash']:.2f}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        # === ENVIRONMENTAL BENEFITS ===
        st.subheader("🌳 Environmental Benefits")
        st.markdown(f"""
        <div class="grid-container">
          <div class="card"><div class="title">Per 1 kWp<br>Fossil Fuel</div><div class="value">350.00 kg</div></div>
          <div class="card"><div class="title">Per 1 kWp<br>Trees Saved</div><div class="value">2.00</div></div>
          <div class="card"><div class="title">Per 1 kWp<br>CO₂</div><div class="value">0.85 t</div></div>
          <div class="card"><div class="title">Total {calc['chosen_kw']:.2f} kWp<br>Fossil Fuel</div><div class="value">{calc['total_fossil']:.2f} kg</div></div>
          <div class="card"><div class="title">Total Trees Saved</div><div class="value">{calc['total_trees']:.2f}</div></div>
          <div class="card"><div class="title">Total CO₂</div><div class="value">{calc['total_co2']:.2f} t</div></div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()