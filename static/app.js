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

// Track chart instances to destroy before re-rendering
const _trendingCharts = {};

// Fetch and render trending markets with sparkline charts
async function updateTrending() {
    const container = document.getElementById('trending-scroll');
    if (!container) return;
    
    try {
        const res = await fetch(`${API_BASE}/trending`);
        const assets = await res.json();
        
        if (!assets || assets.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted);">No trending data available.</p>';
            return;
        }
        
        // Destroy existing charts to prevent memory leaks
        Object.values(_trendingCharts).forEach(chart => chart.destroy());
        Object.keys(_trendingCharts).forEach(k => delete _trendingCharts[k]);
        
        container.innerHTML = '';
        
        assets.forEach(asset => {
            if (!asset.prices || asset.prices.length === 0) return;
            
            const changePct = asset.change_pct;
            const changeClass = changePct > 0 ? 'positive' : changePct < 0 ? 'negative' : 'neutral';
            const changeText = changePct !== null
                ? `${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%`
                : '–';
            const priceText = asset.price !== null
                ? `$${asset.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : 'N/A';

            const chartColor = changePct >= 0 ? '#2ea043' : '#f85149';
            const chartFill = changePct >= 0 ? 'rgba(46,160,67,0.15)' : 'rgba(248,81,73,0.12)';
            const canvasId = `chart-${asset.ticker.replace('-', '_')}`;

            const item = document.createElement('div');
            item.className = 'trending-item';
            item.innerHTML = `
                <div class="trending-item-header">
                    <span class="trending-ticker">${asset.ticker}</span>
                    <span class="trending-change ${changeClass}">${changeText}</span>
                </div>
                <span class="trending-price">${priceText}</span>
                <div class="trending-chart-wrap">
                    <canvas id="${canvasId}"></canvas>
                </div>
            `;
            container.appendChild(item);

            // Draw sparkline chart
            const ctx = document.getElementById(canvasId)?.getContext('2d');
            if (ctx) {
                _trendingCharts[asset.ticker] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: asset.timestamps,
                        datasets: [{
                            data: asset.prices,
                            borderColor: chartColor,
                            backgroundColor: chartFill,
                            borderWidth: 1.5,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false }, tooltip: { enabled: false } },
                        scales: {
                            x: { display: false },
                            y: { display: false }
                        },
                        animation: false,
                    }
                });
            }
        });
    } catch (error) {
        console.error("Failed to fetch trending data", error);
        container.innerHTML = '<p style="color: var(--text-muted);">Market data unavailable.</p>';
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
    brokerType: document.getElementById('broker-type'),
    brokerApiSettings: document.getElementById('broker-api-settings'),
    brokerBaseUrl: document.getElementById('broker-base-url'),
    brokerApiKey: document.getElementById('broker-api-key'),
    brokerSecretKey: document.getElementById('broker-secret-key'),
    newTicker: document.getElementById('new-ticker'),
    addTickerBtn: document.getElementById('add-ticker-btn'),
    watchlist: document.getElementById('watchlist-list')
};

const mcpDom = {
    list: document.getElementById('mcp-server-list'),
    name: document.getElementById('mcp-name'),
    cmd: document.getElementById('mcp-cmd'),
    args: document.getElementById('mcp-args'),
    env: document.getElementById('mcp-env'),
    addBtn: document.getElementById('add-mcp-btn')
};

settingsDom.provider.addEventListener('change', (e) => {
    settingsDom.universalSettings.style.display = e.target.value === 'openai' ? 'block' : 'none';
});

// Toggle broker settings visibility
settingsDom.brokerType.addEventListener('change', (e) => {
    settingsDom.brokerApiSettings.style.display = e.target.value !== 'mock' ? 'block' : 'none';
});

async function loadSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        const data = await res.json();
        
        settingsDom.provider.value = data.llm_provider || 'finbert';
        settingsDom.baseUrl.value = data.llm_base_url || 'https://api.openai.com/v1';
        settingsDom.model.value = data.llm_model || 'gpt-4o';
        settingsDom.apiKey.value = data.llm_api_key || '';
        
        // Map legacy broker types to the new generic 'external' type
        let loadedBrokerType = data.broker_type || 'mock';
        if (loadedBrokerType === 'alpaca' || loadedBrokerType === 'binance') {
            loadedBrokerType = 'external';
        }
        settingsDom.brokerType.value = loadedBrokerType;
        
        settingsDom.brokerBaseUrl.value = data.broker_base_url || 'https://paper-api.alpaca.markets';
        settingsDom.brokerApiKey.value = data.broker_api_key || '';
        settingsDom.brokerSecretKey.value = data.broker_secret_key || '';
        
        settingsDom.universalSettings.style.display = settingsDom.provider.value === 'openai' ? 'block' : 'none';
        settingsDom.brokerApiSettings.style.display = settingsDom.brokerType.value !== 'mock' ? 'block' : 'none';
        
        syncCustomSelects();
        
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

async function loadMCPServers() {
    try {
        const res = await fetch(`${API_BASE}/mcp-servers`);
        const servers = await res.json();
        
        mcpDom.list.innerHTML = '';
        if (servers.length === 0) {
            mcpDom.list.innerHTML = '<div style="color:var(--text-muted); font-size:0.875rem;">No MCP servers configured yet.</div>';
            return;
        }
        
        servers.forEach(s => {
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';
            div.style.padding = '0.75rem';
            div.style.background = 'rgba(255,255,255,0.05)';
            div.style.borderRadius = '8px';
            div.style.marginBottom = '0.5rem';
            
            div.innerHTML = `
                <div>
                    <strong style="color: var(--primary);">${s.name}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${s.command} ${s.args}</div>
                </div>
                <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; background: var(--danger)" onclick="deleteMCPServer(${s.id})">Del</button>
            `;
            mcpDom.list.appendChild(div);
        });
    } catch (e) {
        console.error("Failed to load MCP servers", e);
    }
}

window.deleteMCPServer = async (id) => {
    try {
        await fetch(`${API_BASE}/mcp-servers/${id}`, { method: 'DELETE' });
        await loadMCPServers();
    } catch (e) {
        console.error("Failed to delete MCP server", e);
    }
};

mcpDom.addBtn.addEventListener('click', async () => {
    const name = mcpDom.name.value;
    const cmd = mcpDom.cmd.value;
    const args = mcpDom.args.value;
    const env = mcpDom.env.value;
    
    if(!name || !cmd) return alert("Name and Execution Command are required");
    if(env) {
        try { JSON.parse(env); } catch(e) { return alert("Environment variables must be valid JSON"); }
    }
    
    mcpDom.addBtn.textContent = "Adding...";
    try {
        await fetch(`${API_BASE}/mcp-servers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, command: cmd, args, env_vars: env })
        });
        mcpDom.name.value = '';
        mcpDom.cmd.value = '';
        mcpDom.args.value = '';
        mcpDom.env.value = '';
        await loadMCPServers();
    } catch (e) {
        console.error("Failed to add MCP server", e);
    }
    mcpDom.addBtn.textContent = "Add Connection";
});

