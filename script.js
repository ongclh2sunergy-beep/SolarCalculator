function calculateSolar() {
    const bill = parseFloat(document.getElementById('bill').value);
  
    if (isNaN(bill) || bill <= 0) {
      alert("Please enter a valid bill amount.");
      return;
    }
  
    // Constants
    const tariff = 0.50; // MYR per kWh
    const sunlightHours = 4; // avg per day
    const costPerKW = 5000; // MYR per kW
    const panelWatt = 550; // W
    const systemLife = 25; // years
  
    // Calculations
    const monthlyUsageKWh = bill / tariff;
    const recommendedKW = (monthlyUsageKWh) / (sunlightHours * 30);
    const panelsNeeded = Math.ceil(recommendedKW * 1000 / panelWatt);
    const installCost = recommendedKW * costPerKW;
    const monthlySavings = bill; // Assuming 100% offset
    const yearlySavings = monthlySavings * 12;
    const payback = installCost / yearlySavings;
    const lifetimeSavings = yearlySavings * systemLife;
    const roi = ((lifetimeSavings - installCost) / installCost) * 100;
    const annualGen = recommendedKW * sunlightHours * 365;
    const monthlyGen = annualGen / 12;
    const offsetPercent = Math.min(100, (monthlyGen * tariff) / bill * 100);
  
    // Display
    document.getElementById('results').innerHTML = `
      <p><strong>Recommended Solar Capacity:</strong> ${recommendedKW.toFixed(2)} kW</p>
      <p><strong>Suggested Number of Panels:</strong> ${panelsNeeded} panels (550W each)</p>
      <p><strong>Total Installation Cost:</strong> MYR ${installCost.toFixed(0)}</p>
      <p><strong>Estimated Monthly Savings:</strong> MYR ${monthlySavings.toFixed(0)}</p>
      <p><strong>Estimated Yearly Savings:</strong> MYR ${yearlySavings.toFixed(0)}</p>
      <p><strong>Payback Period:</strong> ${payback.toFixed(1)} years</p>
      <p><strong>Estimated Lifetime Savings:</strong> MYR ${lifetimeSavings.toFixed(0)}</p>
      <p><strong>Return on Investment:</strong> ${roi.toFixed(1)}%</p>
      <p><strong>Estimated Solar Generation:</strong> ${annualGen.toFixed(0)} kWh/year, ${monthlyGen.toFixed(0)} kWh/month</p>
      <p><strong>Bill Offset:</strong> ${offsetPercent.toFixed(1)}%</p>
    `;
  }