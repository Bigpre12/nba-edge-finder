/**
 * NBA Edge Finder - Ultra-light Frontend
 * Features:
 * - Accessible tabs with keyboard navigation
 * - AbortController to cancel in-flight requests
 * - localStorage + memory cache with TTL
 * - Auto-poll when tab is focused
 * - Fallback UI for stale data
 */

// === Configuration ===
const CONFIG = {
    API_BASE: '/api',           // Local API (or use GitHub raw URL)
    CACHE_TTL: 60000,           // 60 seconds cache TTL
    POLL_INTERVAL: 15000,       // 15 seconds auto-refresh
    STALE_THRESHOLD: 300000,    // 5 minutes = stale data
};

// === State ===
let currentTab = 'pts';
let currentController = null;  // AbortController for in-flight requests
let propsData = null;
let lastFetch = 0;
let pollTimer = null;
let minProbability = 70;

// === Memory Cache ===
const memCache = new Map();

function getCached(key) {
    // Check memory first
    const memItem = memCache.get(key);
    if (memItem && Date.now() - memItem.time < CONFIG.CACHE_TTL) {
        return memItem.data;
    }
    
    // Check localStorage
    try {
        const stored = localStorage.getItem(`nba_${key}`);
        if (stored) {
            const item = JSON.parse(stored);
            if (Date.now() - item.time < CONFIG.CACHE_TTL) {
                // Promote to memory cache
                memCache.set(key, item);
                return item.data;
            }
        }
    } catch (e) {
        console.warn('localStorage error:', e);
    }
    
    return null;
}

function setCached(key, data) {
    const item = { data, time: Date.now() };
    
    // Memory cache
    memCache.set(key, item);
    
    // localStorage (with size limit)
    try {
        localStorage.setItem(`nba_${key}`, JSON.stringify(item));
    } catch (e) {
        // localStorage full - clear old items
        try {
            localStorage.clear();
            localStorage.setItem(`nba_${key}`, JSON.stringify(item));
        } catch (e2) {
            console.warn('localStorage full:', e2);
        }
    }
}

// === Fetch with AbortController ===
async function fetchData(endpoint, forceRefresh = false) {
    const cacheKey = endpoint;
    
    // Check cache first (unless force refresh)
    if (!forceRefresh) {
        const cached = getCached(cacheKey);
        if (cached) {
            console.log(`Cache hit: ${endpoint}`);
            return cached;
        }
    }
    
    // Cancel previous request
    if (currentController) {
        currentController.abort();
    }
    currentController = new AbortController();
    
    // Show spinner
    showSpinner(true);
    hideError();
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
            signal: currentController.signal,
            headers: {
                'Accept': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Cache the result
        setCached(cacheKey, data);
        lastFetch = Date.now();
        
        showSpinner(false);
        return data;
        
    } catch (error) {
        showSpinner(false);
        
        if (error.name === 'AbortError') {
            console.log('Request aborted');
            return null;
        }
        
        console.error('Fetch error:', error);
        
        // Try to return stale cache
        const stale = getCached(cacheKey);
        if (stale) {
            showError(`Using cached data. Error: ${error.message}`);
            return stale;
        }
        
        showError(`Failed to load data: ${error.message}`);
        return null;
    } finally {
        currentController = null;
    }
}

// === UI Helpers ===
function showSpinner(show) {
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.hidden = !show;
    }
}

function showError(message) {
    const banner = document.getElementById('errorBanner');
    const text = document.getElementById('errorText');
    if (banner && text) {
        text.textContent = message;
        banner.hidden = false;
    }
}

function hideError() {
    const banner = document.getElementById('errorBanner');
    if (banner) {
        banner.hidden = true;
    }
}

function updateStatus(data) {
    const timeEl = document.getElementById('updateTime');
    const countEl = document.getElementById('propCount');
    
    if (data && data.updated) {
        const updated = new Date(data.updated);
        const ago = Math.round((Date.now() - updated.getTime()) / 60000);
        timeEl.textContent = `Updated ${ago}m ago`;
        
        // Check if stale
        if (Date.now() - updated.getTime() > CONFIG.STALE_THRESHOLD) {
            timeEl.classList.add('stale');
        } else {
            timeEl.classList.remove('stale');
        }
    } else {
        timeEl.textContent = 'Unknown';
    }
    
    if (data && data.count !== undefined) {
        countEl.textContent = `${data.count} props`;
    }
}

