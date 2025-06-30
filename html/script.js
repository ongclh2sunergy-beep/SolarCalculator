function calculateSolar() {
    const bill = parseFloat(document.getElementById('bill').value);
    if (isNaN(bill) || bill <= 0) {
      alert("Please enter a valid bill amount.");
      return;
    }
  
    const tariff = 0.50;
    const sunlightHours = 4;
    const costPerKW = 5000;
    const panelWatt = 550;
    const systemLife = 25;
  
    const monthlyUsageKWh = bill / tariff;
    const recommendedKW = (monthlyUsageKWh) / (sunlightHours * 30);
    const panelsNeeded = Math.ceil(recommendedKW * 1000 / panelWatt);
  
    // Determine price based on pcs
    const panelPriceList = [
      { pcs: 10, price: 21000 },
      { pcs: 14, price: 26000 },
      { pcs: 20, price: 34000 },
      { pcs: 30, price: 43000 },
      { pcs: 40, price: 52000 }
    ];
  
    let selectedPrice = null;
    let selectedPcs = null;
  
    for (let i = 0; i < panelPriceList.length; i++) {
      if (panelsNeeded <= panelPriceList[i].pcs) {
        selectedPcs = panelPriceList[i].pcs;
        selectedPrice = panelPriceList[i].price;
        break;
      }
    }
  
    if (selectedPrice === null) {
      selectedPcs = panelPriceList[panelPriceList.length - 1].pcs;
      selectedPrice = panelPriceList[panelPriceList.length - 1].price;
    }
  
    const monthlySavings = bill;
    const yearlySavings = monthlySavings * 12;
    const payback = selectedPrice / yearlySavings;
    const lifetimeSavings = yearlySavings * systemLife;
    const roi = ((lifetimeSavings - selectedPrice) / selectedPrice) * 100;
    const annualGen = recommendedKW * sunlightHours * 365;
    const monthlyGen = annualGen / 12;
    const offsetPercent = Math.min(100, (monthlyGen * tariff) / bill * 100);
  
    const results = `
      <div class="result-box"><div class="value">RM${(monthlySavings * 0.93).toFixed(0)} - RM${monthlySavings.toFixed(0)}</div><div class="label">Monthly Savings</div></div>
      <div class="result-box"><div class="value">RM${(yearlySavings * 0.93).toFixed(0)} - RM${yearlySavings.toFixed(0)}</div><div class="label">Yearly Savings</div></div>
      <div class="result-box"><div class="value">${recommendedKW.toFixed(2)} kW</div><div class="label">Recommended Solar Capacity</div></div>
      <div class="result-box"><div class="value">${panelsNeeded} Panels</div><div class="label">Calculated Panels Needed</div></div>
      <div class="result-box"><div class="value">${selectedPcs} Panels</div><div class="label">Suggested Package</div></div>
      <div class="result-box"><div class="value">MYR ${selectedPrice}</div><div class="label">Package Price</div></div>
      <div class="result-box"><div class="value">${payback.toFixed(1)} years</div><div class="label">Payback Period</div></div>
      <div class="result-box"><div class="value">MYR ${lifetimeSavings.toFixed(0)}</div><div class="label">Lifetime Savings</div></div>
      <div class="result-box"><div class="value">${roi.toFixed(1)}%</div><div class="label">ROI</div></div>
      <div class="result-box"><div class="value">${annualGen.toFixed(0)} kWh/year</div><div class="label">Estimated Solar Generation</div></div>
      <div class="result-box"><div class="value">${offsetPercent.toFixed(1)}%</div><div class="label">Bill Offset</div></div>
    `;
  
    document.getElementById('results').innerHTML = results;
  
    // Optional staggered delay for animations
    document.querySelectorAll('.result-box').forEach((box, i) => {
      box.style.animationDelay = `${i * 0.2}s`;
    });
  
    // Scroll to output
    document.getElementById('results').scrollIntoView({
      behavior: 'smooth'
    });
  }