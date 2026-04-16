const notifications = {
    container: null,
    lastAlertIds: new Set(),

    init() {
        this.container = document.getElementById('alerts-container');
    },

    updateList(alerts) {
        if (!this.container) return;

        if (alerts.length === 0) {
            this.container.innerHTML = `
                <div class="message assistant" style="text-align: center; max-width: 100%;">
                    No active alerts at this time.
                </div>
            `;
            return;
        }

        // Check for new critical alerts to show as browser notifications or toasts
        alerts.forEach(alert => {
            if (!this.lastAlertIds.has(alert.id)) {
                if (alert.severity === 'critical') {
                    this.showToast(alert);
                }
                this.lastAlertIds.add(alert.id);
            }
        });

        this.container.innerHTML = alerts.map(alert => {
            const time = new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            return `
                <div class="alert-item alert-${alert.severity}">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong style="font-size: 16px;">${alert.title}</strong>
                        <span style="font-size: 12px; color: var(--text-muted);">${time}</span>
                    </div>
                    <div style="font-size: 14px; line-height: 1.4;">${alert.message}</div>
                </div>
            `;
        }).join('');
    },

    showToast(alert) {
        // Simple implementation of a critical toast
        console.log("CRITICAL ALERT:", alert.title, alert.message);
        // This could be a floating UI element
    }
};

window.notifications = notifications;
document.addEventListener('DOMContentLoaded', () => notifications.init());