// === Render Props ===
function renderProps(data, statType) {
    if (!data || !data.props) {
        return '<div class="no-data">No data available</div>';
    }
    
    let props = data.props;
    
    // Filter by stat type
    if (statType !== 'all') {
        props = props.filter(p => p.props && p.props[statType]);
    }
    
    // Filter by probability
    props = props.filter(p => {
        if (statType === 'all') {
            // Check any stat meets threshold
            return Object.values(p.props || {}).some(s => s.prob >= minProbability);
        }
        const stat = p.props?.[statType];
        return stat && stat.prob >= minProbability;
    });
    
    // Sort by probability (highest first)
    props.sort((a, b) => {
        const getProb = (p) => {
            if (statType === 'all') {
                return Math.max(...Object.values(p.props || {}).map(s => s.prob || 0));
            }
            return p.props?.[statType]?.prob || 0;
        };
        return getProb(b) - getProb(a);
    });
    
    if (props.length === 0) {
        return '<div class="no-data">No props match filters</div>';
    }
    
    if (statType === 'all') {
        // Render all stats for each player
        return props.map(p => `
            <div class="prop-card">
                <div class="player-name">${escapeHtml(p.player)}</div>
                <div class="props-list">
                    ${Object.entries(p.props || {}).map(([stat, data]) => `
                        <div class="prop-row ${data.prob >= 70 ? 'high-prob' : ''}">
                            <span class="stat-type">${stat.toUpperCase()}</span>
                            <span class="line">${data.line}</span>
                            <span class="pick pick-${data.pick.toLowerCase()}">${data.pick}</span>
                            <span class="prob">${data.prob}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }
    
    // Render single stat type
    return props.map(p => {
        const stat = p.props?.[statType];
        if (!stat) return '';
        
        return `
            <div class="prop-card ${stat.prob >= 70 ? 'high-prob' : ''}">
                <div class="player-name">${escapeHtml(p.player)}</div>
                <div class="prop-details">
                    <div class="line-row">
                        <span class="label">Line:</span>
                        <span class="value">${stat.line}</span>
                    </div>
                    <div class="avg-row">
                        <span class="label">Avg:</span>
                        <span class="value">${stat.avg}</span>
                    </div>
                </div>
                <div class="prop-action">
                    <span class="pick pick-${stat.pick.toLowerCase()}">${stat.pick}</span>
                    <span class="prob">${stat.prob}%</span>
                </div>
            </div>
        `;
    }).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// === Tab Management ===
function switchTab(tabId) {
    const statType = tabId.replace('tab-', '');
    currentTab = statType;
    
    // Update tab states
    document.querySelectorAll('[role="tab"]').forEach(tab => {
        const isSelected = tab.id === tabId;
        tab.setAttribute('aria-selected', isSelected);
        tab.setAttribute('tabindex', isSelected ? '0' : '-1');
        tab.classList.toggle('active', isSelected);
    });
    
    // Update panel visibility
    document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
        const isActive = panel.id === `panel-${statType}`;
        panel.hidden = !isActive;
        panel.classList.toggle('active', isActive);
    });
    
    // Load data for this tab
    loadTabData(statType);
}

async function loadTabData(statType) {
    const data = await fetchData('/props');
    
    if (data) {
        propsData = data;
        updateStatus(data);
        
        const contentEl = document.getElementById(`content-${statType}`);
        if (contentEl) {
            contentEl.innerHTML = renderProps(data, statType);
        }
    }
}

// === Keyboard Navigation ===
function setupKeyboardNav() {
    const tablist = document.querySelector('[role="tablist"]');
    if (!tablist) return;
    
    const tabs = tablist.querySelectorAll('[role="tab"]');
    
    tablist.addEventListener('keydown', (e) => {
        const currentIndex = Array.from(tabs).findIndex(t => t === document.activeElement);
        let newIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                break;
            case 'Home':
                e.preventDefault();
                newIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                newIndex = tabs.length - 1;
                break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (document.activeElement.role === 'tab') {
                    switchTab(document.activeElement.id);
                }
                return;
            default:
                return;
        }
        
        tabs[newIndex].focus();
        switchTab(tabs[newIndex].id);
    });
}

// === Auto-polling ===
function startPolling() {
    if (pollTimer) return;
    
    pollTimer = setInterval(() => {
        if (document.visibilityState === 'visible') {
            console.log('Auto-refresh...');
            loadTabData(currentTab);
        }
    }, CONFIG.POLL_INTERVAL);
}

function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
}

// === Global refresh function ===
function refreshData() {
    loadTabData(currentTab);
}

// === Initialization ===
function init() {
    console.log('NBA Edge Finder initializing...');
    
    // Setup tab click handlers
    document.querySelectorAll('[role="tab"]').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.id));
    });
    
    // Setup keyboard navigation
    setupKeyboardNav();
    
    // Setup filter
    const filterEl = document.getElementById('minProb');
    if (filterEl) {
        filterEl.addEventListener('change', (e) => {
            minProbability = parseInt(e.target.value, 10);
            loadTabData(currentTab);
        });
    }
    
    // Load initial data
    loadTabData(currentTab);
    
    // Start polling when visible
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            startPolling();
            loadTabData(currentTab);  // Refresh on return
        } else {
            stopPolling();
        }
    });
    
    // Start polling
    startPolling();
    
    console.log('NBA Edge Finder ready');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
