class CrowdEngine:
    def __init__(self, venue, simulation):
        self.venue = venue
        self.simulation = simulation

    def get_crowd_analytics(self):
        zones = self.venue.get_all_zones()
        
        # Sort zones by occupancy
        highly_crowded = [z for z in zones if z['occupancy_rate'] > 75]
        moderate_crowded = [z for z in zones if 40 <= z['occupancy_rate'] <= 75]
        low_crowded = [z for z in zones if z['occupancy_rate'] < 40]
        
        return {
            "summary": {
                "highly_crowded_count": len(highly_crowded),
                "moderate_crowded_count": len(moderate_crowded),
                "low_crowded_count": len(low_crowded),
                "avg_occupancy": round(sum(z['occupancy_rate'] for z in zones) / len(zones), 1) if zones else 0
            },
            "top_crowded": sorted(highly_crowded, key=lambda x: x['occupancy_rate'], reverse=True)[:3],
            "recommendations": self._generate_recommendations(highly_crowded, low_crowded)
        }

    def _generate_recommendations(self, highly_crowded, low_crowded):
        recs = []
        for crowded_zone in highly_crowded:
            # Find a less crowded alternative of the same type
            alternatives = [z for z in low_crowded if z['type'] == crowded_zone['type']]
            if alternatives:
                best_alt = alternatives[0]
                recs.append({
                    "from_zone": crowded_zone['name'],
                    "to_zone": best_alt['name'],
                    "type": crowded_zone['type'],
                    "message": f"{crowded_zone['name']} is busy. Try {best_alt['name']} for shorter wait times."
                })
        return recs

    def get_wait_time_predictions(self):
        zones = self.venue.get_all_zones()
        amenities = [z for z in zones if z['type'] in ['food', 'restroom', 'gate']]
        
        predictions = []
        for zone in amenities:
            # Simple prediction: If occupancy increasing, wait time will increase
            # In simulation, we'll just add some "trend" metadata
            trend = "stable"
            if zone['occupancy_rate'] > 60:
                trend = "increasing"
            elif zone['occupancy_rate'] < 30:
                trend = "decreasing"
                
            predictions.append({
                "zone_id": zone['id'],
                "name": zone['name'],
                "type": zone['type'],
                "current_wait": zone['wait_time_minutes'],
                "predicted_wait_15m": zone['wait_time_minutes'] + (5 if trend == "increasing" else -2 if trend == "decreasing" else 0),
                "trend": trend
            })
            
        return predictions

    def get_venue_context_for_ai(self):
        status = self.simulation.get_status()
        zones = self.venue.get_all_zones()
        
        zones_summary = []
        for z in zones:
            zones_summary.append(f"{z['name']} ({z['type']}): {z['occupancy_rate']}% full, {z['wait_time_minutes']} min wait")
            
        return {
            "name": self.venue.name,
            "phase": status['phase'],
            "total_crowd": status['total_crowd'],
            "zones_summary": ". ".join(zones_summary[:10])  # Limit for prompt size
        }
