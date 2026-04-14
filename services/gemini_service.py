from google import genai
import os
from config import get_config

config = get_config()

class GeminiService:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing Gemini client: {e}")

    def get_ai_response(self, user_message, venue_context):
        if not self.client:
            return "Gemini API key not configured. I'm currently in offline mode but can still help with basic venue information!"

        system_instruction = f"""
        You are CrowdIQ Assistant, a smart AI guide for the CrowdIQ National Stadium.
        Your goal is to help attendees with navigation, wait times, safety, and general venue information.
        
        Current Venue Context:
        - Venue Name: {venue_context.get('name')}
        - Event Phase: {venue_context.get('phase')}
        - Total Crowd: {venue_context.get('total_crowd')}
        - Zones Info: {venue_context.get('zones_summary')}
        
        Guidelines:
        1. Be helpful, concise, and professional.
        2. Use the provided venue context to give accurate information about wait times and crowd levels.
        3. If a zone is over 80% capacity, suggest alternative less crowded areas.
        4. In case of emergency queries, provide clear exit instructions.
        5. If asked about something not in the context, politely state you don't have that specific real-time data but provide general helpful advice based on standard stadium layouts.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                config={
                    "system_instruction": system_instruction,
                },
                contents=[user_message]
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "I'm having trouble connecting to my brain right now. Please try again or check the dashboard for live updates!"

# Singleton instance
gemini_service = GeminiService()
