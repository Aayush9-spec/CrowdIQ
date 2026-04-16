const dashboard = {
    crowdChart: null,
    zoneChart: null,
    history: [],
    maxHistory: 20,

    init() {
        this.initCharts();
    },

    initCharts() {
        const ctxCrowd = document.getElementById('crowdChart').getContext('2d');
        const ctxZone = document.getElementById('zoneChart').getContext('2d');

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', sans-serif";

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

        // Update Doughnut Chart (Simulate grouping from analytics later)
        // For now, let's just get data from a direct venue fetch once in app.js
        this.fetchZoneData();
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
