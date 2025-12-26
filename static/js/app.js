/**
 * Main JavaScript Application
 * Handles API calls, UI updates, and user interactions
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

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

        if (!response.ok) throw new Error('Login failed');

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);

        await loadUserProfile();
        hideLoginModal();
        loadDashboard();

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

        if (!response.ok) throw new Error('Registration failed');

        showNotification('Registration successful! Please login.', 'success');
        switchAuthTab('login');
    } catch (error) {
        showNotification('Registration failed: ' + error.message, 'error');
    }
}

async function loadUserProfile() {
    try {
        const response = await apiCall('/auth/me');
        currentUser = response;
        document.getElementById('userName').textContent = currentUser.username;
    } catch (error) {
        console.error('Failed to load user profile:', error);
    }
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;

    // UI Update instead of reload
    document.getElementById('userName').textContent = "User";
    document.getElementById('loginModal').classList.add('active');

    // Clear sensitive data from UI
    document.getElementById('portfolioValue').textContent = "₹0";
    document.getElementById('totalPnL').textContent = "₹0";
}

// ============== API Helper ==============

async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        logout();
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
    }

    return await response.json();
}

// ============== Dashboard ==============

async function loadDashboard() {
    try {
        // Load portfolio summary
        const portfolio = await apiCall('/trading/portfolio');
        updatePortfolioStats(portfolio);

        // Load market movers
        await loadMarketMovers();

        // Load AI insights
        await loadAIInsights();
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function updatePortfolioStats(portfolio) {
    document.getElementById('portfolioValue').textContent = formatCurrency(portfolio.total_portfolio_value);
    document.getElementById('cashBalance').textContent = formatCurrency(portfolio.cash_balance);
    document.getElementById('activePositions').textContent = portfolio.num_positions;

    const pnl = portfolio.pnl;
    document.getElementById('totalPnL').textContent = formatCurrency(pnl.total_pnl);

    const pnlPercent = document.getElementById('pnlPercent');
    pnlPercent.textContent = `${pnl.pnl_percent.toFixed(2)}%`;
    pnlPercent.className = 'stat-change ' + (pnl.pnl_percent >= 0 ? 'positive' : 'negative');
}

async function loadMarketMovers() {
    try {
        const gainers = await apiCall('/stocks/market/movers?mover_type=gainers&limit=5');
        const losers = await apiCall('/stocks/market/movers?mover_type=losers&limit=5');

        displayMovers('topGainers', gainers.stocks);
        displayMovers('topLosers', losers.stocks);
    } catch (error) {
        console.error('Failed to load market movers:', error);
    }
}

function displayMovers(containerId, stocks) {
    const container = document.getElementById(containerId);

    if (!stocks || stocks.length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }

    container.innerHTML = stocks.map(stock => `
        <div class="mover-item" onclick="viewStockDetails(${stock.id})">
            <div class="mover-info">
                <strong>${stock.symbol.replace('.NS', '')}</strong>
                <span class="text-muted">${stock.name}</span>
            </div>
            <div class="mover-price">
                <strong>${formatCurrency(stock.current_price)}</strong>
                <span class="stat-change ${stock.latest_data.change_percent >= 0 ? 'positive' : 'negative'}">
                    ${stock.latest_data.change_percent.toFixed(2)}%
                </span>
            </div>
        </div>
    `).join('');
}

async function loadAIInsights() {
    try {
        const container = document.getElementById('aiInsights');
        container.innerHTML = '<div class="loader"></div>';

        const insights = await apiCall('/ai/market-overview');

        if (insights.status === 'success') {
            container.innerHTML = `<div class="ai-content">${formatAIResponse(insights.overview)}</div>`;
        } else {
            container.innerHTML = '<p class="text-muted">AI assistant is currently unavailable.</p>';
        }
    } catch (error) {
        document.getElementById('aiInsights').innerHTML =
            '<p class="text-muted">Unable to load AI insights.</p>';
    }
}

function formatAIResponse(text) {
    // Convert markdown-style formatting to HTML
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

        displayStocksTable(data.stocks);
    } catch (error) {
        console.error('Failed to load stocks:', error);
    }
}

function displayStocksTable(stocks) {
    const tbody = document.getElementById('stocksTableBody');

    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No stocks found</td></tr>';
        return;
    }

    tbody.innerHTML = stocks.map(stock => `
        <tr>
            <td><strong>${stock.symbol.replace('.NS', '')}</strong></td>
            <td>${stock.name}</td>
            <td>${formatCurrency(stock.current_price || 0)}</td>
            <td class="${stock.change_value >= 0 ? 'text-success' : 'text-danger'}">
                ${formatCurrency(stock.change_value || 0)}
            </td>
            <td>
                <span class="stat-change ${stock.change_percent >= 0 ? 'positive' : 'negative'}">
                    ${(stock.change_percent || 0).toFixed(2)}%
                </span>
            </td>
            <td>${formatMarketCap(stock.market_cap)}</td>
            <td>${stock.sector || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openTradeModal(${stock.id}, '${stock.symbol}', ${stock.current_price})">
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
        document.getElementById('portfolioTotalValue').textContent = formatCurrency(portfolio.total_portfolio_value);
        document.getElementById('portfolioInvested').textContent = formatCurrency(portfolio.invested_value);
        document.getElementById('portfolioCurrent').textContent = formatCurrency(portfolio.current_value);
        document.getElementById('portfolioUnrealizedPnL').textContent = formatCurrency(portfolio.pnl.total_pnl);

        // Display holdings
        displayHoldings(portfolio.holdings);

        // Load transactions
        await loadTransactions();
    } catch (error) {
        console.error('Failed to load portfolio:', error);
    }
}

function displayHoldings(holdings) {
    const tbody = document.getElementById('holdingsTableBody');

    if (!holdings || holdings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No holdings yet</td></tr>';
        return;
    }

    tbody.innerHTML = holdings.map(holding => `
        <tr>
            <td><strong>${holding.stock.symbol.replace('.NS', '')}</strong></td>
            <td>${holding.quantity}</td>
            <td>${formatCurrency(holding.average_buy_price)}</td>
            <td>${formatCurrency(holding.current_price)}</td>
            <td>${formatCurrency(holding.invested_value)}</td>
            <td>${formatCurrency(holding.current_value)}</td>
            <td class="${holding.unrealized_pnl >= 0 ? ' text-success' : 'text-danger'}">
                ${formatCurrency(holding.unrealized_pnl)}
            </td>
            <td>
                <span class="stat-change ${holding.unrealized_pnl_percent >= 0 ? 'positive' : 'negative'}">
                    ${holding.unrealized_pnl_percent.toFixed(2)}%
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="openSellModal(${holding.stock_id}, '${holding.stock.symbol}', ${holding.current_price}, ${holding.quantity})">
                    Sell
                </button>
            </td>
        </tr>
    `).join('');
}

async function loadTransactions() {
    try {
        const data = await apiCall('/trading/transactions?limit=50');
        displayTransactions(data.transactions);
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsTableBody');

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No transactions yet</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(txn => `
        <tr>
            <td>${new Date(txn.created_at).toLocaleString()}</td>
            <td>
                <span class="badge ${txn.transaction_type === 'BUY' ? 'badge-success' : 'badge-danger'}">
                    ${txn.transaction_type}
                </span>
            </td>
            <td><strong>${txn.stock.symbol.replace('.NS', '')}</strong></td>
            <td>${txn.quantity}</td>
            <td>${formatCurrency(txn.price)}</td>
            <td>${formatCurrency(txn.total_value)}</td>
            <td>${formatCurrency(txn.transaction_fee)}</td>
            <td class="${txn.realized_pnl >= 0 ? 'text-success' : 'text-danger'}">
                ${txn.realized_pnl ? formatCurrency(txn.realized_pnl) : '-'}
            </td>
        </tr>
    `).join('');
}

// ============== Trading ==============

async function executeTrade(action, stockId, quantity, price) {
    try {
        const endpoint = action === 'buy' ? '/trading/buy' : '/trading/sell';

        const result = await apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify({
                stock_id: stockId,
                quantity: parseInt(quantity),
                price: parseFloat(price)
            })
        });

        showNotification(`${action} order executed successfully!`, 'success');
        closeTradeModal();

        // Refresh data
        await loadDashboard();
        if (document.getElementById('page-portfolio').classList.contains('active')) {
            await loadPortfolio();
        }
    } catch (error) {
        showNotification(`Trade failed: ${error.message}`, 'error');
    }
}

// ============== AI Assistant ==============

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Add loading message
    const loadingId = addChatMessage('Thinking...', 'ai', true);

    try {
        const response = await apiCall('/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ message })
        });

        // Remove loading message
        document.getElementById(loadingId)?.remove();

        // Add AI response
        addChatMessage(response.response, 'ai');
    } catch (error) {
        document.getElementById(loadingId)?.remove();
        addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
    }
}

function addChatMessage(content, sender, isLoading = false) {
    const container = document.getElementById('chatContainer');
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
    return `₹${parseFloat(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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
    const container = document.querySelector('.toast-container') || createToastContainer();

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

    // Remove after animation (4s + buffer)
    setTimeout(() => {
        toast.remove();
    }, 4500);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function navigateToPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show selected page
    document.getElementById(`page-${pageName}`).classList.add('active');

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');

    // Load page data
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
    document.getElementById('loginModal').classList.remove('active');
}

function closeTradeModal() {
    document.getElementById('tradeModal').classList.remove('active');
}

// ============== Event Listeners ==============

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    if (authToken) {
        loadUserProfile();
        loadDashboard();
        hideLoginModal();
    }

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navigateToPage(link.dataset.page);
        });
    });

    // Auth forms
    document.getElementById('loginForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        login(email, password);
    });

    document.getElementById('registerForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('registerEmail').value;
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;
        const fullName = document.getElementById('registerFullName').value;
        register(email, username, password, fullName);
    });

    // Auth tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchAuthTab(tab.dataset.tab));
    });

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', logout);

    // Chat input
    document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');

    document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
}
