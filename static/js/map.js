const venueMapModule = {
    map: null,
    heatmap: null,
    zones: [],
    markers: [],

    init() {
        // Wait for Google Maps to be loaded
        if (typeof google === 'undefined') {
            setTimeout(() => this.init(), 500);
            return;
        }
        this.initMap();
    },

    initMap() {
        const stadiumCenter = { lat: 12.9706, lng: 77.5946 };
        
        this.map = new google.maps.Map(document.getElementById('map-container'), {
            zoom: 18,
            center: stadiumCenter,
            mapTypeId: 'satellite',
            styles: [
                { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
                { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
                { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
            ],
            tilt: 45,
            heading: 90,
            disableDefaultUI: true,
            zoomControl: true
        });

        window.venueMap = this.map;
        this.updateHeatmap();
    },

    async updateHeatmap() {
        if (!this.map) return;

        try {
            const res = await fetch('/api/venue');
            const data = await res.json();
            
            const heatmapData = [];
            
            // Clear old markers if any
            this.markers.forEach(m => m.setMap(null));
            this.markers = [];

            data.zones.forEach(zone => {
                // Create heatmap point with weight based on occupancy
                heatmapData.push({
                    location: new google.maps.LatLng(zone.lat, zone.lng),
                    weight: Math.max(1, zone.current_count / 100)
                });

                // Add informational markers for key zones
                if (zone.type !== 'stand') {
                    const marker = new google.maps.Marker({
                        position: { lat: zone.lat, lng: zone.lng },
                        map: this.map,
                        title: zone.name,
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 6,
                            fillColor: this.getZoneColor(zone.type),
                            fillOpacity: 0.8,
                            strokeWeight: 2,
                            strokeColor: '#fff'
                        }
                    });
                    
                    const infoWindow = new google.maps.InfoWindow({
                        content: `<div style="color:#000"><strong>${zone.name}</strong><br>Wait time: ${zone.wait_time_minutes}m<br>Occupancy: ${zone.occupancy_rate}%</div>`
                    });

                    marker.addListener("click", () => {
                        infoWindow.open(this.map, marker);
                    });
                    
                    this.markers.push(marker);
                }
            });

            if (this.heatmap) {
                this.heatmap.setData(heatmapData);
            } else {
                this.heatmap = new google.maps.visualization.HeatmapLayer({
                    data: heatmapData,
                    map: this.map,
                    radius: 30,
                    opacity: 0.7
                });
            }
        } catch (e) {
            console.error('Error updating map data', e);
        }
    },

    getZoneColor(type) {
        switch(type) {
            case 'gate': return '#06b6d4';
            case 'food': return '#f59e0b';
            case 'restroom': return '#f43f5e';
            case 'parking': return '#94a3b8';
            default: return '#6366f1';
        }
    }
};

window.venueMapModule = venueMapModule;
document.addEventListener('DOMContentLoaded', () => venueMapModule.init());
