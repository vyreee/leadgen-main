# lead_generator.py
import requests
import time
from typing import Dict, List, Optional, Any
import streamlit as st
from urllib.parse import quote
import json

class LeadGenerator:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Missing Google API Key")
        self.api_key = api_key
        self.delay_between_requests = 0.5  # Adjustable delay
        
    def _get_location_bounds(self, location: str) -> Optional[Dict]:
        """Get the viewport bounds for a location to ensure we stay within city limits"""
        try:
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={quote(location)}&key={self.api_key}"
            response = requests.get(geocode_url)
            data = response.json()
            
            if data['status'] != 'OK':
                raise ValueError(f"Could not geocode location: {location}")
                
            viewport = data['results'][0]['geometry']['viewport']
            return {
                'lat': data['results'][0]['geometry']['location']['lat'],
                'lng': data['results'][0]['geometry']['location']['lng'],
                'bounds': viewport
            }
            
        except Exception as e:
            st.error(f"Error getting location bounds: {str(e)}")
            return None
            
    def _is_within_bounds(self, lat: float, lng: float, bounds: Dict) -> bool:
        """Check if coordinates are within viewport bounds"""
        return (bounds['southwest']['lat'] <= lat <= bounds['northeast']['lat'] and
                bounds['southwest']['lng'] <= lng <= bounds['northeast']['lng'])
    
    def generate_leads(self, business_type: str, location: str, max_results: int = 300) -> List[Dict]:
        """Generate leads using Google Places API with location bounds checking"""
        try:
            leads = []
            processed_places = set()  # Track processed place IDs
            
            # Get location data
            location_data = self._get_location_bounds(location)
            if not location_data:
                return []
                
            lat, lng = location_data['lat'], location_data['lng']
            bounds = location_data['bounds']
            
            # Initial search parameters
            base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            next_page_token = None
            
            while len(leads) < max_results:
                # Prepare search parameters
                params = {
                    'query': f"{business_type} in {location}",
                    'key': self.api_key,
                    'location': f"{lat},{lng}",
                }
                
                if next_page_token:
                    params['pagetoken'] = next_page_token
                    time.sleep(2)  # Required delay for next page token
                
                # Make request
                response = requests.get(base_url, params=params)
                data = response.json()
                
                if data['status'] != 'OK':
                    break
                
                # Process results
                for place in data['results']:
                    if len(leads) >= max_results:
                        break
                        
                    # Skip if already processed
                    if place['place_id'] in processed_places:
                        continue
                        
                    processed_places.add(place['place_id'])
                    
                    # Check if within bounds
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    
                    if not self._is_within_bounds(place_lat, place_lng, bounds):
                        continue
                    
                    # Get detailed information
                    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                    details_params = {
                        'place_id': place['place_id'],
                        'fields': 'name,formatted_address,formatted_phone_number,website,business_status',
                        'key': self.api_key
                    }
                    
                    details_response = requests.get(details_url, params=details_params)
                    details_data = details_response.json()
                    
                    if details_data['status'] == 'OK':
                        result = details_data['result']
                        
                        # Skip if not operational
                        if result.get('business_status') != 'OPERATIONAL':
                            continue
                        
                        lead = {
                            'company_name': result.get('name', ''),
                            'full_address': result.get('formatted_address', ''),
                            'Phone': result.get('formatted_phone_number', 'N/A'),
                            'Website': result.get('website', 'N/A'),
                            'Business Type': business_type
                        }
                        
                        leads.append(lead)
                        st.write(f"Found: {lead['company_name']}")
                    
                    time.sleep(self.delay_between_requests)
                
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break
            
            return leads
            
        except Exception as e:
            st.error(f"Error generating leads: {str(e)}")
            return []