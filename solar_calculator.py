import streamlit as st

def main():
    st.title("☀️ Solar Savings Calculator")

    st.write("Enter your average monthly electricity bill (MYR):")
    bill = st.number_input(
    "Monthly Bill (MYR)",
    min_value=0.0,
    step=10.0,
    placeholder="Key in your monthly bill"
)

    if bill > 0:
        # Constants
        # Electricity cost in MYR per kWh (you pay RM0.50 for 1 kWh)
        tariff = 0.50

        # Average hours of useful sunlight per day
        sunlight_hours = 3.42

        # Installation cost estimate: RM5000 for each 1 kW of solar power capacity
        cost_per_kw = 5000

        # Each solar panel generates 615 watts 
        panel_watt = 615

        # The system is assumed to last 25 years
        system_life = 25

        # Calculation
        # Your monthly energy use in kWh (bill ÷ price per kWh)
        monthly_usage_kwh = bill / tariff

        # How many kW of solar capacity needed to match your monthly usage.
        recommended_kw = monthly_usage_kwh / (sunlight_hours * 30)

        # Calculate number of panels (convert kW to watts, divide by panel size).
        panels_needed = int(-(-recommended_kw * 1000 // panel_watt))  # ceil without math.ceil

        # Total installation cost for the recommended kW.
        install_cost = recommended_kw * cost_per_kw

        # You save what you were paying — assumes solar offsets 100% of your bill.
        monthly_savings = bill

        # Annual savings (monthly savings × 12).
        yearly_savings = monthly_savings * 12

        # How many years to recover your investment.
        payback = install_cost / yearly_savings

        # Total savings over 25 years.
        lifetime_savings = yearly_savings * system_life

        # Return on investment (ROI %).
        roi = ((lifetime_savings - install_cost) / install_cost) * 100

        # How much energy your system will produce yearly (kWh).
        annual_gen = recommended_kw * sunlight_hours * 365

        # Average solar generation per month (kWh).
        monthly_gen = annual_gen / 12

        # % of your bill that solar generation covers (capped at 100%).
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

        # Show results in boxes using columns
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Recommended Solar Capacity:</strong><br> {recommended_kw:.2f} kW
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Suggested Number of Panels:</strong><br> {panels_needed} panels
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Estimated Installation Cost:</strong><br> MYR {install_cost:,.0f}
                </div>
            """, unsafe_allow_html=True)

            if custom_price != "N/A":
                st.markdown(f"""
                    <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                    <strong>Package Price (for {panels_needed} panels):</strong><br> MYR {custom_price:,}
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Estimated Monthly Savings:</strong><br> MYR {monthly_savings:.0f}
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Estimated Yearly Savings:</strong><br> MYR {yearly_savings:.0f}
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Payback Period:</strong><br> {payback:.1f} years
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Lifetime Savings (25 years):</strong><br> MYR {lifetime_savings:,.0f}
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>ROI:</strong><br> {roi:.1f}%
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Estimated Solar Generation:</strong><br> {annual_gen:.0f} kWh/year
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Bill Offset:</strong><br> {offset_percent:.1f}%
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()