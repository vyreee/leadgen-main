# Add these imports at the top of main.py
import streamlit as st
import pandas as pd
import plotly.express as px  # Add this import
from scraper import EnhancedWebsiteScraper
from analyzer import EnhancedContentAnalyzer
from email_finder import EmailFinder
from lead_processor import LeadProcessor
from lead_generator import LeadGenerator
from lead_quality_finder import LeadQualityFilter, LeadQualityConfig
import traceback

def init_api_components(openai_key, google_key):
    """Initialize API components with validation and debugging"""
    try:
        st.write("Initializing Scraper...")
        scraper = EnhancedWebsiteScraper()
        
        st.write("Initializing Content Analyzer...")
        analyzer = EnhancedContentAnalyzer(api_key=str(openai_key).strip())
        
        st.write("Initializing Email Finder...")
        email_finder = EmailFinder(api_key=str(openai_key).strip())
        
        st.write("Initializing Lead Generator...")
        lead_generator = LeadGenerator(api_key=str(google_key).strip())
        
        st.write("Initializing Lead Quality Filter...")
        quality_config = LeadQualityConfig(
            min_key_facts=3,
            require_website=True,
            require_email=True,
            require_owner_info=True,
            min_confidence_level="medium",
            strict_location_match=True
        )
        quality_filter = LeadQualityFilter(config=quality_config)
        
        st.write("Initializing Lead Processor...")
        processor = LeadProcessor(
            scraper=scraper,
            analyzer=analyzer,
            email_finder=email_finder,
            generator=lead_generator
        )
        
        st.write("All components initialized successfully!")
        return processor
        
    except Exception as e:
        st.error("🚨 Initialization Error")
        st.error(f"Error details: {str(e)}")
        st.error(f"Error location:\n{traceback.format_exc()}")
        return None

