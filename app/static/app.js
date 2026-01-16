/**
 * RepoScraper Frontend Application
 * A clean, reactive vanilla JS app for architecture search
 */

const API_BASE = '';

// State
const state = {
    currentView: 'search',
    searchResults: [],
    githubResults: [],
    indexedRepos: [],
    tags: [],
    loading: false
};

// DOM Elements
const elements = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    cacheElements();
    bindEvents();
    checkApiHealth();
});

function cacheElements() {
    elements.navBtns = document.querySelectorAll('.nav-btn');
    elements.views = document.querySelectorAll('.view');
    elements.statusDot = document.querySelector('.status-dot');
    elements.statusText = document.querySelector('.status-text');
    
    // Search view
    elements.architectureSearch = document.getElementById('architecture-search');
    elements.searchBtn = document.getElementById('search-btn');
    elements.searchResults = document.getElementById('search-results');
    elements.minConfidence = document.getElementById('min-confidence');
    elements.confidenceValue = document.getElementById('confidence-value');
    
    // Discover view
    elements.githubSearch = document.getElementById('github-search');
    elements.languageFilter = document.getElementById('language-filter');
    elements.githubSearchBtn = document.getElementById('github-search-btn');
    elements.githubResults = document.getElementById('github-results');
    elements.minStars = document.getElementById('min-stars');
    
    // Indexed view
    elements.indexedResults = document.getElementById('indexed-results');
    elements.tagsCloud = document.getElementById('tags-cloud');
    elements.statRepos = document.getElementById('stat-repos');
    elements.statTags = document.getElementById('stat-tags');
    
    elements.toastContainer = document.getElementById('toast-container');
}

function bindEvents() {
    // Navigation
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
    
    // Search view
    elements.searchBtn.addEventListener('click', performArchitectureSearch);
    elements.architectureSearch.addEventListener('keypress', e => {
        if (e.key === 'Enter') performArchitectureSearch();
    });
    elements.minConfidence.addEventListener('input', e => {
        elements.confidenceValue.textContent = (e.target.value / 100).toFixed(1);
    });
    
    // Discover view
    elements.githubSearchBtn.addEventListener('click', performGitHubSearch);
    elements.githubSearch.addEventListener('keypress', e => {
        if (e.key === 'Enter') performGitHubSearch();
    });
}

function switchView(viewName) {
    state.currentView = viewName;
    
    // Update nav buttons
    elements.navBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });
    
    // Update views
    elements.views.forEach(view => {
        view.classList.toggle('active', view.id === `view-${viewName}`);
    });
    
    // Load data for the view
    if (viewName === 'indexed') {
        loadIndexedRepos();
        loadTags();
    }
}

// API Functions
async function checkApiHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        if (data.status === 'healthy') {
            elements.statusDot.style.background = 'var(--success)';
            elements.statusText.textContent = 'API Connected';
        }
    } catch (err) {
        elements.statusDot.style.background = 'var(--error)';
        elements.statusText.textContent = 'API Offline';
    }
}

async function performArchitectureSearch() {
    const query = elements.architectureSearch.value.trim();
    if (!query) return;
    
    const minConfidence = elements.minConfidence.value / 100;
    
    elements.searchResults.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const res = await fetch(
            `${API_BASE}/api/search?query=${encodeURIComponent(query)}&min_confidence=${minConfidence}`
        );
        const results = await res.json();
        
        if (results.length === 0) {
            elements.searchResults.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">∅</div>
                    <p>No repositories found</p>
                    <span class="empty-hint">Try different search terms or ingest more repos</span>
                </div>
            `;
            return;
        }
        
        renderSearchResults(results);
    } catch (err) {
        showToast('Search failed: ' + err.message, 'error');
        elements.searchResults.innerHTML = '<div class="empty-state"><p>Search failed</p></div>';
    }
}

async function performGitHubSearch() {
    const query = elements.githubSearch.value.trim();
    const language = elements.languageFilter.value;
    const minStars = elements.minStars.value || 1000;
    
    elements.githubResults.innerHTML = '<div class="loading">Searching GitHub...</div>';
    
    try {
        let url = `${API_BASE}/api/github/search?min_stars=${minStars}&max_results=20`;
        if (query) url += `&query=${encodeURIComponent(query)}`;
        if (language) url += `&language=${encodeURIComponent(language)}`;
        
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.repositories.length === 0) {
            elements.githubResults.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">☆</div>
                    <p>No repositories found</p>
                </div>
            `;
            return;
        }
        
        renderGitHubResults(data.repositories);
    } catch (err) {
        showToast('GitHub search failed: ' + err.message, 'error');
        elements.githubResults.innerHTML = '<div class="empty-state"><p>Search failed</p></div>';
    }
}

