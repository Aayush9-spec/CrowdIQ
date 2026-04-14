# 🏟️ CrowdIQ — Smart Venue Experience Platform

**CrowdIQ** is an intelligent, real-time venue experience platform designed to enhance the physical event experience at large-scale sporting venues. It addresses the core challenges of **crowd movement**, **waiting times**, and **real-time coordination** through AI-powered insights, live venue maps, and a smart assistant.

## 🎯 Chosen Vertical
**Physical Event Experience at Large-Scale Sporting Venues**

## 💡 The Problem
In large stadiums (60,000+ capacity), attendees often face:
- Long, unpredictable wait times at food stalls and restrooms.
- Confusion regarding entry/exit routes during peak crowd flow.
- Lack of real-time information about crowd density in specific zones.
- Minimal personalized guidance during the event.

## 🚀 The Solution: CrowdIQ
CrowdIQ solves these issues by providing a unified digital companion that:
1. **Visualizes Crowd Density**: Uses Google Maps with a live heatmap to show real-time crowd levels across the venue.
2. **Predicts Wait Times**: Employs AI-driven algorithms to estimate current and future wait times for amenities.
3. **Assists Attendees**: Features a Gemini-powered AI Assistant that provides context-aware navigation and safety tips.
4. **Alerts in Real-Time**: Provides system-wide notifications for crowd surges, phase changes, and safety updates.

## 🛠️ Technology Stack
- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
- **Backend**: Python Flask, Gunicorn
- **AI**: Google Gemini API (`gemini-2.0-flash`)
- **Maps**: Google Maps JavaScript API (Visualization & Heatmap Layers)
- **Deployment**: Google Cloud Run (Containerized with Docker)
- **Simulation**: Custom multi-threaded crowd flow engine

## 🧠 Approach and Logic

### 1. Crowd Simulation Engine
Since real sensor data is proprietary, CrowdIQ features a sophisticated **Crowd Simulation Engine**. It models crowd flow based on event phases (Pre-Match, Ongoing, Halftime, Post-Match). People flow realistically between parking, gates, stands, and amenities using randomized but weighted probability distributions.

### 2. Gemini AI Integration
The **CrowdIQ Assistant** is grounded in the current state of the venue. Every request to the Gemini API includes a "Venue Context" (current phase, total crowd, zone-level density, and wait times). This ensures the AI provides factual, real-time advice rather than generic responses.

### 3. Dynamic Heatmapping
The platform uses the **Google Maps JavaScript API** to render a weighted heatmap. Each zone (Stand, Gate, Restroom) is mapped to geo-coordinates. The current crowd count in each zone determines the "intensity" of the heatmap point, providing an intuitive visual for attendees.

## 📦 How to Run Local

### Prerequisites
- Python 3.11+
- Google Maps API Key
- Google Gemini API Key

### Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd CrowdIQ
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set Up Environment Variables:
   Create a `.env` file or export them:
   ```bash
   export GOOGLE_MAPS_API_KEY='your-key'
   export GEMINI_API_KEY='your-key'
   ```

4. Run the app:
   ```bash
   python app.py
   ```
5. Access at `http://localhost:8080`

## 🌍 Google Services Used
- **Google Maps API**: Core visualization of the venue and layout.
- **Gemini AI**: Powering the smart conversational assistant.
- **Google Cloud Run**: Hosting the production-grade application for scale.

## 📜 Assumptions Made
- The venue is modeled as a generic 60,000-seat national stadium.
- Wait times are calculated using a queue-theory heuristic based on current zone occupancy.
- Real-world sensor data is simulated via a multi-threaded state machine.
