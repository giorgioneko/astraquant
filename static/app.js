const API_BASE = `${window.location.protocol}//${window.location.host}/api`;

const dom = {
    totalBalance: document.getElementById('total-balance'),
    positionsTbody: document.getElementById('positions-tbody'),
    logsList: document.getElementById('logs-list'),
    botStatusText: document.getElementById('status-text'),
    botStatusBadge: document.getElementById('bot-status'),
    toggleBotBtn: document.getElementById('toggle-bot-btn')
};

// Navigation Tab Logic
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        // Remove active class from buttons
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        
        // Hide all views
        document.querySelectorAll('.view-section').forEach(view => {
            view.style.display = 'none';
        });
        
        // Show target view
        const targetViewId = e.target.getAttribute('data-view');
        document.getElementById(targetViewId).style.display = 'grid'; // Grid to keep the dashboard-grid layout
    });
});

// Format as USD
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
};

// Fetch and update bot status
async function updateBotStatus() {
    try {
        const res = await fetch(`${API_BASE}/bot/status`);
        const data = await res.json();
        
        const isRunning = data.status === "Running";
        
        dom.botStatusText.textContent = isRunning ? "Trading Active" : "Bot Stopped";
        dom.toggleBotBtn.textContent = isRunning ? "Stop Bot" : "Start Bot";
        
        if (isRunning) {
            dom.botStatusBadge.classList.replace('stopped', 'running');
            dom.botStatusBadge.classList.remove('stopped'); // Fallback
            dom.toggleBotBtn.classList.add('active-bot');
        } else {
            dom.botStatusBadge.classList.add('stopped');
            dom.botStatusBadge.classList.remove('running');
            dom.toggleBotBtn.classList.remove('active-bot');
        }
    } catch (error) {
        console.error("Failed to fetch bot status", error);
    }
}

// Fetch and update portfolio and positions
async function updatePortfolio() {
    try {
        const res = await fetch(`${API_BASE}/portfolio`);
        const data = await res.json();
        
        dom.totalBalance.textContent = formatCurrency(data.balance);
        
        dom.positionsTbody.innerHTML = '';
        
        const positions = Object.keys(data.positions);
        if (positions.length === 0) {
            dom.positionsTbody.innerHTML = '<tr><td colspan="3">No active positions.</td></tr>';
            return;
        }

        positions.forEach(ticker => {
            const pos = data.positions[ticker];
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td><span class="asset-badge">${ticker}</span></td>
                <td>${pos.quantity}</td>
                <td>${formatCurrency(pos.avg_price)}</td>
            `;
            dom.positionsTbody.appendChild(row);
        });

    } catch (error) {
        console.error("Failed to fetch portfolio", error);
    }
}

// Fetch and update live watched assets
async function updateWatchedAssets() {
    const grid = document.getElementById('watched-assets-grid');
    if (!grid) return;
    
    try {
        const res = await fetch(`${API_BASE}/market-data`);
        const assets = await res.json();
        
        if (!assets || assets.length === 0) {
            grid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.875rem;">Add tickers in Settings to start tracking assets.</p>';
            return;
        }
        
        grid.innerHTML = '';
        assets.forEach(asset => {
            const chip = document.createElement('div');
            chip.className = 'asset-chip';
            
            const changePct = asset.change_pct;
            const changeClass = changePct > 0 ? 'positive' : changePct < 0 ? 'negative' : 'neutral';
            const changePrefix = changePct > 0 ? '▲' : changePct < 0 ? '▼' : '–';
            const changeText = changePct !== null ? `${changePrefix} ${Math.abs(changePct).toFixed(2)}%` : '–';
            const priceText = asset.price !== null ? `$${asset.price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : 'N/A';
            
            chip.innerHTML = `
                <span class="asset-chip-ticker">${asset.ticker}</span>
                <span class="asset-chip-price">${priceText}</span>
                <span class="asset-chip-change ${changeClass}">${changeText}</span>
            `;
            grid.appendChild(chip);
        });
    } catch (error) {
        console.error("Failed to fetch market data", error);
        grid.innerHTML = '<p style="color: var(--text-muted);">Market data unavailable.</p>';
    }
}

// Fetch and update trade logs
async function updateLogs() {
    try {
        const res = await fetch(`${API_BASE}/logs?limit=5`);
        const logs = await res.json();
        
        dom.logsList.innerHTML = '';
        
        if (logs.length === 0) {
            dom.logsList.innerHTML = '<li class="log-item empty-state">No trades executed yet.</li>';
            return;
        }

        logs.forEach(log => {
            const li = document.createElement('li');
            li.className = 'log-item';
            
            const isBuy = log.action === 'BUY';
            const actionClass = isBuy ? 'buy' : 'sell';
            const actionIcon = isBuy ? '↑' : '↓';
            
            const dateStr = new Date(log.timestamp).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'
            });

            li.innerHTML = `
                <div>
                    <span class="log-action ${actionClass}">${actionIcon} ${log.action}</span>
                    <strong>${log.quantity} ${log.ticker}</strong>
                </div>
                <div style="text-align: right;">
                    <div>${formatCurrency(log.price)}</div>
                    <div class="log-details">${dateStr}</div>
                </div>
            `;
            dom.logsList.appendChild(li);
        });
    } catch (error) {
        console.error("Failed to fetch logs", error);
    }
}