async function loadIndexedRepos() {
    try {
        const res = await fetch(`${API_BASE}/api/repos?limit=50`);
        const repos = await res.json();
        
        elements.statRepos.textContent = repos.length;
        
        if (repos.length === 0) {
            elements.indexedResults.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">▤</div>
                    <p>No repositories indexed yet</p>
                    <span class="empty-hint">Use Discover to find and ingest repos</span>
                </div>
            `;
            return;
        }
        
        renderIndexedRepos(repos);
    } catch (err) {
        elements.indexedResults.innerHTML = '<div class="empty-state"><p>Failed to load</p></div>';
    }
}

async function loadTags() {
    try {
        const res = await fetch(`${API_BASE}/api/tags`);
        const tags = await res.json();
        
        elements.statTags.textContent = tags.length;
        
        if (tags.length === 0) {
            elements.tagsCloud.innerHTML = '<span class="empty-hint">No tags yet</span>';
            return;
        }
        
        // Sort by count and take top 20
        const topTags = tags.sort((a, b) => b.count - a.count).slice(0, 20);
        
        elements.tagsCloud.innerHTML = topTags.map(tag => `
            <span class="cloud-tag" onclick="searchByTag('${tag.tag}')">
                ${tag.tag}<span class="count">${tag.count}</span>
            </span>
        `).join('');
    } catch (err) {
        elements.tagsCloud.innerHTML = '';
    }
}

async function ingestRepo(fullName, button) {
    const [owner, repo] = fullName.split('/');
    
    button.disabled = true;
    button.classList.add('loading');
    button.innerHTML = 'Analyzing...';
    
    try {
        const res = await fetch(`${API_BASE}/api/repos/ingest/${owner}/${repo}?analyze=true`, {
            method: 'POST'
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || `Ingestion failed (${res.status})`);
        }
        
        const data = await res.json();
        
        button.classList.remove('loading');
        button.innerHTML = '✓ Indexed';
        button.style.background = 'var(--success)';
        button.style.borderColor = 'var(--success)';
        button.style.color = '#fff';
        
        showToast(`${repo} analyzed and indexed!`, 'success');
        
    } catch (err) {
        button.disabled = false;
        button.classList.remove('loading');
        button.innerHTML = '↻ Retry';
        showToast('Ingestion failed: ' + err.message, 'error');
    }
}

// Render Functions
function renderSearchResults(results) {
    elements.searchResults.innerHTML = `
        <div class="repo-grid">
            ${results.map(result => `
                <div class="repo-card">
                    <span class="relevance-badge">Score: ${result.relevance_score.toFixed(2)}</span>
                    <div class="repo-header">
                        <div class="repo-name">
                            <a href="${result.repository.url}" target="_blank">${result.repository.full_name}</a>
                        </div>
                        <div class="repo-stars">★ ${formatNumber(result.repository.stars)}</div>
                    </div>
                    <p class="repo-description">${result.repository.description || 'No description'}</p>
                    <div class="repo-meta">
                        ${result.repository.language ? `
                            <span class="repo-language">
                                <span class="lang-dot"></span>
                                ${result.repository.language}
                            </span>
                        ` : ''}
                    </div>
                    <div class="repo-tags">
                        ${(result.matched_tags || []).slice(0, 5).map(tag => `
                            <span class="tag">${tag}</span>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderGitHubResults(repos) {
    elements.githubResults.innerHTML = `
        <div class="repo-grid">
            ${repos.map(repo => `
                <div class="repo-card">
                    <div class="repo-header">
                        <div class="repo-name">
                            <a href="${repo.url}" target="_blank">${repo.full_name}</a>
                        </div>
                        <div class="repo-stars">★ ${formatNumber(repo.stars)}</div>
                    </div>
                    <p class="repo-description">${repo.description || 'No description'}</p>
                    <div class="repo-meta">
                        ${repo.language ? `
                            <span class="repo-language">
                                <span class="lang-dot"></span>
                                ${repo.language}
                            </span>
                        ` : ''}
                    </div>
                    <button class="ingest-btn" onclick="ingestRepo('${repo.full_name}', this)">
                        ⬇ Analyze & Index
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

function renderIndexedRepos(repos) {
    elements.indexedResults.innerHTML = `
        <div class="repo-grid">
            ${repos.map(repo => `
                <div class="repo-card">
                    <div class="repo-header">
                        <div class="repo-name">
                            <a href="${repo.url}" target="_blank">${repo.full_name}</a>
                        </div>
                        <div class="repo-stars">★ ${formatNumber(repo.stars)}</div>
                    </div>
                    <p class="repo-description">${repo.description || 'No description'}</p>
                    <div class="repo-meta">
                        ${repo.language ? `
                            <span class="repo-language">
                                <span class="lang-dot"></span>
                                ${repo.language}
                            </span>
                        ` : ''}
                    </div>
                    <div class="repo-tags">
                        ${(repo.architecture_tags || []).slice(0, 6).map(tag => `
                            <span class="tag ${tag.tag_type}">${tag.tag}</span>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Utility Functions
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function searchByTag(tag) {
    switchView('search');
    elements.architectureSearch.value = tag;
    performArchitectureSearch();
}

// Global functions for onclick handlers
window.ingestRepo = ingestRepo;
window.searchByTag = searchByTag;
