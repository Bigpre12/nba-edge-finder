// Parlay Calculator and Recommendations UI Functions

let parlayBets = [];

function showParlayCalculator() {
    try {
        const modal = document.getElementById('parlayCalculatorModal');
        if (!modal) {
            console.error('parlayCalculatorModal element not found');
            alert('Parlay Calculator modal not found. Please refresh the page.');
            return;
        }
        modal.style.display = 'flex';
        if (parlayBets.length === 0 && typeof addBetRow === 'function') {
            addBetRow();
        }
    } catch (error) {
        console.error('Error showing parlay calculator:', error);
        alert('Error opening Parlay Calculator: ' + error.message);
    }
}

function hideParlayCalculator() {
    document.getElementById('parlayCalculatorModal').style.display = 'none';
}

function addBetRow() {
    const betsList = document.getElementById('betsList');
    const betIndex = parlayBets.length;
    
    const betRow = document.createElement('div');
    betRow.className = 'bet-row';
    betRow.innerHTML = `
        <input type="text" placeholder="Player/Team" class="bet-input" id="bet-player-${betIndex}">
        <input type="number" placeholder="Odds (-110)" class="bet-input" id="bet-odds-${betIndex}" value="-110">
        <input type="number" placeholder="Probability %" class="bet-input" id="bet-prob-${betIndex}" step="0.1">
        <button onclick="removeBetRow(${betIndex})" class="remove-bet-btn">✕</button>
    `;
    
    betsList.appendChild(betRow);
    parlayBets.push({});
    
    // Add event listeners for auto-calculation
    document.getElementById(`bet-odds-${betIndex}`).addEventListener('input', calculateParlay);
    document.getElementById(`bet-prob-${betIndex}`).addEventListener('input', calculateParlay);
}

function removeBetRow(index) {
    const betsList = document.getElementById('betsList');
    const rows = betsList.querySelectorAll('.bet-row');
    if (rows[index]) {
        rows[index].remove();
        parlayBets.splice(index, 1);
        // Re-index remaining rows
        parlayBets = parlayBets.map((bet, i) => ({ ...bet, index: i }));
        calculateParlay();
    }
}

async function calculateParlay() {
    const bets = [];
    const betsList = document.getElementById('betsList');
    const rows = betsList.querySelectorAll('.bet-row');
    
    for (let i = 0; i < rows.length; i++) {
        const odds = parseFloat(document.getElementById(`bet-odds-${i}`)?.value) || -110;
        const prob = parseFloat(document.getElementById(`bet-prob-${i}`)?.value) || 50;
        
        if (prob > 0 && prob <= 100) {
            bets.push({
                odds: odds,
                probability: prob
            });
        }
    }
    
    if (bets.length < 2) {
        document.getElementById('calculatorResults').innerHTML = 
            '<p class="calc-message">Add at least 2 bets to calculate parlay</p>';
        return;
    }
    
    try {
        const response = await fetch('/api/parlay-calculator', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bets: bets, odds_format: 'american'})
        });
        
        const data = await response.json();
        
        if (data.success && data.payout.valid) {
            const payout = data.payout;
            document.getElementById('calculatorResults').innerHTML = `
                <div class="calc-result-card">
                    <div class="calc-row">
                        <span>Combined Probability:</span>
                        <span class="calc-value">${payout.combined_probability}%</span>
                    </div>
                    <div class="calc-row">
                        <span>Parlay Odds:</span>
                        <span class="calc-value">${payout.american_odds > 0 ? '+' : ''}${payout.american_odds}</span>
                    </div>
                    <div class="calc-row">
                        <span>Payout per $100:</span>
                        <span class="calc-value profit">$${payout.payout_per_100.toFixed(2)}</span>
                    </div>
                    <div class="calc-row">
                        <span>Expected Value:</span>
                        <span class="calc-value ${payout.expected_value >= 0 ? 'profit' : 'loss'}">$${payout.expected_value.toFixed(2)}</span>
                    </div>
                    <div class="calc-row">
                        <span>Edge:</span>
                        <span class="calc-value ${payout.edge >= 0 ? 'profit' : 'loss'}">${payout.edge >= 0 ? '+' : ''}${payout.edge.toFixed(2)}%</span>
                    </div>
                </div>
            `;
        } else {
            document.getElementById('calculatorResults').innerHTML = 
                `<p class="calc-error">${data.error || 'Invalid parlay'}</p>`;
        }
    } catch (error) {
        document.getElementById('calculatorResults').innerHTML = 
            `<p class="calc-error">Error: ${error.message}</p>`;
    }
}

function showParlayTab(size) {
    // Hide all tabs
    document.querySelectorAll('.parlay-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.parlay-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`parlay-${size}`).classList.add('active');
    event.target.classList.add('active');
}

function renderParlayRecommendations(recommendations) {
    if (!recommendations) return;
    
    const sizes = ['2_man', '3_man', '4_man', '6_man'];
    sizes.forEach(size => {
        const container = document.getElementById(`parlay${size.charAt(0).toUpperCase() + size.slice(1).replace('_', '')}Container`);
        const recs = recommendations[size] || [];
        
        if (recs.length === 0) {
            container.innerHTML = `<p class="no-parlays">No ${size.replace('_', '-')} parlay recommendations available</p>`;
            return;
        }
        
        container.innerHTML = recs.map((parlay, idx) => {
            const payout = parlay.payout || {};
            const bets = parlay.bets || [];
            
            return `
                <div class="parlay-recommendation-card">
                    <div class="parlay-header">
                        <div class="parlay-probability">${payout.combined_probability || 0}%</div>
                        <div class="parlay-odds">${payout.american_odds > 0 ? '+' : ''}${payout.american_odds || 0}</div>
                    </div>
                    <div class="parlay-bets">
                        ${bets.map(bet => `
                            <div class="parlay-bet-item">
                                <strong>${bet.player}</strong> ${bet.recommendation} ${bet.line} (${bet.probability}%)
                            </div>
                        `).join('')}
                    </div>
                    <div class="parlay-metrics">
                        <div class="parlay-metric">
                            <span>Payout:</span>
                            <span class="metric-value">$${payout.payout_per_100?.toFixed(2) || 0}/$100</span>
                        </div>
                        <div class="parlay-metric">
                            <span>EV:</span>
                            <span class="metric-value ${payout.expected_value >= 0 ? 'positive' : 'negative'}">$${payout.expected_value?.toFixed(2) || 0}</span>
                        </div>
                        <div class="parlay-metric">
                            <span>Edge:</span>
                            <span class="metric-value ${payout.edge >= 0 ? 'positive' : 'negative'}">${payout.edge >= 0 ? '+' : ''}${payout.edge?.toFixed(2) || 0}%</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    });
}

// Show parlay section if recommendations exist
function checkParlayRecommendations(data) {
    const recommendations = data.parlay_recommendations || {};
    const hasRecommendations = Object.values(recommendations).some(recs => recs && recs.length > 0);
    
    if (hasRecommendations) {
        document.getElementById('parlaySection').style.display = 'block';
        renderParlayRecommendations(recommendations);
    }
}
