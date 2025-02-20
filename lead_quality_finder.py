# lead_quality_filter.py
from typing import Dict, List, Any
import pandas as pd
from dataclasses import dataclass
import re

@dataclass
class LeadQualityConfig:
    """Configuration for lead quality filtering"""
    min_key_facts: int = 3
    require_website: bool = True
    require_email: bool = True
    require_owner_info: bool = True
    min_confidence_level: str = "medium"
    strict_location_match: bool = True
    
class LeadQualityFilter:
    def __init__(self, config: LeadQualityConfig = None):
        self.config = config or LeadQualityConfig()
        
    def _has_valid_website(self, lead: Dict[str, Any]) -> bool:
        """Check if lead has a valid website"""
        website = str(lead.get('Website', '')).lower()
        return (website not in ['', 'n/a', 'none', 'nan'] and 
                any(website.startswith(prefix) for prefix in ['http://', 'https://']))
    
    def _has_valid_email(self, lead: Dict[str, Any]) -> bool:
        """Check if lead has valid email information"""
        discovered_emails = str(lead.get('discovered_emails', ''))
        potential_emails = str(lead.get('potential_emails', ''))
        return bool(discovered_emails.strip() or potential_emails.strip())
    
    def _has_sufficient_key_facts(self, lead: Dict[str, Any]) -> bool:
        """Check if lead has enough key facts"""
        key_facts = str(lead.get('key_facts', ''))
        if not key_facts.strip():
            return False
        # Count facts by splitting on semicolons
        facts_count = len([f for f in key_facts.split(';') if f.strip()])
        return facts_count >= self.config.min_key_facts
    
    def _has_owner_info(self, lead: Dict[str, Any]) -> bool:
        """Check if lead has owner information"""
        owner_name = str(lead.get('owner_name', '')).strip()
        confidence = str(lead.get('confidence', '')).lower()
        return (bool(owner_name) and 
                confidence in ['high', 'medium'] and 
                owner_name.lower() not in ['none', 'n/a', 'unknown'])
    
    def _matches_location(self, lead: Dict[str, Any], target_location: str) -> bool:
        """Check if lead matches the target location strictly"""
        if not self.config.strict_location_match:
            return True
            
        lead_address = str(lead.get('full_address', '')).lower()
        target_location = target_location.lower()
        
        # Split location into city and state
        location_parts = target_location.split(',')
        if len(location_parts) != 2:
            return True  # Skip validation if location format is unexpected
            
        city, state = map(str.strip, location_parts)
        
        # Check if both city and state are in the address
        return city in lead_address and state in lead_address
    
    def filter_leads(self, leads: List[Dict[str, Any]], target_location: str = None) -> List[Dict[str, Any]]:
        """Filter leads based on quality criteria"""
        filtered_leads = []
        
        for lead in leads:
            # Skip leads without required fields
            if self.config.require_website and not self._has_valid_website(lead):
                continue
                
            if self.config.require_email and not self._has_valid_email(lead):
                continue
                
            if self.config.require_owner_info and not self._has_owner_info(lead):
                continue
                
            if not self._has_sufficient_key_facts(lead):
                continue
                
            if target_location and not self._matches_location(lead, target_location):
                continue
                
            filtered_leads.append(lead)
            
        return filtered_leads
    
    def calculate_quality_score(self, lead: Dict[str, Any]) -> float:
        """Calculate a quality score for a lead (0-100)"""
        score = 0
        
        # Website availability (20 points)
        if self._has_valid_website(lead):
            score += 20
            
        # Email availability (20 points)
        if self._has_valid_email(lead):
            score += 20
            
        # Key facts (30 points)
        key_facts = str(lead.get('key_facts', '')).split(';')
        facts_count = len([f for f in key_facts if f.strip()])
        score += min(facts_count * 10, 30)  # Up to 30 points for 3 or more facts
            
        # Owner information (30 points)
        if self._has_owner_info(lead):
            confidence = str(lead.get('confidence', '')).lower()
            if confidence == 'high':
                score += 30
            elif confidence == 'medium':
                score += 20
                
        return score
    
    def enrich_leads_with_scores(self, leads: List[Dict[str, Any]]) -> pd.DataFrame:
        """Add quality scores to leads and return as DataFrame"""
        enriched_leads = []
        
        for lead in leads:
            lead_copy = lead.copy()
            lead_copy['quality_score'] = self.calculate_quality_score(lead)
            enriched_leads.append(lead_copy)
            
        df = pd.DataFrame(enriched_leads)
        if not df.empty:
            df = df.sort_values('quality_score', ascending=False)
            
        return df