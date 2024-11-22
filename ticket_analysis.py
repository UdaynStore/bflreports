import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re

def extract_email_domain(email):
    if pd.isna(email):
        return "Unknown"
    match = re.search(r"@([\w.-]+)", email)
    return match.group(1) if match else "Unknown"

def analyze_tickets(df):
    # Basic cleaning
    df['Email Domain'] = df['Contact ID'].apply(extract_email_domain)
    
    # Create layout
    st.title("Support Ticket Analysis Dashboard")
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tickets", len(df))
    with col2:
        st.metric("Open Tickets", len(df[df['Status'] == 'Open']))
    with col3:
        st.metric("Waiting Tickets", len(df[df['Status'] == 'Waiting on Third Party']))
    
    # Status Distribution
    st.subheader("Ticket Status Distribution")
    status_dist = df['Status'].value_counts()
    fig_status = px.pie(values=status_dist.values, 
                       names=status_dist.index,
                       title="Ticket Status Distribution")
    st.plotly_chart(fig_status)
    
    # Top Email Domains
    st.subheader("Top Email Domains")
    domain_counts = df['Email Domain'].value_counts().head(10)
    fig_domains = px.bar(x=domain_counts.index, 
                        y=domain_counts.values,
                        title="Top 10 Email Domains",
                        labels={'x': 'Domain', 'y': 'Number of Tickets'})
    st.plotly_chart(fig_domains)
    
    # Common Patterns Analysis
    st.subheader("Common Patterns in Tickets")
    
    # Detect order-related tickets
    order_related = df['Subject'].str.contains('order|Order|OID', case=False, na=False).sum()
    fwd_tickets = df['Subject'].str.startswith('Fwd:', na=False).sum()
    
    pattern_data = pd.DataFrame({
        'Pattern': ['Order Related', 'Forwarded Tickets'],
        'Count': [order_related, fwd_tickets]
    })
    
    fig_patterns = px.bar(pattern_data, 
                         x='Pattern', 
                         y='Count',
                         title="Common Ticket Patterns")
    st.plotly_chart(fig_patterns)
    
    # Ticket Details Table
    st.subheader("Ticket Details")
    st.dataframe(df)

def main():
    st.set_page_config(page_title="Support Ticket Analysis", 
                      layout="wide",
                      initial_sidebar_state="expanded")
    
    st.sidebar.title("Upload Data")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            analyze_tickets(df)
        except Exception as e:
            st.error(f"Error reading the file: {str(e)}")
    else:
        st.info("Please upload a CSV file to begin analysis")

if __name__ == "__main__":
    main()