def main():
    st.set_page_config(page_title="Lead Generator Pro", layout="wide")
    st.title("🎯 Lead Generator Pro")

    # Business type definitions
    business_types = {
        "Real Estate": "real estate agent OR realtor",
        "Insurance Agent": "insurance agent OR insurance broker",
        "Financial Advisor": "financial advisor OR financial planner",
        "Lawyer": "lawyer OR attorney OR law firm",
        "Doctor": "doctor OR physician OR medical practice",
        "Dentist": "dentist OR dental practice",
        "Accountant": "accountant OR CPA OR accounting firm",
        "Marketing Agency": "marketing agency OR digital marketing",
        "Home Services": "home services",
        "Health & Wellness": "health and wellness",
        "Automotive Services": "automotive services",
        "Professional Services": "professional services",
        "Health & Beauty": "health and beauty",
        "Restaurants & Food Services": "restaurants and food services",
        "Fitness & Sports": "fitness and sports",
        "Event & Entertainment Services": "event and entertainment services",
        "Education & Tutoring": "education and tutoring",
        "Pet Services": "pet services",
        "Retail & Local Shops": "retail and local shops",
        "Unique & Miscellaneous Local Businesses": "unique local businesses",
        "Celebrations & Parties": "celebrations and parties",
        "Weddings": "weddings",
        "Baby & Parenting Events": "baby and parenting events",
        "Graduations & Educational Milestones": "graduations and educational milestones"
    }

    # Add API key inputs in sidebar
    st.sidebar.title("API Configuration")

    openai_api_key = st.sidebar.text_input(
        "OpenAI API Key", 
        type="password",
        help="Get your API key from https://platform.openai.com/api-keys"
    )
    
    google_api_key = st.sidebar.text_input(
        "Google Places API Key",
        type="password",
        help="Get your API key from https://console.cloud.google.com/apis/credentials"
    )

    # Check for API keys
    if not openai_api_key or not google_api_key:
        st.warning("Please enter your API keys in the sidebar to use the application.")
        return

    # Initialize processor with explicit error handling
    processor = init_api_components(
        openai_key=openai_api_key,
        google_key=google_api_key
    )
    
    if not processor:
        st.error("Failed to initialize the application. Please check the error messages above.")
        return

   # Update the tabs section in main.py

    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Upload Leads", "Generate Leads", "Clean Leads"])

    # Upload Leads tab remains the same...
    with tab1:

        st.header("Process Existing Leads")
        uploaded_file = st.file_uploader("Upload CSV with leads", type="csv")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                required_cols = ['company_name', 'Website']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    return
                
                if st.button("Process Leads"):
                    with st.spinner("Processing leads..."):
                        # Remove duplicates
                        df = df.drop_duplicates(subset=['company_name', 'Website'])
                        st.write(f"Processing {len(df)} unique leads...")
                        
                        # Process leads
                        results_df = processor.process_leads(df)
                        
                        # Show results and download options
                        st.success("Processing complete!")
                        st.write("Results:")
                        st.dataframe(results_df)
                        
                        # Prepare download options
                        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                        
                        # CSV download
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"processed_leads_{timestamp}.csv",
                            mime="text/csv"
                        )
                        
                        # Excel download
                        excel_data = processor.download_excel(results_df, f"processed_leads_{timestamp}.xlsx")
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name=f"processed_leads_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.error(f"Error details:\n{traceback.format_exc()}")

    # Generate Leads tab
    with tab2:
        st.header("Generate New Leads")
        
        col1, col2 = st.columns(2)
    
        with col1:
            selected_type = st.selectbox(
                "Select Business Type",
                options=list(business_types.keys())
            )
            
            location = st.text_input(
                "Location (City, State)",
                placeholder="e.g., Newbern, NC"
            )
        
        with col2:
            max_results = st.slider(
                "Maximum Results",
                min_value=50,
                max_value=300,
                value=100
            )
        
        # Add Generate Leads button after the columns
        if st.button("Generate Leads", key="generate_leads_btn"):
            if not location or ',' not in location:
                st.error("Please enter location in City, State format")
                return
            
            try:
                with st.spinner("Generating leads..."):
                    # Generate leads
                    leads = processor.generator.generate_leads(
                        business_type=business_types[selected_type],
                        location=location,
                        max_results=max_results
                    )
                
                if leads:
                    # Convert to DataFrame
                    leads_df = pd.DataFrame(leads)
                    
                    # Remove duplicates
                    leads_df = leads_df.drop_duplicates(subset=['company_name', 'Website'])
                    
                    st.write(f"Found {len(leads_df)} unique leads")
                    st.dataframe(leads_df)

                    # Add downloads for raw leads
                    col1, col2 = st.columns(2)
                    with col1:
                        # CSV download for raw leads
                        csv = leads_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Raw Leads (CSV)",
                            data=csv,
                            file_name=f"raw_leads_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="raw_leads_csv"
                        )
                    
                    with col2:
                        # Excel download for raw leads
                        excel_data = processor.download_excel(leads_df, "raw_leads.xlsx")
                        st.download_button(
                            label="📊 Download Raw Leads (Excel)",
                            data=excel_data,
                            file_name=f"raw_leads_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="raw_leads_excel"
                        )
                    
                    st.write("---")  # Add a separator
                    
                    if st.button("Process Generated Leads", key="process_generated_leads"):
                        with st.spinner("Processing leads..."):
                            # Process leads with owner/email discovery
                            results_df = processor.process_leads(leads_df)
                        
                        st.success("Processing complete!")
                        st.write("Results with owner information:")
                        st.dataframe(results_df)
                        
                        # Prepare downloads for processed leads
                        col1, col2 = st.columns(2)
                        with col1:
                            # CSV download for processed leads
                            csv = results_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Processed Leads (CSV)",
                                data=csv,
                                file_name=f"processed_leads_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="processed_leads_csv"
                            )
                        
                        with col2:
                            # Excel download for processed leads
                            excel_data = processor.download_excel(results_df, "processed_leads.xlsx")
                            st.download_button(
                                label="📊 Download Processed Leads (Excel)",
                                data=excel_data,
                                file_name=f"processed_leads_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="processed_leads_excel"
                            )
                    
            except Exception as e:
                st.error(f"Error generating leads: {str(e)}")
                st.error(f"Error details:\n{traceback.format_exc()}")

    # New Clean Leads tab
    with tab3:
        st.header("Clean Processed Leads")
        
        uploaded_file = st.file_uploader("Upload processed leads CSV", type="csv", key="clean_leads")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                col1, col2 = st.columns(2)
                
                with col1:
                    min_quality = st.slider(
                        "Minimum Quality Score",
                        min_value=0,
                        max_value=100,
                        value=70,
                        help="Filter leads with quality score above this threshold"
                    )
                    
                    require_website = st.checkbox("Must have website", value=True)
                    require_email = st.checkbox("Must have email", value=True)
                
                with col2:
                    require_owner = st.checkbox("Must have owner info", value=True)
                    min_facts = st.number_input(
                        "Minimum key facts",
                        min_value=1,
                        max_value=10,
                        value=3
                    )
                
                if st.button("Clean Leads"):
                    with st.spinner("Cleaning leads..."):
                        # Initialize quality filter with user config
                        quality_config = LeadQualityConfig(
                            min_key_facts=min_facts,
                            require_website=require_website,
                            require_email=require_email,
                            require_owner_info=require_owner,
                            min_confidence_level="medium",
                            strict_location_match=False
                        )
                        quality_filter = LeadQualityFilter(config=quality_config)
                        
                        # Convert DataFrame to list of dicts for filtering
                        leads_list = df.to_dict('records')
                        
                        # Add quality scores
                        scored_df = quality_filter.enrich_leads_with_scores(leads_list)
                        
                        # Filter based on minimum quality score
                        filtered_df = scored_df[scored_df['quality_score'] >= min_quality]
                        
                        # Show results
                        st.success(f"Found {len(filtered_df)} leads meeting criteria")
                        st.write("Quality Score Distribution:")
                        
                        # Show quality score distribution
                        fig = px.histogram(filtered_df, x='quality_score', nbins=10)
                        st.plotly_chart(fig)
                        
                        # Display results with color coding
                        st.write("Filtered Results:")
                        st.dataframe(
                            filtered_df.style.background_gradient(
                                subset=['quality_score'],
                                cmap='RdYlGn',
                                vmin=0,
                                vmax=100
                            )
                        )
                        
                        # Prepare downloads
                        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                        
                        # CSV download
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Filtered CSV",
                            data=csv,
                            file_name=f"cleaned_leads_{timestamp}.csv",
                            mime="text/csv"
                        )
                        
                        # Excel download
                        excel_data = processor.download_excel(filtered_df, f"cleaned_leads_{timestamp}.xlsx")
                        st.download_button(
                            label="📊 Download Filtered Excel",
                            data=excel_data,
                            file_name=f"cleaned_leads_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.error(f"Error details:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()