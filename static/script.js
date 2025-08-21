document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENT SELECTORS ---
    const recommendationsGrid = document.querySelector('.recommendations-grid');
    const searchBtn = document.getElementById('search-btn');
    const tickerInput = document.getElementById('ticker-input');
    const resultsContainer = document.getElementById('results-container');
    const loader = document.getElementById('loader');
    const errorContainer = document.getElementById('error-container');
    const watchlistList = document.getElementById('watchlist-list');
    const addToWatchlistBtn = document.getElementById('add-to-watchlist-btn');
    const timeframeControls = document.getElementById('timeframe-controls');

    let historicalChart = null;
    let currentTicker = null;
    let watchlist = JSON.parse(localStorage.getItem('credtech_watchlist')) || [];
    let autoRefreshInterval = null;

    const renderWatchlist = () => {
        watchlistList.innerHTML = '';
        if (watchlist.length === 0) {
            watchlistList.innerHTML = '<p style="color: #888;">Your watchlist is empty.</p>';
            return;
        }
        watchlist.forEach(ticker => {
            const li = document.createElement('li');
            li.textContent = ticker;
            li.addEventListener('click', () => { tickerInput.value = ticker; fetchScore(); });
            const removeBtn = document.createElement('button');
            removeBtn.textContent = '✖';
            removeBtn.className = 'remove-watchlist';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                watchlist = watchlist.filter(t => t !== ticker);
                localStorage.setItem('credtech_watchlist', JSON.stringify(watchlist));
                renderWatchlist();
            });
            li.appendChild(removeBtn);
            watchlistList.appendChild(li);
        });
    };

    addToWatchlistBtn.addEventListener('click', () => {
        if (currentTicker && !watchlist.includes(currentTicker)) {
            watchlist.push(currentTicker);
            localStorage.setItem('credtech_watchlist', JSON.stringify(watchlist));
            renderWatchlist();
        }
    });

    const renderChart = async (ticker, period = '1m') => {
        try {
            const response = await fetch(`/history/${ticker}/${period}`);
            const data = await response.json();
            const ctx = document.getElementById('historical-chart').getContext('2d');
            if (historicalChart) { historicalChart.destroy(); }
            historicalChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Object.keys(data),
                    datasets: [{
                        label: `${ticker} ${period.toUpperCase()} Price`,
                        data: Object.values(data),
                        borderColor: '#007bff', tension: 0.1, fill: false
                    }]
                },
                options: { scales: { x: { ticks: { color: '#888' } }, y: { ticks: { color: '#888' } } }, plugins: { legend: { labels: { color: '#e0e0e0' } } } }
            });
        } catch (error) { console.error('Error fetching historical data:', error); }
    };

    const renderPeerScores = (peers) => { /* ... unchanged ... */ };
    const renderExplanation = (explanation) => { /* ... unchanged ... */ };

    const setupAutoRefresh = (ticker) => {
        if (autoRefreshInterval) clearInterval(autoRefreshInterval);
        autoRefreshInterval = setInterval(() => {
            console.log(`Auto-refreshing score for ${ticker}...`);
            fetchScore(true); // Pass flag to indicate auto-refresh
        }, 60000);
    };

    const fetchScore = async (isAutoRefresh = false) => {
        const ticker = isAutoRefresh ? currentTicker : tickerInput.value.toUpperCase().trim();
        if (!ticker) {
            errorContainer.innerText = 'Please enter a ticker symbol.';
            errorContainer.classList.remove('hidden'); return;
        }
        currentTicker = ticker;
        if (!isAutoRefresh) {
            loader.classList.remove('hidden');
            resultsContainer.classList.add('hidden');
        }
        errorContainer.classList.add('hidden');

        try {
            const response = await fetch(`/score/${ticker}`);
            const data = await response.json();
            if (!response.ok) { throw new Error(data.error || 'An unknown error occurred.'); }

            document.getElementById('company-name').innerText = data.company_name;
            const scoreElement = document.getElementById('credit-score');
            scoreElement.innerText = data.credit_score;
            scoreElement.className = '';
            if (data.credit_score > 65) scoreElement.classList.add('score-good');
            else if (data.credit_score < 40) scoreElement.classList.add('score-bad');
            else scoreElement.classList.add('score-neutral');
            
            // --- UPDATE: MAKE HEADLINES CLICKABLE ---
            const headlinesList = document.getElementById('headlines-list');
            headlinesList.innerHTML = '';
            data.recent_headlines.forEach(article => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = article.url;
                a.textContent = article.title;
                a.target = '_blank';
                li.appendChild(a);
                headlinesList.appendChild(li);
            });

            renderExplanation(data.explanation);
            renderPeerScores(data.peer_scores);
            if (!isAutoRefresh) { await renderChart(ticker, '1m'); }

            resultsContainer.classList.remove('hidden');
            setupAutoRefresh(ticker);
        } catch (error) {
            errorContainer.innerText = `Error: ${error.message}`;
            errorContainer.classList.remove('hidden');
        } finally {
            if (!isAutoRefresh) loader.classList.add('hidden');
        }
    };

    searchBtn.addEventListener('click', () => fetchScore());
    tickerInput.addEventListener('keyup', (event) => { if (event.key === 'Enter') fetchScore(); });
    recommendationsGrid.addEventListener('click', (event) => {
        if (event.target.classList.contains('recommendation-btn')) {
            tickerInput.value = event.target.dataset.ticker;
            fetchScore();
        }
    });
    timeframeControls.addEventListener('click', (e) => {
        if (e.target.classList.contains('timeframe-btn')) {
            document.querySelectorAll('.timeframe-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            if (currentTicker) renderChart(currentTicker, e.target.dataset.period);
        }
    });

    renderWatchlist();
});