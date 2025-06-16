import streamlit as st

def main():
    st.title("☀️ Solar Savings Calculator")

    st.write("Enter your average monthly electricity bill (MYR):")
    bill = st.number_input("Monthly Bill (MYR)", min_value=0.0, step=10.0)

    if bill > 0:
        # Constants
        tariff = 0.50
        sunlight_hours = 4
        cost_per_kw = 5000
        panel_watt = 550
        system_life = 25

        # Calculation
        monthly_usage_kwh = bill / tariff
        recommended_kw = monthly_usage_kwh / (sunlight_hours * 30)
        panels_needed = int(-(-recommended_kw * 1000 // panel_watt))  # ceil without math.ceil
        install_cost = recommended_kw * cost_per_kw
        monthly_savings = bill
        yearly_savings = monthly_savings * 12
        payback = install_cost / yearly_savings
        lifetime_savings = yearly_savings * system_life
        roi = ((lifetime_savings - install_cost) / install_cost) * 100
        annual_gen = recommended_kw * sunlight_hours * 365
        monthly_gen = annual_gen / 12
        offset_percent = min(100, (monthly_gen * tariff) / bill * 100)

        # Price table
        price_table = {
            10: 21000,
            14: 26000,
            20: 34000,
            30: 43000,
            40: 52000
        }

        custom_price = price_table.get(panels_needed, "N/A")

        # Results
        st.subheader("📊 Results")
        st.write(f"**Recommended Solar Capacity:** {recommended_kw:.2f} kW")
        st.write(f"**Suggested Number of Panels:** {panels_needed} panels")
        st.write(f"**Estimated Installation Cost:** MYR {install_cost:,.0f}")
        if custom_price != "N/A":
            st.write(f"**Package Price (for {panels_needed} panels):** MYR {custom_price:,}")
        st.write(f"**Estimated Monthly Savings:** MYR {monthly_savings:.0f}")
        st.write(f"**Estimated Yearly Savings:** MYR {yearly_savings:.0f}")
        st.write(f"**Payback Period:** {payback:.1f} years")
        st.write(f"**Lifetime Savings (25 years):** MYR {lifetime_savings:,.0f}")
        st.write(f"**ROI:** {roi:.1f}%")
        st.write(f"**Estimated Solar Generation:** {annual_gen:.0f} kWh/year")
        st.write(f"**Bill Offset:** {offset_percent:.1f}%")

if __name__ == "__main__":
    main()