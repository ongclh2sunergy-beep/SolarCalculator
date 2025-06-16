import streamlit as st

def main():
    st.title("☀️ Solar Savings Calculator")

    # Input: Monthly electricity bill
    st.write("Enter your average monthly electricity bill (MYR):")
    bill_input = st.text_input("Monthly Bill (MYR)", placeholder="Key in your monthly bill")

    bill = None
    if bill_input:
        try:
            bill = float(bill_input)
            if bill < 0:
                st.error("Bill cannot be negative.")
                bill = None
        except ValueError:
            st.error("Please enter a valid number.")

    # If we have a valid bill, proceed with calculations
    if bill is not None and bill > 0:
        # Constants
        tariff = 0.63  # MYR per kWh
        sunlight_hours = 3.42  # average hours per day
        panel_watt = 615  # each panel output in watts
        system_life = 25  # system lifespan in years

        # Price table for each package (package price replaces cost per kW calculation)
        price_table = {
            10: 21000,
            14: 26000,
            20: 34000,
            30: 43000,
            40: 52000
        }

        allowed_panels = [10, 14, 20, 30, 40]

        # Step 1: Calculate recommended system size
        monthly_usage_kwh = bill / tariff  # how much electricity you use in kWh
        recommended_kw = monthly_usage_kwh / (sunlight_hours * 30)  # kW needed

        # Step 2: Calculate minimum panels required (ceiling division)
        raw_panels_needed = int(-(-recommended_kw * 1000 // panel_watt))  # kW -> W -> panels
        suggested_panels = next((p for p in allowed_panels if p >= raw_panels_needed), allowed_panels[-1])

        # Show recommended package
        st.success(f"Recommended Package: {suggested_panels} panels")

        # Step 3: Let user choose another package if they want
        user_panels = st.selectbox(
            "Choose your package (or keep the recommended)",
            allowed_panels,
            index=allowed_panels.index(suggested_panels)
        )

        # Step 4: Determine cost and savings based on chosen package
        install_cost = price_table.get(user_panels, 0)
        monthly_savings = bill  # assume 100% offset of current bill
        yearly_savings = monthly_savings * 12
        payback = install_cost / yearly_savings if yearly_savings else 0
        lifetime_savings = yearly_savings * system_life
        roi = ((lifetime_savings - install_cost) / install_cost) * 100 if install_cost else 0

        # Step 5: Estimate energy production
        chosen_kw = user_panels * panel_watt / 1000
        annual_gen = chosen_kw * sunlight_hours * 365
        monthly_gen = annual_gen / 12
        offset_percent = min(100, (monthly_gen * tariff) / bill * 100)

        # Step 6: Display results
        st.subheader("📊 Results")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Recommended Solar Capacity:</strong><br> {recommended_kw:.2f} kW
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Your Selected Package:</strong><br> {user_panels} panels
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.2); padding:10px; border-radius:8px; background:rgba(0,0,0,0.2); color:inherit">
                <strong>Installation Cost:</strong><br> MYR {install_cost:,.0f}
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

    else:
        st.info("Please enter your monthly bill to see the calculation.")

if __name__ == "__main__":
    main()