/**
 * Main JavaScript Application
 * Handles API calls, UI updates, and user interactions
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let isLoggingOut = false;

// ============== Authentication ==============

async function login(email, password) {
    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Invalid credentials');
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);

        // Hide login modal FIRST
        hideLoginModal();

        // Then load user data
        try {
            await loadUserProfile();
        } catch (e) {
            console.log('Profile load error (non-critical):', e);
        }

        // Load dashboard (don't block on errors)
        loadDashboard().catch(e => console.log('Dashboard load error:', e));

        showNotification('Login successful!', 'success');
    } catch (error) {
        showNotification('Login failed: ' + error.message, 'error');
    }
}

async function register(email, username, password, fullName) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                username,
                password,
                full_name: fullName
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Registration failed');
        }

        showNotification('Registration successful! Please login.', 'success');
        switchAuthTab('login');
    } catch (error) {
        showNotification('Registration failed: ' + error.message, 'error');
    }
}

async function loadUserProfile() {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('userName').textContent = currentUser.username || 'User';
        }
    } catch (error) {
        console.error('Failed to load user profile:', error);
    }
}

function logout() {
    if (isLoggingOut) return;
    isLoggingOut = true;

    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;

    // Show login modal
    document.getElementById('loginModal').classList.add('active');
    document.getElementById('userName').textContent = 'User';

    // Reset form fields
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    if (loginEmail) loginEmail.value = '';
    if (loginPassword) loginPassword.value = '';

    showNotification('Logged out successfully', 'info');

    setTimeout(() => { isLoggingOut = false; }, 500);
}

// ============== API Helper ==============

async function apiCall(endpoint, options = {}) {
    if (!authToken) {
        throw new Error('Not authenticated');
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        ...options.headers
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Only logout if we're not already in a logout flow
        if (!isLoggingOut) {
            console.log('Session expired, please login again');
            // Don't auto-logout, just throw error
        }
        throw new Error('Session expired');
    }

    if (!response.ok) {
        let errorMsg = 'API request failed';
        try {
            const error = await response.json();
            errorMsg = error.detail || errorMsg;
        } catch (e) { }
        throw new Error(errorMsg);
    }

    return await response.json();
}

// ============== Dashboard ==============

async function loadDashboard() {
    if (!authToken) return;

    try {
        // Load portfolio summary
        const portfolio = await apiCall('/trading/portfolio');
        updatePortfolioStats(portfolio);
    } catch (error) {
        console.log('Portfolio load error:', error.message);
        // Set default values if portfolio fails
        setDefaultPortfolioStats();
    }

    // Load market data (non-blocking)
    loadMarketMovers().catch(e => console.log('Market movers error:', e));
    loadAIInsights().catch(e => console.log('AI insights error:', e));
}

function setDefaultPortfolioStats() {
    document.getElementById('portfolioValue').textContent = '₹10,00,000.00';
    document.getElementById('cashBalance').textContent = '₹10,00,000.00';
    document.getElementById('activePositions').textContent = '0';
    document.getElementById('totalPnL').textContent = '₹0.00';
    document.getElementById('pnlPercent').textContent = '0.00%';
}

function updatePortfolioStats(portfolio) {
    if (!portfolio) {
        setDefaultPortfolioStats();
        return;
    }

    document.getElementById('portfolioValue').textContent = formatCurrency(portfolio.total_portfolio_value || 1000000);
    document.getElementById('cashBalance').textContent = formatCurrency(portfolio.cash_balance || 1000000);
    document.getElementById('activePositions').textContent = portfolio.num_positions || 0;

    const pnl = portfolio.pnl || { total_pnl: 0, pnl_percent: 0 };
    document.getElementById('totalPnL').textContent = formatCurrency(pnl.total_pnl || 0);

    const pnlPercent = document.getElementById('pnlPercent');
    pnlPercent.textContent = `${(pnl.pnl_percent || 0).toFixed(2)}%`;
    pnlPercent.className = 'stat-change ' + ((pnl.pnl_percent || 0) >= 0 ? 'positive' : 'negative');
}

async function loadMarketMovers() {
    try {
        const gainers = await apiCall('/stocks/market/movers?mover_type=gainers&limit=5');
        const losers = await apiCall('/stocks/market/movers?mover_type=losers&limit=5');

        displayMovers('topGainers', gainers.stocks || []);
        displayMovers('topLosers', losers.stocks || []);
    } catch (error) {
        console.log('Market movers error:', error.message);
        document.getElementById('topGainers').innerHTML = '<p class="text-muted">No data available</p>';
        document.getElementById('topLosers').innerHTML = '<p class="text-muted">No data available</p>';
    }
}

function displayMovers(containerId, stocks) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!stocks || stocks.length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }

    container.innerHTML = stocks.map(stock => `
        <div class="mover-item" onclick="viewStockDetails(${stock.id})">
            <div class="mover-info">
                <strong>${(stock.symbol || '').replace('.NS', '')}</strong>
                <span class="text-muted">${stock.name || ''}</span>
            </div>
            <div class="mover-price">
                <strong>${formatCurrency(stock.current_price || 0)}</strong>
                <span class="stat-change ${(stock.latest_data?.change_percent || 0) >= 0 ? 'positive' : 'negative'}">
                    ${(stock.latest_data?.change_percent || 0).toFixed(2)}%
                </span>
            </div>
        </div>
    `).join('');
}

async function loadAIInsights() {
    const container = document.getElementById('aiInsights');
    if (!container) return;

    container.innerHTML = '<div class="loader"></div>';

    try {
        const insights = await apiCall('/ai/market-overview');

        if (insights && insights.status === 'success') {
            container.innerHTML = `<div class="ai-content">${formatAIResponse(insights.overview || '')}</div>`;
        } else {
            container.innerHTML = '<p class="text-muted">AI assistant is currently unavailable.</p>';
        }
    } catch (error) {
        container.innerHTML = '<p class="text-muted">Unable to load AI insights.</p>';
    }
}

function formatAIResponse(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

// ============== Markets Page ==============

async function loadStocks(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        const data = await apiCall(`/stocks/?${params}`);

        displayStocksTable(data.stocks || []);
    } catch (error) {
        console.log('Failed to load stocks:', error.message);
        document.getElementById('stocksTableBody').innerHTML =
            '<tr><td colspan="8" class="text-center text-muted">Unable to load stocks</td></tr>';
    }
}

function displayStocksTable(stocks) {
    const tbody = document.getElementById('stocksTableBody');
    if (!tbody) return;

    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No stocks found</td></tr>';
        return;
    }

    tbody.innerHTML = stocks.map(stock => `
        <tr>
            <td><strong>${(stock.symbol || '').replace('.NS', '')}</strong></td>
            <td>${stock.name || ''}</td>
            <td>${formatCurrency(stock.current_price || 0)}</td>
            <td class="${(stock.change_value || 0) >= 0 ? 'text-success' : 'text-danger'}">
                ${formatCurrency(stock.change_value || 0)}
            </td>
            <td>
                <span class="stat-change ${(stock.change_percent || 0) >= 0 ? 'positive' : 'negative'}">
                    ${(stock.change_percent || 0).toFixed(2)}%
                </span>
            </td>
            <td>${formatMarketCap(stock.market_cap)}</td>
            <td>${stock.sector || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openTradeModal(${stock.id}, '${stock.symbol}', ${stock.current_price || 0})">
                    Trade
                </button>
            </td>
        </tr>
    `).join('');
}

// ============== Portfolio Page ==============

async function loadPortfolio() {
    try {
        const portfolio = await apiCall('/trading/portfolio');

        // Update summary
        document.getElementById('portfolioTotalValue').textContent = formatCurrency(portfolio.total_portfolio_value || 0);
        document.getElementById('portfolioInvested').textContent = formatCurrency(portfolio.invested_value || 0);
        document.getElementById('portfolioCurrent').textContent = formatCurrency(portfolio.current_value || 0);
        document.getElementById('portfolioUnrealizedPnL').textContent = formatCurrency(portfolio.pnl?.total_pnl || 0);

        displayHoldings(portfolio.holdings || []);
        await loadTransactions();
    } catch (error) {
        console.log('Failed to load portfolio:', error.message);
    }
}

function displayHoldings(holdings) {
    const tbody = document.getElementById('holdingsTableBody');
    if (!tbody) return;

    if (!holdings || holdings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No holdings yet</td></tr>';
        return;
    }

    tbody.innerHTML = holdings.map(holding => `
        <tr>
            <td><strong>${(holding.stock?.symbol || '').replace('.NS', '')}</strong></td>
            <td>${holding.quantity || 0}</td>
            <td>${formatCurrency(holding.average_buy_price || 0)}</td>
            <td>${formatCurrency(holding.current_price || 0)}</td>
            <td>${formatCurrency(holding.invested_value || 0)}</td>
            <td>${formatCurrency(holding.current_value || 0)}</td>
            <td class="${(holding.unrealized_pnl || 0) >= 0 ? 'text-success' : 'text-danger'}">
                ${formatCurrency(holding.unrealized_pnl || 0)}
            </td>
            <td>
                <span class="stat-change ${(holding.unrealized_pnl_percent || 0) >= 0 ? 'positive' : 'negative'}">
                    ${(holding.unrealized_pnl_percent || 0).toFixed(2)}%
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="openSellModal(${holding.stock_id}, '${holding.stock?.symbol}', ${holding.current_price}, ${holding.quantity})">
                    Sell
                </button>
            </td>
        </tr>
    `).join('');
}

async function loadTransactions() {
    try {
        const data = await apiCall('/trading/transactions?limit=50');
        displayTransactions(data.transactions || []);
    } catch (error) {
        console.log('Failed to load transactions:', error.message);
    }
}

function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsTableBody');
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No transactions yet</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(txn => `
        <tr>
            <td>${new Date(txn.created_at).toLocaleString()}</td>
            <td>
                <span class="badge ${txn.transaction_type === 'BUY' ? 'badge-success' : 'badge-danger'}">
                    ${txn.transaction_type || ''}
                </span>
            </td>
            <td><strong>${(txn.stock?.symbol || '').replace('.NS', '')}</strong></td>
            <td>${txn.quantity || 0}</td>
            <td>${formatCurrency(txn.price || 0)}</td>
            <td>${formatCurrency(txn.total_value || 0)}</td>
            <td>${formatCurrency(txn.transaction_fee || 0)}</td>
            <td class="${(txn.realized_pnl || 0) >= 0 ? 'text-success' : 'text-danger'}">
                ${txn.realized_pnl ? formatCurrency(txn.realized_pnl) : '-'}
            </td>
        </tr>
    `).join('');
}

// ============== Trading ==============

function openTradeModal(stockId, symbol, price) {
    document.getElementById('tradeStockSearch').value = symbol || '';
    document.getElementById('tradeStockId').value = stockId || '';
    document.getElementById('tradePrice').value = price || '';
    document.getElementById('tradeQuantity').value = '';
    document.getElementById('tradeModal').classList.add('active');
    updateTradeSummary();
}

function openSellModal(stockId, symbol, price, maxQty) {
    openTradeModal(stockId, symbol, price);
    document.querySelector('[data-action="sell"]')?.click();
}

function updateTradeSummary() {
    const qty = parseFloat(document.getElementById('tradeQuantity')?.value) || 0;
    const price = parseFloat(document.getElementById('tradePrice')?.value) || 0;
    const total = qty * price;
    const fee = total * 0.0005;
    const net = total + fee;

    document.getElementById('tradeTotalValue').textContent = formatCurrency(total);
    document.getElementById('tradeFee').textContent = formatCurrency(fee);
    document.getElementById('tradeNetAmount').textContent = formatCurrency(net);
}

async function executeTrade(action, stockId, quantity, price) {
    try {
        const endpoint = action === 'buy' ? '/trading/buy' : '/trading/sell';

        await apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify({
                stock_id: parseInt(stockId),
                quantity: parseInt(quantity),
                price: parseFloat(price)
            })
        });

        showNotification(`${action.toUpperCase()} order executed successfully!`, 'success');
        closeTradeModal();

        // Refresh data
        await loadDashboard();
        if (document.getElementById('page-portfolio')?.classList.contains('active')) {
            await loadPortfolio();
        }
    } catch (error) {
        showNotification(`Trade failed: ${error.message}`, 'error');
    }
}

// ============== AI Assistant ==============

async function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    addChatMessage(message, 'user');
    input.value = '';

    const loadingId = addChatMessage('Thinking...', 'ai', true);

    try {
        const response = await apiCall('/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ message })
        });

        document.getElementById(loadingId)?.remove();
        addChatMessage(response.response || 'No response received', 'ai');
    } catch (error) {
        document.getElementById(loadingId)?.remove();
        addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
    }
}

function addChatMessage(content, sender, isLoading = false) {
    const container = document.getElementById('chatContainer');
    if (!container) return null;

    const messageId = `msg-${Date.now()}`;

    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${sender}-message`;

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
        </div>
        <div class="message-content">
            ${isLoading ? '<div class="loader"></div>' : `<p>${formatAIResponse(content)}</p>`}
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;

    return messageId;
}

// ============== UI Utilities ==============

function formatCurrency(value) {
    const num = parseFloat(value) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatMarketCap(value) {
    if (!value) return 'N/A';

    const crores = value / 10000000;
    if (crores >= 1000) {
        return `₹${(crores / 1000).toFixed(2)}T`;
    }
    return `₹${crores.toFixed(2)}Cr`;
}

function showNotification(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';

    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4500);
}

function navigateToPage(pageName) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) targetPage.classList.add('active');

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');

    switch (pageName) {
        case 'markets':
            loadStocks();
            break;
        case 'portfolio':
            loadPortfolio();
            break;
        case 'dashboard':
            loadDashboard();
            break;
    }
}

function hideLoginModal() {
    document.getElementById('loginModal')?.classList.remove('active');
}

function showLoginModal() {
    document.getElementById('loginModal')?.classList.add('active');
}

function closeTradeModal() {
    document.getElementById('tradeModal')?.classList.remove('active');
}

function showTradeModal() {
    document.getElementById('tradeModal')?.classList.add('active');
}

function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) loginForm.style.display = tab === 'login' ? 'block' : 'none';
    if (registerForm) registerForm.style.display = tab === 'register' ? 'block' : 'none';
}

// ============== Initialization ==============

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    if (authToken) {
        // User has token, hide login modal and load dashboard
        hideLoginModal();
        loadUserProfile().catch(e => console.log('Profile error:', e));
        loadDashboard().catch(e => console.log('Dashboard error:', e));
    } else {
        // No token, show login modal
        showLoginModal();
    }

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            if (link.dataset.page) navigateToPage(link.dataset.page);
        });
    });

    // Auth forms
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail')?.value;
            const password = document.getElementById('loginPassword')?.value;
            if (email && password) login(email, password);
        });
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('registerEmail')?.value;
            const username = document.getElementById('registerUsername')?.value;
            const password = document.getElementById('registerPassword')?.value;
            const fullName = document.getElementById('registerFullName')?.value;
            if (email && username && password) register(email, username, password, fullName);
        });
    }

    // Trade form
    const tradeForm = document.getElementById('tradeForm');
    if (tradeForm) {
        tradeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const stockId = document.getElementById('tradeStockId')?.value;
            const qty = document.getElementById('tradeQuantity')?.value;
            const price = document.getElementById('tradePrice')?.value;
            const action = document.querySelector('[data-action].btn.active')?.dataset.action || 'buy';
            if (stockId && qty && price) executeTrade(action, stockId, qty, price);
        });

        // Update summary on input
        document.getElementById('tradeQuantity')?.addEventListener('input', updateTradeSummary);
        document.getElementById('tradePrice')?.addEventListener('input', updateTradeSummary);
    }

    // Trade action buttons
    document.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-action]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Auth tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.dataset.tab) switchAuthTab(tab.dataset.tab);
        });
    });

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });

    // Chat input
    document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Refresh button
    document.getElementById('refreshDataBtn')?.addEventListener('click', () => {
        loadDashboard();
        showNotification('Data refreshed', 'info');
    });

    // User dropdown
    document.getElementById('userMenuBtn')?.addEventListener('click', () => {
        document.getElementById('userDropdown')?.classList.toggle('active');
    });
});

// Placeholder functions for stock details
function viewStockDetails(stockId) {
    console.log('View stock details:', stockId);
    showNotification('Stock details feature coming soon', 'info');
}

function applyFilters() {
    const sector = document.getElementById('sectorFilter')?.value;
    const change = document.getElementById('changeFilter')?.value;
    loadStocks({ sector, min_change: change });
}

function viewAllMovers(type) {
    navigateToPage('markets');
    // Could apply filter here
}

function refreshAIInsights() {
    loadAIInsights();
}
