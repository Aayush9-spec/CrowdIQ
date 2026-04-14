document.addEventListener('DOMContentLoaded', () => {
    const app = {
        currentTab: 'dashboard',
        dataRefreshInterval: 5000,
        
        init() {
            this.setupNavigation();
            this.startDataPolling();
            this.updateTime();
            setInterval(() => this.updateTime(), 60000);
        },

        setupNavigation() {
            const navItems = document.querySelectorAll('.nav-item');
            const tabPanels = document.querySelectorAll('.tab-panel');
            const pageTitle = document.getElementById('page-title');

            navItems.forEach(item => {
                item.addEventListener('click', () => {
                    const tabId = item.getAttribute('data-tab');
                    
                    // Update active nav
                    navItems.forEach(nav => nav.classList.remove('active'));
                    item.classList.add('active');

                    // Update active panel
                    tabPanels.forEach(panel => panel.classList.remove('active'));
                    document.getElementById(tabId).classList.add('active');

                    // Update header title
                    const titles = {
                        'dashboard': 'Venue Overview',
                        'map': 'Live Venue Heatmap',
                        'wait-times': 'Amenity Wait Times',
                        'assistant': 'AI Venue Assistant',
                        'alerts': 'Safety & System Alerts'
                    };
                    pageTitle.textContent = titles[tabId] || 'CrowdIQ';
                    
                    this.currentTab = tabId;
                    
                    // Trigger map resize if needed
                    if (tabId === 'map' && window.venueMap) {
                        google.maps.event.trigger(window.venueMap, 'resize');
                    }
                });
            });
        },

        startDataPolling() {
            this.fetchData();
            setInterval(() => this.fetchData(), this.dataRefreshInterval);
        },

        async fetchData() {
            try {
                const [statusRes, analyticsRes, alertRes] = await Promise.all([
                    fetch('/api/status'),
                    fetch('/api/analytics'),
                    fetch('/api/alerts')
                ]);

                const status = await statusRes.json();
                const analytics = await analyticsRes.json();
                const alerts = await alertRes.json();

                this.updateUI(status, analytics, alerts);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        },

        updateUI(status, analytics, alerts) {
            // Update Global Header
            document.getElementById('current-phase').textContent = status.phase.replace('_', ' ');
            document.getElementById('total-crowd').textContent = status.total_crowd.toLocaleString();

            // Update Dashboard metrics
            if (this.currentTab === 'dashboard') {
                document.getElementById('avg-occupancy').textContent = analytics.summary.avg_occupancy + '%';
                
                // Trigger dashboard chart updates
                if (window.dashboard) {
                    window.dashboard.updateCharts(status, analytics);
                }
            }

            // Update Alerts notification badge
            const badge = document.getElementById('alert-count-badge');
            if (alerts.length > 0) {
                badge.textContent = alerts.length;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }

            // Trigger notification center update
            if (window.notifications) {
                window.notifications.updateList(alerts);
            }

            // Trigger Map update
            if (window.venueMapModule) {
                window.venueMapModule.updateHeatmap();
            }
            
            // Trigger Wait times update
            if (this.currentTab === 'wait-times') {
                this.updateWaitTimes();
            }
        },

        async updateWaitTimes() {
            try {
                const res = await fetch('/api/wait-times');
                const predictions = await res.json();
                const container = document.getElementById('wait-times-container');
                
                container.innerHTML = predictions.map(p => `
                    <div class="card">
                        <div class="card-title">${p.name}</div>
                        <div class="card-value">${p.current_wait}m</div>
                        <div class="card-trend ${p.trend === 'increasing' ? 'trend-down' : 'trend-up'}">
                            ${p.trend === 'increasing' ? '↑ Increasing' : p.trend === 'decreasing' ? '↓ Decreasing' : '→ Stable'}
                        </div>
                        <div style="font-size: 12px; margin-top: 10px; color: var(--text-muted);">
                            Predicted in 15m: <strong>${p.predicted_wait_15m}m</strong>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error updating wait times:', error);
            }
        },

        updateTime() {
            // Could add a clock to header if needed
        }
    };

    window.App = app;
    app.init();
});