// Connect event listeners
dom.toggleBotBtn.addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/bot/toggle`, { method: 'POST' });
        updateBotStatus();
    } catch (error) {
        console.error("Failed to toggle bot", error);
    }
});

// --- Settings & Configuration Logic ---
const settingsDom = {
    provider: document.getElementById('llm-provider'),
    universalSettings: document.getElementById('universal-llm-settings'),
    baseUrl: document.getElementById('llm-base-url'),
    model: document.getElementById('llm-model'),
    apiKey: document.getElementById('llm-api-key'),
    saveBtn: document.getElementById('save-settings-btn'),
    newTicker: document.getElementById('new-ticker'),
    addTickerBtn: document.getElementById('add-ticker-btn'),
    watchlist: document.getElementById('watchlist-list')
};

// Toggle universal settings visibility
settingsDom.provider.addEventListener('change', (e) => {
    settingsDom.universalSettings.style.display = e.target.value === 'openai' ? 'block' : 'none';
});

async function loadSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        const data = await res.json();
        
        settingsDom.provider.value = data.llm_provider || 'finbert';
        settingsDom.baseUrl.value = data.llm_base_url || 'https://api.openai.com/v1';
        settingsDom.model.value = data.llm_model || 'gpt-4o';
        settingsDom.apiKey.value = data.llm_api_key || '';
        
        settingsDom.universalSettings.style.display = settingsDom.provider.value === 'openai' ? 'block' : 'none';
        
    } catch (error) {
        console.error("Failed to load settings", error);
    }
}

async function loadWatchlist() {
    try {
        const res = await fetch(`${API_BASE}/watchlist`);
        const data = await res.json();
        
        settingsDom.watchlist.innerHTML = '';
        data.tickers.forEach(ticker => {
            const li = document.createElement('li');
            li.className = 'watchlist-item';
            li.innerHTML = `
                ${ticker}
                <button class="btn-remove" onclick="removeTicker('${ticker}')">×</button>
            `;
            settingsDom.watchlist.appendChild(li);
        });
    } catch (error) {
        console.error("Failed to load watchlist", error);
    }
}

settingsDom.addTickerBtn.addEventListener('click', async () => {
    const ticker = settingsDom.newTicker.value.trim().toUpperCase();
    if (!ticker) return;
    
    try {
        await fetch(`${API_BASE}/watchlist`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker })
        });
        settingsDom.newTicker.value = '';
        await loadWatchlist();
    } catch (e) {
        console.error("Failed to add ticker", e);
    }
});

window.removeTicker = async (ticker) => {
    try {
        await fetch(`${API_BASE}/watchlist/${ticker}`, { method: 'DELETE' });
        await loadWatchlist();
    } catch (e) {
        console.error("Failed to remove ticker", e);
    }
};

settingsDom.saveBtn.addEventListener('click', async () => {
    const originalText = settingsDom.saveBtn.textContent;
    settingsDom.saveBtn.textContent = 'Saving...';
    
    try {
        await fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                llm_provider: settingsDom.provider.value,
                llm_base_url: settingsDom.baseUrl.value,
                llm_model: settingsDom.model.value,
                llm_api_key: settingsDom.apiKey.value
            })
        });
        
        settingsDom.saveBtn.textContent = 'Saved!';
        setTimeout(() => settingsDom.saveBtn.textContent = originalText, 2000);
    } catch (e) {
        console.error("Failed to save settings", e);
        settingsDom.saveBtn.textContent = 'Error!';
        setTimeout(() => settingsDom.saveBtn.textContent = originalText, 2000);
    }
});

// Initialization and auto-refresh
async function init() {
    await updateBotStatus();
    await updatePortfolio();
    await updateLogs();
    await updateWatchedAssets();
    await loadSettings();
    await loadWatchlist();
    
    // Poll dashboard data every 5 seconds
    setInterval(() => {
        updatePortfolio();
        updateLogs();
        updateBotStatus();
    }, 5000);
    
    // Poll market prices every 30 seconds (to avoid hammering yfinance)
    setInterval(() => {
        updateWatchedAssets();
    }, 30000);
}

document.addEventListener('DOMContentLoaded', init);
