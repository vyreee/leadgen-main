# lead_processor.py
import pandas as pd
from typing import Dict, List, Any
import streamlit as st
from urllib.parse import urlparse
import time
import json
from io import BytesIO

class LeadProcessor:
    def __init__(self, scraper, analyzer, email_finder, generator):
        self.scraper = scraper
        self.analyzer = analyzer
        self.email_finder = email_finder
        self.generator = generator  # Add this line this line


    def _format_list_to_string(self, data: List[Any]) -> str:
        """Convert list to string representation"""
        if not data:
            return ""
        return "; ".join(str(item) for item in data if item)

    def _clean_string(self, value: Any) -> str:
        """Clean and format string values"""
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()

    def process_lead(self, lead: Dict) -> Dict:
        """Process a single lead"""
        try:
            website = self._clean_string(lead.get('Website', ''))
            if not website or website.lower() == 'n/a':
                return self._create_empty_result(lead)

            # Basic website data extraction
            website_data = self.scraper.scrape_website(website)
            
            # Simple email pattern matching first
            emails = self.email_finder.extract_emails_from_text(website_data['content'])
            
            # Analysis with cost-optimized LLM
            analysis = self.analyzer.analyze_content(website_data)
            
            # Generate potential emails if owner found
            domain = urlparse(website).netloc.replace('www.', '')
            potential_emails = []
            if analysis.get('owner_name'):
                potential_emails = self.email_finder.generate_potential_emails(
                    domain, 
                    analysis.get('owner_name')
                )

            return {
                'company_name': self._clean_string(lead.get('company_name')),
                'full_address': self._clean_string(lead.get('full_address')),
                'town': self._clean_string(lead.get('town')),
                'Phone': self._clean_string(lead.get('Phone')),
                'Website': website,
                'Business Type': self._clean_string(lead.get('Business Type')),
                'processed': True,
                'owner_name': self._clean_string(analysis.get('owner_name')),
                'owner_title': self._clean_string(analysis.get('owner_title')),
                'confidence': self._clean_string(analysis.get('confidence', 'low')),
                'confidence_reasoning': self._clean_string(analysis.get('confidence_reasoning')),
                'discovered_emails': self._format_list_to_string(emails),
                'potential_emails': self._format_list_to_string(potential_emails),
                'key_facts': self._format_list_to_string(analysis.get('key_facts', [])),
                'error': ''
            }

        except Exception as e:
            return self._create_empty_result(lead, str(e))

    def _create_empty_result(self, lead: Dict, error: str = "") -> Dict:
        """Create an empty result with basic lead info"""
        return {
            'company_name': self._clean_string(lead.get('company_name')),
            'full_address': self._clean_string(lead.get('full_address')),
            'town': self._clean_string(lead.get('town')),
            'Phone': self._clean_string(lead.get('Phone')),
            'Website': self._clean_string(lead.get('Website')),
            'Business Type': self._clean_string(lead.get('Business Type')),
            'processed': False,
            'owner_name': '',
            'owner_title': '',
            'confidence': 'none',
            'confidence_reasoning': '',
            'discovered_emails': '',
            'potential_emails': '',
            'key_facts': '',
            'error': error
        }

    def process_leads(self, leads: pd.DataFrame) -> pd.DataFrame:
        """Process multiple leads"""
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Define columns for output
        columns = [
            'company_name', 'full_address', 'town', 'Phone', 'Website', 
            'Business Type', 'processed', 'error', 'owner_name', 'owner_title',
            'confidence', 'confidence_reasoning', 'discovered_emails', 
            'potential_emails', 'key_facts'
        ]
        
        try:
            for idx, row in leads.iterrows():
                status_text.text(f"Processing {idx + 1}/{len(leads)}: {row.get('company_name', '')}")
                result = self.process_lead(row.to_dict())
                results.append(result)
                progress_bar.progress((idx + 1) / len(leads))
                time.sleep(0.5)  # Reduced rate limiting
            
            # Create DataFrame with specified columns
            df = pd.DataFrame(results)
            df = df[columns]
            df = df.fillna('')  # Clean up any NaN values
            
            return df
            
        except Exception as e:
            st.error(f"Error in batch processing: {str(e)}")
            return pd.DataFrame(columns=columns)

    def download_excel(self, df: pd.DataFrame, filename: str) -> bytes:
        """Create Excel file in memory"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')
        output.seek(0)
        return output.getvalue()


    def download_leads_csv(self, leads: List[Dict], filename: str = "generated_leads.csv"):
        """Download the generated leads as a CSV file."""
        df = pd.DataFrame(leads)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Leads as CSV",
            data=csv,
            file_name=filename,
            mime='text/csv'
        )