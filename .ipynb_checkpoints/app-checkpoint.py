import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Quarterly MRR Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .quarter-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e86de;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_process_data(file_path):
    """Load and process the revenue data for quarterly analysis"""
    
    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    
    # Drop unnecessary columns upfront
    columns_to_drop = [
        "Entity\nUpto Mar 2024", 
        "Entity April 2024", 
        "Entity grouped",
        "S. no."
    ]
    
    # Drop columns if they exist
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
    
    # Debug: Show remaining columns
    st.write("**Remaining columns after cleanup:**", len(df.columns))
    st.write("**All column names:**", df.columns.tolist())
    st.write("**Column data types:**", df.dtypes.head(20))
    
    # Find geography column
    geography_col = 'Country'
    if geography_col not in df.columns:
        st.error(f"Geography column '{geography_col}' not found!")
        return None, None, None
    
    # IMPROVED: Multiple methods to detect datetime columns for 2024
    monthly_cols = []
    
    # Method 1: Check for pandas Timestamp objects
    for col in df.columns:
        if isinstance(col, pd.Timestamp) and col.year == 2024:
            monthly_cols.append(col)
    
    # Method 2: If no Timestamp objects found, try parsing string columns
    if not monthly_cols:
        for col in df.columns:
            if isinstance(col, str):
                # Check if it looks like a date string
                if '2024' in str(col) and ('-' in str(col) or '/' in str(col)):
                    try:
                        parsed_date = pd.to_datetime(col, errors='coerce')
                        if pd.notna(parsed_date) and parsed_date.year == 2024:
                            monthly_cols.append(col)
                    except:
                        continue
    
    # Method 3: If still no columns found, look for datetime-like strings
    if not monthly_cols:
        for col in df.columns:
            col_str = str(col)
            # Look for datetime pattern like "2024-01-01 00:00:00"
            if '2024-' in col_str and '00:00:00' in col_str:
                monthly_cols.append(col)
    
    # Method 4: Last resort - look for any column containing "2024"
    if not monthly_cols:
        for col in df.columns:
            if '2024' in str(col):
                monthly_cols.append(col)
    
    # Sort monthly columns chronologically
    if monthly_cols:
        try:
            # Try to sort by converting to datetime
            monthly_cols = sorted(monthly_cols, key=lambda x: pd.to_datetime(str(x)))
        except:
            # If that fails, sort as strings
            monthly_cols = sorted(monthly_cols)
    
    st.write(f"**Found {len(monthly_cols)} monthly columns**")
    if monthly_cols:
        st.write("**Monthly columns found:**", [str(col) for col in monthly_cols[:6]])
    
    if len(monthly_cols) == 0:
        st.error("No monthly revenue columns found for 2024!")
        st.write("**Debug info - all columns:**")
        for i, col in enumerate(df.columns):
            st.write(f"{i}: {col} (type: {type(col)})")
        return None, None, None
    
    # Prepare clean dataframe
    mrr_df = df[[geography_col] + monthly_cols].copy()
    
    # Convert monthly columns to numeric, handling any data type issues
    for col in monthly_cols:
        mrr_df[col] = pd.to_numeric(mrr_df[col], errors='coerce').fillna(0)
    
    # Remove rows where geography is null or empty
    mrr_df = mrr_df.dropna(subset=[geography_col])
    mrr_df = mrr_df[mrr_df[geography_col].astype(str).str.strip() != '']
    
    # Group by Geography and sum monthly MRR
    mrr_grouped = mrr_df.groupby(geography_col).sum()
    
    # Use first 12 months or available months
    available_months = min(12, len(monthly_cols))
    monthly_cols = monthly_cols[:available_months]
    
    # Create quarterly aggregation
    quarters_mapping = {
        'Q1 2024': monthly_cols[:3],                    # Jan, Feb, Mar
        'Q2 2024': monthly_cols[3:6] if len(monthly_cols) >= 6 else [],    # Apr, May, Jun
        'Q3 2024': monthly_cols[6:9] if len(monthly_cols) >= 9 else [],    # Jul, Aug, Sep
        'Q4 2024': monthly_cols[9:12] if len(monthly_cols) >= 12 else []   # Oct, Nov, Dec
    }
    
    # Calculate quarterly MRR
    quarterly_mrr = pd.DataFrame(index=mrr_grouped.index)
    for quarter, months in quarters_mapping.items():
        if months:  # Only process if months exist
            quarterly_mrr[quarter] = mrr_grouped[months].sum(axis=1)
        else:
            quarterly_mrr[quarter] = 0
    
    # Debug: Show quarterly totals
    quarterly_totals = quarterly_mrr.sum()
    st.write("**Quarterly Totals Debug:**")
    for quarter, total in quarterly_totals.items():
        st.write(f"- {quarter}: ${total:,.2f}")
    
    # Calculate quarterly percentages
    quarterly_percentages = pd.DataFrame(index=quarterly_mrr.index)
    for quarter in quarterly_mrr.columns:
        total = quarterly_mrr[quarter].sum()
        if total > 0:
            quarterly_percentages[quarter] = (quarterly_mrr[quarter] / total) * 100
        else:
            quarterly_percentages[quarter] = 0
    
    # Round to 2 decimal places
    quarterly_mrr = quarterly_mrr.round(2)
    quarterly_percentages = quarterly_percentages.round(2)
    
    return quarterly_mrr, quarterly_percentages, mrr_grouped




