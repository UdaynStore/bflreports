import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np


def load_and_process_data(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Convert date columns to datetime with the correct format
    # For columns in DD-MM-YYYY HH:MM format
    df['Order Create Date & Time'] = pd.to_datetime(df['Order Create Date & Time'], format='%d-%m-%Y %H:%M', errors='coerce')
    
    # For columns in ISO format (YYYY-MM-DDThh:mm:ss.sssZ)
    # Convert to UTC and then remove timezone information
    df['Delivered At Date & Time'] = pd.to_datetime(df['Delivered At Date & Time'], errors='coerce').dt.tz_localize(None)
    df['Shipped At Date & Time'] = pd.to_datetime(df['Shipped At Date & Time'], errors='coerce').dt.tz_localize(None)
    df['Ready to Ship At Date & Time'] = pd.to_datetime(df['Ready to Ship At Date & Time'], errors='coerce').dt.tz_localize(None)
    df['Cancelled At Date & Time'] = pd.to_datetime(df['Cancelled At Date & Time'], errors='coerce').dt.tz_localize(None)
    
    # Extract hour from order creation time
    df['Order Hour'] = df['Order Create Date & Time'].dt.hour
    
    # Calculate progress status
    status_mapping = {
        'Completed': 100,
        'In-progress': 75,
        'Accepted': 25
    }
    df['Progress_Status'] = df['Order Status'].map(status_mapping)
    
    return df


def calculate_sla_status(row):
    """Calculate if order is within SLA based on category"""
    try:
        if pd.isna(row['Order Create Date & Time']) or pd.isna(row['Delivered At Date & Time']):
            return 'NA'
        
        # Ensure both timestamps are timezone naive
        create_time = row['Order Create Date & Time']
        deliver_time = row['Delivered At Date & Time']
        
        if create_time.tzinfo:
            create_time = create_time.tz_localize(None)
        if deliver_time.tzinfo:
            deliver_time = deliver_time.tz_localize(None)
            
        # Calculate delivery time in hours
        delivery_time = (deliver_time - create_time).total_seconds() / 3600
        
        if row['Order Category'] == 'F&B':
            threshold = 1
        elif row['Order Category'] == 'Grocery':
            threshold = 3
        else:  # Electronics or other categories
            threshold = 5 * 24  # 5 days in hours
            
        return 'Within SLA' if delivery_time <= threshold else 'SLA Breached'
    except Exception as e:
        print(f"Error calculating SLA for row: {e}")
        return 'NA'

def create_sla_summary(df):
    """Create SLA summary tables for each category"""
    # Add SLA status to dataframe
    df['SLA_Status'] = df.apply(calculate_sla_status, axis=1)
    
    # Get unique categories from the data
    categories = df['Order Category'].unique()
    sla_summaries = {}
    
    for category in categories:
        category_df = df[df['Order Category'] == category]
        if len(category_df) > 0:
            valid_orders = category_df[category_df['SLA_Status'] != 'NA']
            if len(valid_orders) > 0:
                sla_summary = pd.DataFrame({
                    'Status': ['Within SLA', 'SLA Breached'],
                    'Count': [
                        len(valid_orders[valid_orders['SLA_Status'] == 'Within SLA']),
                        len(valid_orders[valid_orders['SLA_Status'] == 'SLA Breached'])
                    ]
                })
                sla_summary['Percentage'] = (sla_summary['Count'] / len(valid_orders) * 100).round(2)
                sla_summaries[category] = sla_summary
    
    return sla_summaries

def create_sla_charts(df):
    """Create visual representations of SLA performance"""
    df['SLA_Status'] = df.apply(calculate_sla_status, axis=1)
    
    # Overall SLA Performance
    valid_sla = df[df['SLA_Status'] != 'NA']
    fig_overall = px.pie(valid_sla, 
                        names='SLA_Status',
                        title='Overall SLA Performance')
    
    # Category-wise SLA Performance
    category_sla = pd.crosstab(df['Order Category'], df['SLA_Status'])
    fig_category = px.bar(category_sla,
                         title='Category-wise SLA Performance',
                         barmode='group')
    
    return fig_overall, fig_category
def create_hourly_sop_tracker(df):
    hourly_orders = df['Order Hour'].value_counts().sort_index()
    fig = px.bar(x=hourly_orders.index, y=hourly_orders.values,
                 labels={'x': 'Hour of Day', 'y': 'Number of Orders'},
                 title='Hourly Order Distribution')
    # Set specific height for A4 compatibility
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_ticket_status_tracker(df):
    status_counts = df['Order Status'].value_counts()
    fig = px.pie(values=status_counts.values, names=status_counts.index,
                 title='Order Status Distribution')
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_category_summary(df):
    category_summary = df['Order Category'].value_counts()
    fig = px.bar(x=category_summary.index, y=category_summary.values,
                 labels={'x': 'Category', 'y': 'Number of Orders'},
                 title='Orders by Category')
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_city_summary(df):
    city_summary = df['Delivery City'].value_counts()
    fig = px.pie(values=city_summary.values, names=city_summary.index,
                 title='Orders by City')
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_sla_charts(df):
    df['SLA_Status'] = df.apply(calculate_sla_status, axis=1)
    
    valid_sla = df[df['SLA_Status'] != 'NA']
    fig_overall = px.pie(valid_sla, 
                        names='SLA_Status',
                        title='Overall SLA Performance')
    fig_overall.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    
    category_sla = pd.crosstab(df['Order Category'], df['SLA_Status'])
    fig_category = px.bar(category_sla,
                         title='Category-wise SLA Performance',
                         barmode='group')
    fig_category.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    
    return fig_overall, fig_category

def main():
    st.set_page_config(
        page_title="ONDC Order Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Add custom CSS for A4 layout
    st.markdown("""
        <style>
        /* A4 size specifications */
        .main {
            max-width: 21cm !important;  /* A4 width */
            margin: auto !important;
            padding: 1cm !important;
        }
        
        /* Container styling */
        .container {
            background-color: white;
            padding: 0.5cm;
            margin-bottom: 1cm;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        /* Chart container */
        .chart-container {
            width: 100%;
            margin-bottom: 1cm;
        }
        
        /* Metrics styling */
        .metric-container {
            padding: 0.5cm;
            margin-bottom: 0.5cm;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        
        /* Table styling */
        .dataframe {
            font-size: 12px !important;
            width: 100% !important;
            margin-bottom: 0.5cm !important;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #2c3e50;
            margin-bottom: 0.5cm;
        }
        
        /* Ensure proper page breaks */
        .page-break {
            page-break-before: always;
        }
        
        /* Adjust plotly chart size */
        .plotly-graph-div {
            width: 100% !important;
            height: 400px !important;
            margin-bottom: 0.5cm !important;
        }
        
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        @media print {
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                width: 21cm;
                height: 29.7cm;
            }
            .container {
                break-inside: avoid;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("ONDC Order Dashboard")
    
    uploaded_file = st.file_uploader("Choose your CSV file", type="csv")
    if uploaded_file is not None:
        df = load_and_process_data(uploaded_file)
        
        # Key Metrics
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("Key Metrics")
        st.metric("Total Orders", len(df))
        st.metric("Completion Rate", f"{(df['Order Status'] == 'Completed').mean() * 100:.1f}%")
        st.metric("Active Orders", len(df[df['Order Status'].isin(['In-progress', 'Accepted'])]))
        st.metric("Avg Order Value", f"₹{df['Total Order Value'].mean():.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Order Distribution
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("Order Distribution")
        st.plotly_chart(
            create_hourly_sop_tracker(df),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status Distribution
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("Status Distribution")
        st.plotly_chart(
            create_ticket_status_tracker(df),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Category Distribution
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("Category Distribution")
        st.plotly_chart(
            create_category_summary(df),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # City Distribution
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("City Distribution")
        st.plotly_chart(
            create_city_summary(df),
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SLA Analysis
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("SLA Analysis")
        sla_summaries = create_sla_summary(df)
        
        if sla_summaries:
            for category, summary in sla_summaries.items():
                st.write(f"{category} SLA Performance")
                st.dataframe(summary)
                st.markdown("<br>", unsafe_allow_html=True)
        
        fig_overall_sla, fig_category_sla = create_sla_charts(df)
        
        st.plotly_chart(
            fig_overall_sla,
            use_container_width=True,
            config={'displayModeBar': False}
        )
        
        st.plotly_chart(
            fig_category_sla,
            use_container_width=True,
            config={'displayModeBar': False}
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SLA Breach Details
        st.markdown('<div class="container">', unsafe_allow_html=True)
        st.subheader("SLA Breach Details")
        breached_orders = df[df['SLA_Status'] == 'SLA Breached'].copy()
        if len(breached_orders) > 0:
            breached_orders['Delivery Time (Hours)'] = (
                breached_orders['Delivered At Date & Time'] - 
                breached_orders['Order Create Date & Time']
            ).dt.total_seconds() / 3600
            
            st.dataframe(breached_orders[[
                'Network Order Id', 
                'Order Category',
                'Order Create Date & Time',
                'Delivered At Date & Time',
                'Delivery Time (Hours)',
                'Delivery City'
            ]])
        else:
            st.write("No SLA breaches found")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()