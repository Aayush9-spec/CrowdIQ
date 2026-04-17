const dashboard = {
    crowdChart: null,
    zoneChart: null,
    history: [],
    maxHistory: 20,

    init() {
        this.initCharts();
        this.startHeartbeatLoop();
        this.updateNavigation(); 
        this.updateStaffRecommendations();
    },

    initCharts() {
        const ctxCrowd = document.getElementById('crowdChart').getContext('2d');
        const ctxZone = document.getElementById('zoneChart').getContext('2d');

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

        this.crowdChart = new Chart(ctxCrowd, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Live Attendance',
                    data: [],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });

        this.zoneChart = new Chart(ctxZone, {
            type: 'doughnut',
            data: {
                labels: ['Stands', 'Gates', 'Food', 'Restrooms'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#6366f1', '#06b6d4', '#f59e0b', '#f43f5e'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 20 } }
                },
                cutout: '70%'
            }
        });
    },

    // --- New Heartbeat Logic ---
    startHeartbeatLoop() {
        this.updateHeartbeat();
        setInterval(() => this.updateHeartbeat(), 10000); // Pulse every 10s
    },

    async updateHeartbeat() {
        try {
            const res = await fetch('/health');
            const data = await res.json();
            
            this.toggleHB('hb-bigquery', data.services.bigquery === 'connected');
            this.toggleHB('hb-gcs', data.services.storage === 'connected');
            this.toggleHB('hb-gemini', true); // Gemini always considered 'active' if API responds
        } catch (e) {
            console.warn('Heartbeat check failed', e);
        }
    },

    toggleHB(id, active) {
        const dot = document.querySelector(`#${id} .status-dot-small`);
        if (dot) {
            dot.classList.toggle('active', active);
        }
    },

    // --- Navigation Optimization ---
    async updateNavigation() {
        try {
            const res = await fetch('/api/navigation/least-crowded');
            const data = await res.json();
            this.renderNavOptimizations(data.optimal_routes);
        } catch (e) {
            console.error('Nav update failed', e);
        }
    },

    renderNavOptimizations(routes) {
        const container = document.getElementById('recommendations-container');
        if (!container || !routes) return;

        container.innerHTML = `
            <div class="card" style="margin-top: 32px; border-left: 4px solid var(--secondary);">
                <h3 style="margin-bottom: 20px; font-size: 16px; color: var(--secondary);">Optimal Routes (Least Crowded)</h3>
                <div class="stats-grid" style="margin-bottom: 0;">
                    ${Object.entries(routes).map(([type, info]) => `
                        <div style="background: rgba(255,255,255,0.02); padding: 16px; border-radius: 12px; border: 1px solid var(--glass-border);">
                            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">${type}</div>
                            <div style="font-size: 18px; font-weight: 700; margin: 4px 0;">${info.target_zone}</div>
                            <div style="font-size: 13px; color: var(--accent-success);">${info.occupancy} Load • ${info.wait_time}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    async updateStaffRecommendations() {
        try {
            const res = await fetch('/api/staff/recommendations');
            const data = await res.json();
            this.renderStaffRecommendations(data.recommendations);
        } catch (e) {
            console.error('Staff update failed', e);
        }
    },

    renderStaffRecommendations(recommendations) {
        const container = document.getElementById('staff-recommendations-container');
        if (!container || !recommendations) return;

        // Convert markdown bullet points to HTML list items if necessary
        const items = recommendations.split('\n')
            .filter(line => line.trim().startsWith('*') || line.trim().startsWith('-'))
            .map(line => `<li>${line.replace(/^[*-]\s*/, '')}</li>`)
            .join('');

        container.innerHTML = `
            <div class="card" style="border-left: 4px solid var(--accent-primary);">
                <h3 style="margin-bottom: 20px; font-size: 16px; color: var(--accent-primary); display: flex; align-items: center; gap: 8px;">
                    <span>🛡️</span> Strategic Staff Logistics (AI Analysis)
                </h3>
                <div style="background: rgba(99, 102, 241, 0.05); padding: 20px; border-radius: 12px; border: 1px dashed rgba(99, 102, 241, 0.3);">
                    <ul style="margin: 0; padding-left: 20px; color: var(--text-light); line-height: 1.6;">
                        ${items || `<li>${recommendations}</li>`}
                    </ul>
                </div>
            </div>
        `;
    },


    updateCharts(status, analytics) {
        if (!this.crowdChart || !this.zoneChart) return;

        // Update Line Chart
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        this.history.push({ time: now, count: status.total_crowd });
        
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }

        this.crowdChart.data.labels = this.history.map(h => h.time);
        this.crowdChart.data.datasets[0].data = this.history.map(h => h.count);
        this.crowdChart.update('none');

        // Update Doughnut Chart
        this.fetchZoneData();
        
        // Refresh nav and staff periodically
        if (Math.random() > 0.8) {
            this.updateNavigation();
            this.updateStaffRecommendations();
        }
    },


    async fetchZoneData() {
        try {
            const res = await fetch('/api/venue');
            const data = await res.json();
            
            const types = { 'stand': 0, 'gate': 0, 'food': 0, 'restroom': 0, 'parking': 0 };
            data.zones.forEach(z => {
                if (types.hasOwnProperty(z.type)) {
                    types[z.type] += z.current_count;
                }
            });

            this.zoneChart.data.datasets[0].data = [
                types['stand'], 
                types['gate'], 
                types['food'], 
                types['restroom']
            ];
            this.zoneChart.update();
        } catch (e) {
            console.error('Error fetching zone data for chart', e);
        }
    }
};

window.dashboard = dashboard;
document.addEventListener('DOMContentLoaded', () => dashboard.init());
