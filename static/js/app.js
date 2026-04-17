document.addEventListener('DOMContentLoaded', () => {
    const app = {
        currentTab: 'dashboard',
        dataRefreshInterval: 5000,
        
        init() {
            this.setupNavigation();
            this.setupPhaseSelector();
            this.startDataPolling();
            this.updateTime();
            setInterval(() => this.updateTime(), 60000);
        },

        setupPhaseSelector() {
            const selector = document.getElementById('phase-selector');
            if (selector) {
                selector.addEventListener('change', async (e) => {
                    const newPhase = e.target.value;
                    try {
                        const res = await fetch('/api/simulation/phase', {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                            },
                            body: JSON.stringify({ phase: newPhase })
                        });
                        const data = await res.json();
                        if (data.status === 'success') {
                            this.fetchData(); // Refresh UI immediately
                        }
                    } catch (error) {
                        console.error('Error setting phase:', error);
                    }
                });
            }
        },

        setupNavigation() {
            const navItems = document.querySelectorAll('.nav-item');
            const tabPanels = document.querySelectorAll('.tab-panel');
            const pageTitle = document.getElementById('page-title');

            navItems.forEach(item => {
                const switchTab = () => {
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
                };

                item.addEventListener('click', switchTab);
                item.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        switchTab();
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
                
                // Render Smart Recommendations
                this.renderRecommendations(analytics.recommendations);

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

        renderRecommendations(recs) {
            const container = document.getElementById('recommendations-container');
            if (!container) return;

            if (!recs || recs.length === 0) {
                container.innerHTML = '';
                return;
            }

            container.innerHTML = `
                <div class="card-title" style="margin-bottom: 12px; margin-top: 10px;">Smart Relocation Alerts</div>
                ${recs.map(r => `
                    <div class="rec-card">
                        <div class="rec-content">
                            <div class="rec-title">Optimize Crowd Flow: ${r.type.toUpperCase()}</div>
                            <div class="rec-message">${r.message}</div>
                        </div>
                        <button class="rec-btn" onclick="window.App.flyToZoneByName('${r.to_zone}')">View Alternative</button>
                    </div>
                `).join('')}
            `;
        },

        async flyToZoneByName(name) {
            try {
                const res = await fetch('/api/venue');
                const data = await res.json();
                const zone = data.zones.find(z => z.name === name);
                if (zone && window.venueMapModule) {
                    // Update tab to map
                    document.querySelector('[data-tab="map"]').click();
                    // Fly to location
                    setTimeout(() => {
                        window.venueMapModule.flyToZone(zone.lat, zone.lng);
                    }, 500);
                }
            } catch (e) {
                console.error('Error flying to zone', e);
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
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div class="card-value">${p.current_wait}m</div>
                            <button class="rec-btn" style="padding: 4px 10px; font-size: 11px;" onclick="window.App.flyToZoneById('${p.zone_id}')">Map</button>
                        </div>
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

        async flyToZoneById(id) {
            try {
                const res = await fetch('/api/venue');
                const data = await res.json();
                const zone = data.zones.find(z => z.id === id);
                if (zone && window.venueMapModule) {
                    document.querySelector('[data-tab="map"]').click();
                    setTimeout(() => {
                        window.venueMapModule.flyToZone(zone.lat, zone.lng);
                    }, 500);
                }
            } catch (e) {
                console.error('Error flying to zone', e);
            }
        },

        updateTime() {
            // Could add a clock to header if needed
        }
    };

    window.App = app;
    app.init();
});