let settingsTimeout;
async function autoSaveSettings() {
    try {
        await fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                llm_provider: settingsDom.provider.value,
                llm_base_url: settingsDom.baseUrl.value,
                llm_model: settingsDom.model.value,
                llm_api_key: settingsDom.apiKey.value,
                broker_type: settingsDom.brokerType.value,
                broker_base_url: settingsDom.brokerBaseUrl.value,
                broker_api_key: settingsDom.brokerApiKey.value,
                broker_secret_key: settingsDom.brokerSecretKey.value
            })
        });
        console.log("Settings auto-saved!");
    } catch (e) {
        console.error("Failed to auto-save settings", e);
    }
}

// Attach auto-save to inputs in the settings tab
document.querySelectorAll('#settings-view .input-field').forEach(input => {
    // Only auto-save on input for those that aren't the add ticker field
    if (input.id !== 'new-ticker') {
        input.addEventListener('input', () => {
            clearTimeout(settingsTimeout);
            settingsTimeout = setTimeout(autoSaveSettings, 800);
        });
        input.addEventListener('change', autoSaveSettings);
    }
});

function setupCustomSelects() {
    document.querySelectorAll('select.input-field').forEach(select => {
        if(select.nextElementSibling && select.nextElementSibling.classList.contains('custom-select-wrapper')) return;
        
        select.style.display = 'none';
        
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-select-wrapper';
        
        const display = document.createElement('div');
        display.className = 'custom-select-display';
        const selectedOption = select.options[select.selectedIndex];
        display.innerHTML = `<span>${selectedOption ? selectedOption.text : ''}</span> <span style="font-size:0.7em; opacity:0.7">▼</span>`;
        
        const optionsList = document.createElement('div');
        optionsList.className = 'custom-select-options';
        
        Array.from(select.options).forEach((option, index) => {
            const optDiv = document.createElement('div');
            optDiv.className = 'custom-option' + (option.selected ? ' selected' : '');
            optDiv.textContent = option.text;
            
            optDiv.addEventListener('click', (e) => {
                e.stopPropagation();
                if(select.selectedIndex !== index) {
                    select.selectedIndex = index;
                    display.innerHTML = `<span>${option.text}</span> <span style="font-size:0.7em; opacity:0.7">▼</span>`;
                    
                    optionsList.querySelectorAll('.custom-option').forEach(o => o.classList.remove('selected'));
                    optDiv.classList.add('selected');
                    select.dispatchEvent(new Event('change'));
                }
                wrapper.classList.remove('open');
                display.classList.remove('open');
            });
            optionsList.appendChild(optDiv);
        });
        
        wrapper.appendChild(display);
        wrapper.appendChild(optionsList);
        select.parentNode.insertBefore(wrapper, select.nextSibling);
        
        display.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.custom-select-wrapper').forEach(w => {
                if(w !== wrapper) {
                    w.classList.remove('open');
                    w.querySelector('.custom-select-display').classList.remove('open');
                }
            });
            wrapper.classList.toggle('open');
            display.classList.toggle('open');
        });
    });
    
    document.addEventListener('click', () => {
        document.querySelectorAll('.custom-select-wrapper').forEach(w => {
            w.classList.remove('open');
            w.querySelector('.custom-select-display').classList.remove('open');
        });
    });
}

function syncCustomSelects() {
    document.querySelectorAll('select.input-field').forEach(select => {
        const wrapper = select.nextElementSibling;
        if(wrapper && wrapper.classList.contains('custom-select-wrapper')) {
            const display = wrapper.querySelector('.custom-select-display span');
            const options = wrapper.querySelectorAll('.custom-option');
            const selectedOption = select.options[select.selectedIndex];
            if(selectedOption) {
                display.textContent = selectedOption.text;
                options.forEach((opt, index) => {
                    if(index === select.selectedIndex) opt.classList.add('selected');
                    else opt.classList.remove('selected');
                });
            }
        }
    });
}

// Initialization and auto-refresh
async function init() {
    setupCustomSelects();
    await updateBotStatus();
    await updatePortfolio();
    await updateLogs();
    await updateWatchedAssets();
    await loadSettings();
    await loadWatchlist();
    await loadMCPServers();
    updateTrending(); // fire async, don't await — it takes a few seconds due to yfinance calls
    
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

    // Trending charts refresh every 60 seconds
    setInterval(() => {
        updateTrending();
    }, 60000);
}

document.addEventListener('DOMContentLoaded', init);