def create_percentage_pie_chart(quarterly_percentages, quarter='Q1 2024'):
    """Create a pie chart for MRR percentage distribution for a single quarter"""
    
    # Get data for the selected quarter
    quarter_data = quarterly_percentages[quarter]
    
    # Filter out zero values for cleaner pie chart
    quarter_data = quarter_data[quarter_data > 0]
    
    fig = px.pie(
        values=quarter_data.values,
        names=quarter_data.index,
        title=f"MRR Percentage Distribution - {quarter}",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_size=12
    )
    
    fig.update_layout(
        height=500,
        legend_title="Geography",
        font=dict(size=12),
        showlegend=True
    )
    
    return fig

def create_trend_chart(quarterly_mrr):
    """Create a line chart showing MRR trends by geography"""
    
    fig = go.Figure()
    
    for geography in quarterly_mrr.index:
        fig.add_trace(go.Scatter(
            x=quarterly_mrr.columns,
            y=quarterly_mrr.loc[geography],
            mode='lines+markers',
            name=geography,
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="MRR Trend Analysis by Geography",
        xaxis_title="Quarter",
        yaxis_title="MRR (USD)",
        height=500,
        font=dict(size=12)
    )
    
    return fig

def main():
    # Main header
    st.markdown('<h1 class="main-header">📊 Quarterly MRR Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar for file upload
    st.sidebar.header("📁 Data Input")
    uploaded_file = st.sidebar.file_uploader("Upload Revenue Excel File", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            # Process the data
            quarterly_mrr, quarterly_percentages, monthly_mrr = load_and_process_data(uploaded_file)
            
            # Overview metrics
            st.header("📈 Executive Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_q1 = quarterly_mrr['Q1 2024'].sum()
            total_q2 = quarterly_mrr['Q2 2024'].sum()
            total_q3 = quarterly_mrr['Q3 2024'].sum()
            total_q4 = quarterly_mrr['Q4 2024'].sum()
            
            with col1:
                st.metric("Q1 2024 Total MRR", f"${total_q1:,.2f}", 
                         delta=None, delta_color="normal")
            
            with col2:
                delta_q2 = ((total_q2 - total_q1) / total_q1 * 100) if total_q1 != 0 else 0
                st.metric("Q2 2024 Total MRR", f"${total_q2:,.2f}", 
                         delta=f"{delta_q2:+.2f}%", delta_color="normal")
            
            with col3:
                delta_q3 = ((total_q3 - total_q2) / total_q2 * 100) if total_q2 != 0 else 0
                st.metric("Q3 2024 Total MRR", f"${total_q3:,.2f}", 
                         delta=f"{delta_q3:+.2f}%", delta_color="normal")
            
            with col4:
                delta_q4 = ((total_q4 - total_q3) / total_q3 * 100) if total_q3 != 0 else 0
                st.metric("Q4 2024 Total MRR", f"${total_q4:,.2f}", 
                         delta=f"{delta_q4:+.2f}%", delta_color="normal")
            
            # Detailed Analysis
            st.header("🗺️ Geographic Breakdown")
            
            # Create two tabs for different views
            tab1, tab2 = st.tabs([ "📈 Percentage Distribution", "📉 Trend Analysis"])
            
            
            with tab1:
                st.subheader("Quarterly Percentage Distribution by Geography")
                    
                    # Quarter selection dropdown
                quarter_to_view = st.selectbox(
                    "Select Quarter to View",
                    options=quarterly_percentages.columns.tolist(),
                    index=0
                )
                    
                # Display the pie chart for selected quarter
                pie_chart = create_percentage_pie_chart(quarterly_percentages, quarter_to_view)
                st.plotly_chart(pie_chart, use_container_width=True)
                    
                # Display the percentage table
                st.subheader("📋 Detailed Percentage Table")
                st.dataframe(
                    quarterly_percentages.style.format("{:.2f}%"),
                    use_container_width=True
                )
            
            with tab2:
                st.subheader("MRR Trend Analysis")
                
                # Display the trend chart
                trend_chart = create_trend_chart(quarterly_mrr)
                st.plotly_chart(trend_chart, use_container_width=True)
                
                # Growth analysis
                st.subheader("📊 Quarter-over-Quarter Growth Analysis")
                growth_df = quarterly_mrr.pct_change(axis=1) * 100
                growth_df = growth_df.iloc[:, 1:]  # Remove Q1 as it has no previous quarter
                growth_df = growth_df.round(2)
                
                st.dataframe(
                    growth_df.style.format("{:+.2f}%"),
                    use_container_width=True
                )
            
            # Geographic insights
            st.header("🔍 Key Insights")
            
            # Top geography by quarter
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Top Geography by Quarter")
                top_geo_by_quarter = quarterly_mrr.idxmax()
                for quarter, geo in top_geo_by_quarter.items():
                    value = quarterly_mrr.loc[geo, quarter]
                    percentage = quarterly_percentages.loc[geo, quarter]
                    st.write(f"**{quarter}**: {geo} - ${value:,.2f} ({percentage:.2f}%)")
            
            with col2:
                st.subheader("📈 Overall Performance")
                total_by_geo = quarterly_mrr.sum(axis=1).sort_values(ascending=False)
                st.write("**Total MRR by Geography (2024):**")
                for geo, value in total_by_geo.items():
                    percentage = (value / total_by_geo.sum()) * 100
                    st.write(f"• {geo}: ${value:,.2f} ({percentage:.2f}%)")
                    
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            st.info("Please ensure the file has the correct format with Geography and monthly columns.")
    
    else:
        st.info("👆 Please upload your revenue Excel file using the sidebar to begin analysis.")
        
        # Show sample data format
        st.subheader("📝 Expected Data Format")
        st.write("Your Excel file should contain:")
        st.write("• A 'Country' column ")
        st.write("• Monthly revenue columns for 2024 (datetime format)")
        st.write("• Each row representing a different entity/customer")

if __name__ == "__main__":
    main()
