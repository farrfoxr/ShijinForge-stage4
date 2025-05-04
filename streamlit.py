import streamlit as st
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt
from PIL import Image
import json
import time

# Ensure the .streamlit directory exists
os.makedirs(".streamlit", exist_ok=True)

# Set page configuration
st.set_page_config(
    page_title="Smart Trash Classification Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define color scheme - updated colors for Plastic and Other
COLORS = {
    "primary": "#4e7056",
    "secondary": "#759f7c",
    "light_green": "#e8f4ea",
    "dark_green": "#3a5641",
    "light_gray": "#f7f7f7",
    "medium_gray": "#e0e0e0",
    "dark_gray": "#555555",
    "white": "#ffffff",
    "organic": "#4e7056",  # Keep green for organic
    "plastic": "#3498db",  # Changed to blue for plastic
    "other": "#a0a0a0"     # Changed to light grey for other
}

# Custom CSS for Notion-like styling with more color
st.markdown("""
<style>
    /* Force light mode */
    html {
        background-color: white !important;
        color: #333 !important;
    }
    
    /* Override any dark mode styles */
    .stApp, .main, .element-container, .block-container {
        background-color: white !important;
        color: #333 !important;
    }
    
    /* Base styles */
    .main {
        background-color: white !important;
        color: #333 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Colorful header */
    .dashboard-header {
        background: linear-gradient(90deg, """ + COLORS["dark_green"] + """ 0%, """ + COLORS["secondary"] + """ 100%);
        margin: -1.5rem -1.5rem 1.5rem -1.5rem;
        padding: 2rem 1.5rem;
        border-radius: 0 0 10px 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        position: relative;
        overflow: hidden;
    }
    
    .dashboard-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, """ + COLORS["dark_green"] + """ 0%, """ + COLORS["light_green"] + """ 50%, """ + COLORS["dark_green"] + """ 100%);
    }
    
    .dashboard-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .dashboard-header p {
        color: rgba(255,255,255,0.9) !important;
        margin-top: 0.5rem;
        font-size: 1rem;
        max-width: 800px;
    }
    
    .dashboard-header .last-updated {
        position: absolute;
        top: 1rem;
        right: 1.5rem;
        color: rgba(255,255,255,0.8) !important;
        font-size: 0.8rem;
        background-color: rgba(0,0,0,0.1);
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
    }
    
    /* Colorful footer */
    .dashboard-footer {
        background-color: """ + COLORS["light_green"] + """;
        margin: 3rem -1.5rem -1.5rem -1.5rem;
        padding: 1.5rem;
        border-top: 1px solid """ + COLORS["secondary"] + """;
        text-align: center;
        position: relative;
    }
    
    .dashboard-footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, """ + COLORS["dark_green"] + """ 0%, """ + COLORS["secondary"] + """ 50%, """ + COLORS["dark_green"] + """ 100%);
    }
    
    .dashboard-footer p {
        color: """ + COLORS["dark_green"] + """ !important;
        font-size: 0.9rem;
        margin: 0;
    }
    
    .eco-icon {
        color: """ + COLORS["primary"] + """ !important;
        font-size: 1.2rem;
        margin: 0 0.3rem;
        vertical-align: middle;
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    h1 {
        font-size: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
        color: """ + COLORS["dark_green"] + """ !important;
        border-bottom: 2px solid """ + COLORS["light_green"] + """;
        padding-bottom: 0.5rem;
        display: inline-block;
    }
    
    h3 {
        font-size: 1.2rem !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.5rem !important;
        color: """ + COLORS["dark_green"] + """ !important;
    }
    
    /* Card styling with subtle color */
    .card {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 1.5rem;
        background-color: white !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border-top: 3px solid """ + COLORS["secondary"] + """;
    }
    
    /* Metric card styling */
    .metric-card {
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: """ + COLORS["light_green"] + """ !important;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 600;
        margin: 0.5rem 0;
        color: #333 !important;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #555 !important;
        margin: 0;
    }
    
    /* Chart container with subtle color */
    .chart-container {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        background-color: white !important;
        margin-bottom: 1rem;
        border-left: 4px solid """ + COLORS["secondary"] + """;
    }
    
    /* Prediction badge */
    .prediction-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
        color: white !important;
        margin-top: 0.5rem;
    }
    
    /* Divider with gradient */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, """ + COLORS["dark_green"] + """ 0%, """ + COLORS["secondary"] + """ 50%, """ + COLORS["light_green"] + """ 100%);
        margin: 1.5rem 0;
        border-radius: 2px;
    }
    
    /* Custom button */
    .custom-button {
        background: linear-gradient(135deg, """ + COLORS["primary"] + """ 0%, """ + COLORS["dark_green"] + """ 100%);
        color: white !important;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        display: inline-block;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .custom-button:hover {
        background: linear-gradient(135deg, """ + COLORS["dark_green"] + """ 0%, """ + COLORS["primary"] + """ 100%);
        color: white !important;
        text-decoration: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    /* Image container */
    .image-container {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
        background-color: white !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Timestamp */
    .timestamp {
        font-size: 0.8rem;
        color: #777 !important;
        margin-top: 0.5rem;
    }
    
    /* Fix tab spacing - make tabs wider with more padding */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: """ + COLORS["light_gray"] + """ !important;
        border-radius: 8px;
        padding: 6px !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #555 !important;
        font-weight: 500;
        padding: 8px 16px !important;
        margin: 0 4px !important;
        transition: all 0.2s;
    }

    .stTabs [aria-selected="true"] {
        background-color: """ + COLORS["light_green"] + """ !important;
        color: """ + COLORS["primary"] + """ !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: rgba(0,0,0,0.05) !important;
    }
    
    /* Make sure all text is visible in light mode */
    p, li, span, div {
        color: #333 !important;
    }
    
    /* Override any Streamlit elements that might use system theme */
    .stAlert, .stInfo, .stWarning, .stError, .stSuccess {
        background-color: """ + COLORS["light_gray"] + """ !important;
        color: #333 !important;
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    .stInfo {
        border-left-color: """ + COLORS["secondary"] + """ !important;
    }
    
    /* Ensure sidebar is also in light mode */
    .css-1d391kg, .css-12oz5g7 {
        background-color: """ + COLORS["light_green"] + """ !important;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main {
            padding: 1rem !important;
        }
        
        .dashboard-header {
            margin: -1rem -1rem 1rem -1rem;
            padding: 1.5rem 1rem;
        }
        
        .dashboard-header h1 {
            font-size: 1.5rem !important;
        }
        
        .dashboard-header .last-updated {
            position: static;
            display: block;
            margin-top: 0.5rem;
            text-align: left;
        }
        
        .dashboard-footer {
            margin: 2rem -1rem -1rem -1rem;
            padding: 1rem;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 1rem !important;
        }
        
        .card {
            padding: 1rem !important;
        }
        
        .metric-card {
            padding: 0.75rem !important;
        }
        
        .metric-value {
            font-size: 1.5rem !important;
        }
        
        /* Make sure columns stack properly on mobile */
        .row-widget.stHorizontal {
            flex-wrap: wrap !important;
        }
        
        /* Ensure charts are responsive */
        .chart-container {
            padding: 0.5rem !important;
            overflow-x: auto !important;
        }
    }
    
    /* Responsive grid for metrics */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
    }
    
    @media (max-width: 1200px) {
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 640px) {
        .metrics-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# Path to the uploads folder (same as in Flask app)
UPLOAD_FOLDER = 'static/uploads'

# Path to store counter data
DATA_FILE = 'trash_data.json'

# Function to create a custom card
def custom_card(title, content, color=COLORS["white"]):
    st.markdown(f"""
    <div class="card" style="background-color: {color};">
        <h3>{title}</h3>
        {content}
    </div>
    """, unsafe_allow_html=True)

# Function to create a metric card
def metric_card(label, value, color):
    st.markdown(f"""
    <div class="metric-card" style="background-color: {COLORS['light_green']}; border-left: 4px solid {color};">
        <p class="metric-label">{label}</p>
        <p class="metric-value" style="color: {color};">{value}</p>
    </div>
    """, unsafe_allow_html=True)

# Function to load the latest image
def get_latest_image():
    if not os.path.exists(UPLOAD_FOLDER):
        return None, "No images directory found", "Unknown"
    
    files = os.listdir(UPLOAD_FOLDER)
    image_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        return None, "No images found", "Unknown"
    
    # Sort by modification time (newest first)
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)), reverse=True)
    latest_image = image_files[0]
    
    # Extract prediction from filename if available
    prediction = "Unknown"
    if "_" in latest_image:
        parts = latest_image.split("_")
        if len(parts) > 1:
            prediction = parts[1].split(".")[0]
    
    image_path = os.path.join(UPLOAD_FOLDER, latest_image)
    timestamp = datetime.fromtimestamp(os.path.getmtime(image_path)).strftime('%Y-%m-%d %H:%M:%S')
    
    return image_path, timestamp, prediction

# Function to load counter data
def load_counter_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"Organic": 0, "Other": 0, "Plastic": 0, "history": [], "hourly_data": {}}

# Function to prepare hourly data for visualization
def prepare_hourly_data(hourly_data):
    if not hourly_data:
        return pd.DataFrame()
    
    # Convert to DataFrame
    rows = []
    for hour, counts in hourly_data.items():
        row = {
            'hour': hour,
            'timestamp': pd.to_datetime(hour),
            'total': counts['total'],
            'Organic': counts.get('Organic', 0),
            'Other': counts.get('Other', 0),
            'Plastic': counts.get('Plastic', 0)
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Sort by timestamp
    if not df.empty:
        df = df.sort_values('timestamp')
    
    return df

# Function to create a time-based chart for hourly submissions
def create_hourly_chart(hourly_df):
    if hourly_df.empty or len(hourly_df) < 2:
        return None
    
    # Create line chart for total submissions - with light theme colors
    total_chart = alt.Chart(hourly_df).mark_line(
        point=alt.OverlayMarkDef(color=COLORS["primary"])
    ).encode(
        x=alt.X('timestamp:T', title='Time'),
        y=alt.Y('total:Q', title='Total Submissions'),
        tooltip=['timestamp:T', 'total:Q']
    ).properties(
        title='Hourly Trash Submissions',
        height=300
    ).configure_axis(
        labelColor='#333',
        titleColor='#333',
        labelFontSize=12,
        titleFontSize=14,
        grid=True,
        gridColor='#eee'
    ).configure_view(
        strokeWidth=0,
        fill='white'
    ).configure_title(
        fontSize=16,
        font='Inter, sans-serif',
        anchor='start',
        color='#333'
    ).configure_legend(
        titleColor='#333',
        labelColor='#333',
        padding=10,
        cornerRadius=5,
        orient='top'
    )
    
    return total_chart

# Function to create a time-based chart for hourly submissions by category
def create_category_hourly_chart(hourly_df):
    if hourly_df.empty or len(hourly_df) < 2:
        return None
    
    # Melt the DataFrame to get it in the right format for Altair
    melted_df = pd.melt(
        hourly_df,
        id_vars=['timestamp'],
        value_vars=['Organic', 'Other', 'Plastic'],
        var_name='Category',
        value_name='Count'
    )
    
    # Create line chart for category submissions - with updated colors
    category_chart = alt.Chart(melted_df).mark_line().encode(
        x=alt.X('timestamp:T', title='Time'),
        y=alt.Y('Count:Q', title='Submissions'),
        color=alt.Color('Category:N', scale=alt.Scale(
            domain=['Organic', 'Other', 'Plastic'],
            range=[COLORS["organic"], COLORS["other"], COLORS["plastic"]]
        )),
        tooltip=['timestamp:T', 'Category:N', 'Count:Q']
    ).properties(
        title='Hourly Trash Submissions by Category',
        height=300
    ).configure_axis(
        labelColor='#333',
        titleColor='#333',
        labelFontSize=12,
        titleFontSize=14,
        grid=True,
        gridColor='#eee'
    ).configure_view(
        strokeWidth=0,
        fill='white'
    ).configure_title(
        fontSize=16,
        font='Inter, sans-serif',
        anchor='start',
        color='#333'
    ).configure_legend(
        titleColor='#333',
        labelColor='#333',
        padding=10,
        cornerRadius=5,
        orient='top'
    )
    
    return category_chart

# Function to create a bar chart of trash counts
def create_bar_chart(counter_data):
    categories = ['Organic', 'Other', 'Plastic']
    counts = [counter_data.get(cat, 0) for cat in categories]
    
    chart_data = pd.DataFrame({
        'Category': categories,
        'Count': counts
    })
    
    # Create bar chart with updated colors
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Category:N', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Count:Q', title='Number of Items'),
        color=alt.Color('Category:N', scale=alt.Scale(
            domain=['Organic', 'Other', 'Plastic'],
            range=[COLORS["organic"], COLORS["other"], COLORS["plastic"]]
        )),
        tooltip=['Category:N', 'Count:Q']
    ).properties(
        title='Trash Classification Distribution',
        height=300
    ).configure_axis(
        labelColor='#333',
        titleColor='#333',
        labelFontSize=12,
        titleFontSize=14,
        grid=False,
        gridColor='#eee'
    ).configure_view(
        strokeWidth=0,
        fill='white'
    ).configure_title(
        fontSize=16,
        font='Inter, sans-serif',
        anchor='start',
        color='#333'
    ).configure_legend(
        titleColor='#333',
        labelColor='#333',
        padding=10,
        cornerRadius=5,
        orient='top'
    )
    
    return chart

# Main dashboard
def main():
    # Load data
    counter_data = load_counter_data()
    image_path, timestamp, prediction = get_latest_image()
    
    # Prepare hourly data
    hourly_data = counter_data.get('hourly_data', {})
    hourly_df = prepare_hourly_data(hourly_data)
    
    # Colorful Header
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="last-updated">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <h1>Smart Trash Classification Dashboard</h1>
        <p>Real-time monitoring and analytics for eco-friendly waste management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs with more spacing and gradient styling
    tab1, tab2, tab3 = st.tabs(["Overview", "Time Analysis", "Latest Detection"])
    
    # Tab 1: Overview
    with tab1:
        # Summary metrics - using custom responsive grid
        st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
        
        total_items = counter_data.get('Organic', 0) + counter_data.get('Other', 0) + counter_data.get('Plastic', 0)
        metric_card("Total Items", total_items, COLORS["dark_green"])
        metric_card("Organic", counter_data.get('Organic', 0), COLORS["organic"])
        metric_card("Other", counter_data.get('Other', 0), COLORS["other"])
        metric_card("Plastic", counter_data.get('Plastic', 0), COLORS["plastic"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Distribution chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        bar_chart = create_bar_chart(counter_data)
        st.altair_chart(bar_chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Latest detection summary
        st.markdown(f"""
        <h2 style="color: #333 !important;">Latest Detection</h2>
        <div class="card">
            <div style="display: flex; flex-wrap: wrap; align-items: center;">
                <div style="flex-grow: 1; margin-bottom: 1rem;">
                    <h3 style="color: #333 !important;">Classification Result</h3>
                    <div class="prediction-badge" style="background-color: {
                        COLORS["organic"] if prediction == "Organic" else 
                        COLORS["plastic"] if prediction == "Plastic" else 
                        COLORS["other"]
                    };">
                        {prediction}
                    </div>
                    <p class="timestamp">Detected at: {timestamp}</p>
                </div>
                <div>
                    <a href="/" target="_self" class="custom-button">
                        View All Detections
                    </a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tab 2: Time Analysis
    with tab2:
        st.markdown("""
        <h2 style="color: #333 !important;">Trash Submission Patterns</h2>
        <p style="color: #555 !important; margin-bottom: 1rem;">
            Analyze when trash is most frequently detected to optimize waste management strategies
        </p>
        """, unsafe_allow_html=True)
        
        # Time-based charts
        if not hourly_df.empty and len(hourly_df) > 1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            hourly_chart = create_hourly_chart(hourly_df)
            st.altair_chart(hourly_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            category_hourly_chart = create_category_hourly_chart(hourly_df)
            st.altair_chart(category_hourly_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Summary insights
            if len(hourly_df) >= 24:  # If we have at least a day's worth of data
                # Find peak hour
                peak_hour = hourly_df.loc[hourly_df['total'].idxmax()]
                peak_time = peak_hour['timestamp'].strftime('%H:00')
                
                # Calculate average submissions per hour
                avg_submissions = hourly_df['total'].mean()
                
                st.markdown(f"""
                <div class="card" style="background-color: {COLORS['light_green']};">
                    <h3 style="color: #333 !important;">Key Insights</h3>
                    <ul>
                        <li><strong>Peak Activity:</strong> Most trash is detected around {peak_time} with {int(peak_hour['total'])} submissions</li>
                        <li><strong>Average Hourly Rate:</strong> {avg_submissions:.1f} items per hour</li>
                        <li><strong>Most Common Type:</strong> {max(counter_data.items(), key=lambda x: x[1] if x[0] in ['Organic', 'Other', 'Plastic'] else 0)[0]}</li>
                    </ul>
                    <p style="color: #333 !important;">Use these insights to optimize waste collection schedules and resource allocation.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Not enough time-based data available yet. Continue collecting data to see time patterns.")
    
    # Tab 3: Latest Detection - made responsive
    with tab3:
        if image_path:
            st.markdown("""
            <h2 style="color: #333 !important;">Latest Captured Image</h2>
            <p style="color: #555 !important; margin-bottom: 1rem;">
                Most recent trash item detected by the system
            </p>
            """, unsafe_allow_html=True)
            
            # Use columns but with responsive design in mind
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                image = Image.open(image_path)
                st.image(image, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(f'<p class="timestamp">Captured at: {timestamp}</p>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="card">
                    <h3 style="color: #333 !important;">Classification Details</h3>
                    <div class="prediction-badge" style="background-color: {
                        COLORS["organic"] if prediction == "Organic" else 
                        COLORS["plastic"] if prediction == "Plastic" else 
                        COLORS["other"]
                    };">
                        {prediction}
                    </div>
                    <div class="divider"></div>
                    <h4 style="color: #333 !important;">What happens next?</h4>
                    <p style="color: #333 !important;">This item will be processed according to its classification:</p>
                    <ul>
                        <li><strong>Organic:</strong> Composted into nutrient-rich soil</li>
                        <li><strong>Plastic:</strong> Recycled into new products</li>
                        <li><strong>Other:</strong> Properly sorted for appropriate disposal</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No images available. Waiting for the first detection.")
    
    # Colorful Footer
    st.markdown(f"""
    <div class="dashboard-footer">
        <p>
            <span class="eco-icon">♻️</span> 
            Smart Trash Classification System © {datetime.now().year} | 
            Eco-friendly waste management solution
            <span class="eco-icon">🌱</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()